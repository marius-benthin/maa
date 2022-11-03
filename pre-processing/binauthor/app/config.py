from functools import lru_cache
from pydantic import BaseSettings, DirectoryPath


class Settings(BaseSettings):
    debug: bool = False
    title: str = "bin-author-api"
    description: str = "BinAuthor - API"
    version: str = "0.0.1"


class Secrets(BaseSettings):
    ida_path: DirectoryPath
    ida_home: DirectoryPath = None
    ida_license_server: str
    upload_dir: DirectoryPath
    bin_author_path: DirectoryPath
    mongodb_uri: str
    mongodb_database: str

    class Config:
        env_file = ".env"


@lru_cache()
def get_secrets() -> Secrets:
    return Secrets()
