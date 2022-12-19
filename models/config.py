from pathlib import Path
from pydantic import BaseSettings, DirectoryPath, MongoDsn, AnyUrl, FilePath


__author__ = "Marius Benthin"


class Config(BaseSettings):

    # dataset files and storages
    sample_folder: DirectoryPath
    database_url: AnyUrl
    mongodb_url: MongoDsn

    # CSV files
    aptclass_csv: FilePath = Path("datasets", "aptclass", "2022-aug-aptclass_dataset.csv")
    cyberresearch_csv: FilePath = Path("datasets", "cyberresearch", "overview.csv")

    # dataset parsing
    alias_aware: bool = True
    alias_json: FilePath = Path("datasets", "aptclass", "aliases.json")
    n_splits: int = 8

    # n-gram feature extraction
    n_gram_model_A: int = 3
    n_gram_model_C: int = 2
    proportion: int = 10

    # numpy files
    numpy_file_model_A: str
    numpy_file_model_B: str
    numpy_file_model_C: str

    # machine learning parameters
    epochs: int = 100
    max_iter: int = 1000000
    learning_rate: float = 0.0001
    random_state: int = 42

    # size of confusion matrix
    cm_size: int = 20

    class Config:
        env_file = ".env"
