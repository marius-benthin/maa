import re
from pydantic import validator
from typing import List, Optional
from sqlalchemy import Column, VARCHAR
from sqlmodel import SQLModel, Field, Relationship


__author__ = "Marius Benthin"


class Country(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(alias='Country')
    actors: List["Actor"] = Relationship(back_populates="country")

    @validator('name', pre=True, always=True)
    def normalize_country_name(cls, v):
        return re.sub(r'[^\dA-Z]+', '_', v.upper())


class Actor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(alias='_3')  # actually 'APT-group' but panda renames it
    samples: List["Sample"] = Relationship(back_populates="actor")
    country_id: Optional[int] = Field(default=None, foreign_key="country.id")
    country: Optional[Country] = Relationship(back_populates="actors")

    @validator('name', pre=True, always=True)
    def normalize_actor_name(cls, v):
        return re.sub(r'[^\dA-Z]+', '_', v.upper()).replace('APT_', 'APT')


class FileType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(alias='Filetype')
    samples: List["Sample"] = Relationship(back_populates="file_type")

    @validator('name', pre=True, always=True)
    def normalize_file_type(cls, v):
        return re.sub(r'[^\dA-Z]+', '_', v.upper())


class Report(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(alias='Source')
    samples: List["Sample"] = Relationship(back_populates="report")


class SampleChildrenLink(SQLModel, table=True):
    sample_id: Optional[int] = Field(default=None, foreign_key="sample.id", primary_key=True)
    child_id: Optional[int] = Field(default=None, foreign_key="child.id", primary_key=True)


class Child(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sha256: str = Field(sa_column=Column("sha256", VARCHAR(64), unique=True))
    samples: List["Sample"] = Relationship(back_populates="children", link_model=SampleChildrenLink)


class Sample(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    md5: str = Field(alias='MD5')
    sha1: str = Field(alias='SHA1')
    sha256: str = Field(alias='SHA256', sa_column=Column("sha256", VARCHAR(64), unique=True))
    actor_id: Optional[int] = Field(default=None, foreign_key="actor.id")
    actor: Optional[Actor] = Relationship(back_populates="samples")
    file_type_id: Optional[int] = Field(default=None, foreign_key="filetype.id")
    file_type: Optional[FileType] = Relationship(back_populates="samples")
    report_id: Optional[int] = Field(default=None, foreign_key="report.id")
    report: Optional[Report] = Relationship(back_populates="samples")
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
