from json import load
from typing import List
from pandas import read_csv
from ast import literal_eval
from sqlmodel import SQLModel, Session, create_engine
from models import Config, Sample, Actor, Report, Country, FileType


__author__ = "Marius Benthin"


# load secrets from environment
config = Config()

# create database connection and tables
sql_engine = create_engine(config.database_url)
SQLModel.metadata.create_all(sql_engine)

actor_aliases = {}
if config.alias_aware:
    # dictionary with aliases as key and group name as value
    with open('aliases.json', 'r') as f:
        actor_aliases = load(f)

# read dataset csv file
with open(config.dataset_file, mode='r', encoding='utf-8') as f:

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

    # local cache with committed database objects
    countries, actors, file_types, reports = {}, {}, {}, {}

    # parse rows and create SQL models
    with Session(sql_engine) as session:
        for df_tuple in df.itertuples():

            if not config.alias_aware:
                apt_name = df_tuple.apt_name
            else:
                # parse actor and check for common aliases
                _actors = []
                aliases = df_tuple.apt_name.split(', ')
                for alias in aliases:
                    if alias in actor_aliases.keys():
                        _actors.append(actor_aliases[alias])
                    else:
                        _actors.append(alias)

                # skip if aliases belong to different groups
                if len(set(_actors)) != 1:
                    continue
                else:
                    apt_name = _actors[0]

            # parse and validate country
            country: Country = Country.from_orm(df_tuple)
            if country.name not in countries.keys():
                session.add(country)
                session.commit()
                session.refresh(country)
                countries[country.name] = country
            else:
                country = countries[country.name]

            # validate actor
            actor: Actor = Actor(apt_name=apt_name)
            if actor.name not in actors.keys():
                actor.country = country
                session.add(actor)
                session.commit()
                session.refresh(actor)
                actors[actor.name] = actor
            else:
                actor = actors[actor.name]

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
            sample.actor = actor
            sample.reports = report_collection
            sample.file_type = file_type
            session.add(sample)
            session.commit()
