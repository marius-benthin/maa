from typing import Optional, List

from pydantic import BaseModel
from sqlalchemy import Column, VARCHAR
from sqlmodel import SQLModel, Field, Relationship


__author__ = "Marius Benthin"


class Actor(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str


class Country(Actor, table=True):
    groups: List["Group"] = Relationship(back_populates="country")


class Group(Actor, table=True):
    samples: List["Sample"] = Relationship(back_populates="group")
    aliases: List["Alias"] = Relationship(back_populates="group")
    country_id: Optional[int] = Field(default=None, foreign_key="country.id")
    country: Optional[Country] = Relationship(back_populates="groups")


class Alias(Actor, table=True):
    group_id: Optional[int] = Field(default=None, foreign_key="group.id")
    group: Optional[Group] = Relationship(back_populates="aliases")


class FileType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    samples: List["Sample"] = Relationship(back_populates="file_type")


class ReportSampleLink(SQLModel, table=True):
    sample_id: Optional[int] = Field(default=None, foreign_key="sample.id", primary_key=True)
    report_id: Optional[int] = Field(default=None, foreign_key="report.id", primary_key=True)


class Report(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    path: str
    sha256: str = Field(sa_column=Column("sha256", VARCHAR(64), unique=True))
    samples: List["Sample"] = Relationship(back_populates="reports", link_model=ReportSampleLink)


class SampleChildrenLink(SQLModel, table=True):
    sample_id: Optional[int] = Field(default=None, foreign_key="sample.id", primary_key=True)
    child_id: Optional[int] = Field(default=None, foreign_key="child.id", primary_key=True)


class Child(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sha256: str = Field(sa_column=Column("sha256", VARCHAR(64), unique=True))
    samples: List["Sample"] = Relationship(back_populates="children", link_model=SampleChildrenLink)


class Sample(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    md5: str
    sha1: str
    sha256: str
    group_id: Optional[int] = Field(default=None, foreign_key="group.id")
    group: Optional[Group] = Relationship(back_populates="samples")
    file_type_id: Optional[int] = Field(default=None, foreign_key="filetype.id")
    file_type: Optional[FileType] = Relationship(back_populates="samples")
    reports: List[Report] = Relationship(back_populates="samples", link_model=ReportSampleLink)
    fold_id: Optional[int] = Field(default=None, nullable=True)
    children: List[Child] = Relationship(back_populates="samples", link_model=SampleChildrenLink)


class EnsembleSample(BaseModel):
    fold_id: int
    label: str
    model_A: bool
    model_B: bool
    model_C: bool
    children: List[Child] = []
