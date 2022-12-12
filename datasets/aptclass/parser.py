import re
from json import load
from typing import List
from pandas import read_csv
from ast import literal_eval
from collections import Counter
from sklearn.model_selection import StratifiedKFold
from sqlmodel import SQLModel, Session, create_engine

from models.config import Config
from aptclass_models import Sample, Group, Alias, Report, Country, FileType


__author__ = "Marius Benthin"


# load secrets from environment
config = Config()

# create database connection and tables
sql_engine = create_engine(config.database_url)
SQLModel.metadata.create_all(sql_engine)


group_aliases = {}
if config.alias_aware:
    # dictionary with aliases as key and group name as value
    with open(config.alias_json, 'r') as f:
        group_aliases = load(f)

# read dataset csv file
with open(config.aptclass_csv, mode='r', encoding='utf-8') as f:

    # apply filters as proposed by the authors
    df = read_csv(f, sep='|')
    df = df[~df['apt_country'].str.contains('unknown')]
    df = df[~df['apt_country'].str.contains(',')]
    df = df[~df['apt_country'].str.contains('no_linked_nation')]
    df = df[~df['apt_name'].str.contains('unknown')]

    if not config.alias_aware:
        # apply this filter rule only if alias mapping is ignored
        df = df[~df['apt_name'].str.contains(',')]

    # apply additional filter rules on countries
    df = df[~df['apt_country'].str.contains('Iran Israel')]
    df = df[~df['apt_country'].str.contains('North Korea South Korea')]
    df = df[~df['apt_country'].str.contains('NATO')]
    df = df[~df['apt_country'].str.contains('China Iran')]
    df = df[~df['apt_country'].str.contains('Russia Ukraine')]

    # apply additional filter for filetypes
    df = df[df['vt_file_type'].isin(['Win16 EXE', 'Win32 EXE', 'Win32 DLL', 'Windows Installer', 'DOS EXE'])]

    # local cache with committed database objects
    countries, groups, file_types, reports = {}, {}, {}, {}

    # store inputs and outputs for splitting into folds
    X, y = [], []

    # parse rows and create SQL models
    with Session(sql_engine) as session:
        for df_tuple in df.itertuples():

            if not config.alias_aware:
                apt_name = df_tuple.apt_name
            else:
                # parse group and check for common aliases
                _groups = []
                aliases = df_tuple.apt_name.split(', ')
                for alias in aliases:
                    if alias in group_aliases.keys():
                        _groups.append(group_aliases[alias])
                    else:
                        _groups.append(alias)

                # skip if aliases belong to different groups
                if len(set(_groups)) != 1:
                    continue
                else:
                    apt_name = _groups[0]

            # parse and validate country
            country: Country = Country.from_orm(df_tuple)
            if country.name not in countries.keys():
                session.add(country)
                session.commit()
                session.refresh(country)
                countries[country.name] = country
            else:
                country = countries[country.name]

            # validate group
            group: Group = Group(apt_name=apt_name)
            if group.name not in groups.keys():
                group.country = country
                session.add(group)
                session.commit()
                session.refresh(group)
                groups[group.name] = group
            else:
                group = groups[group.name]

            # parse and validate file type
            file_type: FileType = FileType.from_orm(df_tuple)
            if file_type.name not in file_types.keys():
                session.add(file_type)
                session.commit()
                session.refresh(file_type)
                file_types[file_type.name] = file_type
            else:
                file_type = file_types[file_type.name]

            # parse and validate reports
            report_collection: List[Report] = []
            paths: List[str] = literal_eval(df_tuple.path)
            report_hashes: List[str] = df_tuple.report_hash.split(', ')
            assert len(report_hashes) == len(paths)
            for i in range(len(paths)):
                report: Report = Report(path=paths[i], sha256=report_hashes[i])
                if report.sha256 not in reports.keys():
                    session.add(report)
                    session.commit()
                    session.refresh(report)
                    reports[report.sha256] = report
                else:
                    report = reports[report.sha256]
                report_collection.append(report)

            # parse and validate sample and connect with other objects
            sample: Sample = Sample.from_orm(df_tuple)
            sample.group = group
            sample.reports = report_collection
            sample.file_type = file_type
            sample.children = []
            session.add(sample)
            session.commit()
            session.refresh(sample)

            X.append(sample)
            y.append(sample.group_id)

        # insert aliases into database
        for alias_name, group_name in group_aliases.items():
            alias = Alias(name=alias_name)
            group_name = re.sub(r'[^\dA-Z]+', '_', group_name.upper())
            alias.group = groups[group_name]
            session.add(alias)
        session.commit()

# split dataset into folds
skf = StratifiedKFold(n_splits=config.n_splits, shuffle=True, random_state=config.random_state)

# ensure that number of samples per group is not less than k fold splits
for group_id, n in Counter(y).items():
    if n < config.n_splits:
        for i, _y in enumerate(y):
            if _y == group_id:
                del X[i]
                del y[i]

fold_id: int = 1
for train, test in skf.split(X, y):
    # set fold ID of each sample
    for sample_id in test:
        sample = X[sample_id]
        sample.fold_id = fold_id
        session.add(sample)
    fold_id += 1

session.commit()
