from typing import List
from pydantic import BaseModel


class JobResponse(BaseModel):
    status: str = "ok"
    message: str
    file: str
    dumps: list = []


class UserFunctionsResponse(BaseModel):
    status: str = "ok"
    file: str
    user_functions: List[str] = []
