from typing import Optional, List
from sqlalchemy import Column, VARCHAR
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseSettings

__author__ = "Marius Benthin"


class Config(BaseSettings):
    database_url: str
    mongodb_url: str
    numpy_file: str
    n_gram: int

    class Config:
        env_file = ".env"


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
    fold_id: Optional[int]
    children: List[Child] = Relationship(back_populates="samples", link_model=SampleChildrenLink)
