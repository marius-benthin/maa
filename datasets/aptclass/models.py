import re
from typing import List, Optional
from sqlalchemy import Column, VARCHAR
from pydantic import validator, BaseSettings
from sqlmodel import SQLModel, Field, Relationship


__author__ = "Marius Benthin"


class Config(BaseSettings):
    database_url: str
    dataset_file: str = "2021-jan-aptclass_dataset.csv"
    alias_aware: bool = False
    n_splits: int = 8
    random_state: int = 42

    class Config:
        env_file = ".env"


class Country(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(alias='apt_country')
    actors: List["Actor"] = Relationship(back_populates="country")

    @validator('name', pre=True, always=True)
    def normalize_country_name(cls, v):
        return re.sub(r'[^\dA-Z]+', '_', v.upper())


class Actor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(alias='apt_name')
    samples: List["Sample"] = Relationship(back_populates="actor")
    country_id: Optional[int] = Field(default=None, foreign_key="country.id")
    country: Optional[Country] = Relationship(back_populates="actors")

    @validator('name', pre=True, always=True)
    def normalize_actor_name(cls, v):
        return re.sub(r'[^\dA-Z]+', '_', v.upper())


class FileType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(alias='vt_file_type')
    samples: List["Sample"] = Relationship(back_populates="file_type")

    @validator('name', pre=True, always=True)
    def normalize_file_type(cls, v):
        return re.sub(r'[^\dA-Z]+', '_', v.upper())


class ReportSampleLink(SQLModel, table=True):
    sample_id: Optional[int] = Field(default=None, foreign_key="sample.id", primary_key=True)
    report_id: Optional[int] = Field(default=None, foreign_key="report.id", primary_key=True)


class Report(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    path: str
    sha256: str = Field(sa_column=Column("sha256", VARCHAR(64), unique=True))
    samples: List["Sample"] = Relationship(back_populates="reports", link_model=ReportSampleLink)

    @validator('sha256', pre=True, always=True)
    def normalize_report_hash(cls, v):
        if re.match(r'^[a-f\d]{64}$', v, re.I) is None:
            raise ValueError('Invalid SHA-256')
        return v.upper()


class SampleChildrenLink(SQLModel, table=True):
    sample_id: Optional[int] = Field(default=None, foreign_key="sample.id", primary_key=True)
    child_id: Optional[int] = Field(default=None, foreign_key="child.id", primary_key=True)


class Child(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sha256: str = Field(sa_column=Column("sha256", VARCHAR(64), unique=True))
    samples: List["Sample"] = Relationship(back_populates="children", link_model=SampleChildrenLink)


class Sample(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    md5: str = Field(alias='vt_md5')
    sha1: str = Field(alias='vt_sha1')
    sha256: str = Field(alias='checked_sha256', sa_column=Column("sha256", VARCHAR(64), unique=True))
    actor_id: Optional[int] = Field(default=None, foreign_key="actor.id")
    actor: Optional[Actor] = Relationship(back_populates="samples")
    file_type_id: Optional[int] = Field(default=None, foreign_key="filetype.id")
    file_type: Optional[FileType] = Relationship(back_populates="samples")
    reports: List[Report] = Relationship(back_populates="samples", link_model=ReportSampleLink)
    fold_id: Optional[int] = Field(default=None, nullable=True)
    children: List[Child] = Relationship(back_populates="samples", link_model=SampleChildrenLink)

    @validator('sha256', pre=True, always=True)
    def normalize_sha256(cls, v):
        if re.match(r'^[a-f\d]{64}$', v, re.I) is None:
            raise ValueError('Invalid SHA-256')
        return v.upper()

    @validator('sha1', pre=True, always=True)
    def normalize_sha1(cls, v):
        if re.match(r'^[a-f\d]{40}$', v, re.I) is None:
            raise ValueError('Invalid SHA-1')
        return v.upper()

    @validator('md5', pre=True, always=True)
    def normalize_md5(cls, v):
        if re.match(r'^[a-f\d]{32}$', v, re.I) is None:
            raise ValueError('Invalid MD5')
        return v.upper()
