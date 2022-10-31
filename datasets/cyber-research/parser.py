from pandas import read_csv
from sqlmodel import SQLModel, Session, create_engine
from models import Config, Sample, Actor, Report, Country

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

    # local cache with committed database objects
    countries, actors, file_types, reports = {}, {}, {}, {}

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
            session.add(sample)
            session.commit()
