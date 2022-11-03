from enum import Enum
from typing import List
from pydantic import BaseModel


class Status(str, Enum):
    OK = "ok"
    FILE_NOT_FOUND = "file_not_found"


class Task(BaseModel):
    sha256: str
    status: Status = Status.OK
    message: str = ""
    children: List[str] = []


class UserFunctions(BaseModel):
    sha256: str
    status: Status = Status.OK
    user_functions: List[str] = []
