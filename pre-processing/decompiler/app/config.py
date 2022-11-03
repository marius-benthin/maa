from typing import Optional
from functools import lru_cache
from pydantic import BaseSettings, DirectoryPath, AnyHttpUrl


class Settings(BaseSettings):
    debug: bool = False
    title: str = "bda-api"
    description: str = "BDA - API"


class Version(BaseSettings):
    version: str

    class Config:
        # load version number from environment file
        env_file = "VERSION"


class Secrets(BaseSettings):
    # volume with malware samples
    SAMPLES: DirectoryPath
    # BinAuthor API endpoint
    BIN_AUTHOR_API: AnyHttpUrl
    # IDA environment variables -> https://www.hex-rays.com/products/ida/support/idadoc/1375.shtml
    IDADIR: DirectoryPath
    IDAUSR: Optional[DirectoryPath]
    TVHEADLESS: int = 1
    # IDA license server address -> https://hex-rays.com/products/ida/support/flexlm/
    HEXRAYS_LICENSE_FILE: Optional[str]

    class Config:
        # load secrets from environment file
        env_file = ".env"


@lru_cache()
def get_secrets() -> Secrets:
    """
    Returns secrets object and caches it
    :return: secrets
    """
    return Secrets()
