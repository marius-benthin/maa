from pandas import read_csv
from collections import Counter
from sklearn.model_selection import StratifiedKFold
from sqlmodel import SQLModel, Session, create_engine
from models import Config, Sample, Actor, Report, Country, FileType

__author__ = "Marius Benthin"


# load secrets from environment
config = Config()

# create database connection and tables
sql_engine = create_engine(config.database_url)
SQLModel.metadata.create_all(sql_engine)

# read dataset csv file
with open(config.dataset_file, mode='r', encoding='utf-8') as f:

    # apply filters as proposed by the authors
    df = read_csv(f, sep=',')
    df = df[~df['Status'].str.contains('X')]

    # apply additional filter for filetypes
    df = df[df['Filetype'].isin(['Win16 EXE', 'Win32 EXE', 'Win32 DLL', 'Windows Installer', 'DOS EXE'])]

    # local cache with committed database objects
    countries, actors, file_types, reports = {}, {}, {}, {}

    # store inputs and outputs for splitting into folds
    X, y = [], []

    # parse rows and create SQL models
    with Session(sql_engine) as session:
        for df_tuple in df.itertuples():

            # parse and validate country
            country: Country = Country.from_orm(df_tuple)
            if country.name not in countries.keys():
                session.add(country)
                session.commit()
                session.refresh(country)
                countries[country.name] = country
            else:
                country = countries[country.name]

            # parse and validate actor
            actor: Actor = Actor.from_orm(df_tuple)
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

            # parse and validate report
            report: Report = Report.from_orm(df_tuple)
            if report.url not in reports.keys():
                session.add(report)
                session.commit()
                session.refresh(report)
                reports[report.url] = report
            else:
                report = reports[report.url]

            # parse and validate sample and connect with other objects
            sample: Sample = Sample.from_orm(df_tuple)
            sample.actor = actor
            sample.report = report
            sample.file_type = file_type
            sample.children = []
            session.add(sample)
            session.commit()
            session.refresh(sample)

            X.append(sample)
            y.append(sample.actor_id)

# split dataset into folds
skf = StratifiedKFold(n_splits=config.n_splits, shuffle=True, random_state=config.random_state)

# ensure that number of samples per group is not less than k fold splits
for actor_id, n in Counter(y).items():
    if n < config.n_splits:
        for i, _y in enumerate(y):
            if _y == actor_id:
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
