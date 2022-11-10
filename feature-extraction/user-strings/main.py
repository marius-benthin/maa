import logging
import pymongo
from typing import Dict, Set, List, Tuple, Optional
from numpy import ndarray, savez_compressed
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import CountVectorizer
from sqlmodel import create_engine, SQLModel, Session, select
from models import Sample, Config

__author__ = "Marius Benthin"


# load secrets from environment
config = Config()

# create database connection and tables
sql_engine = create_engine(config.database_url)
SQLModel.metadata.create_all(sql_engine)

# create MongoDB connection
client = pymongo.MongoClient(config.mongodb_url)
database = client.get_database("BinAuthor")
collection = database.get_collection("Strings")


def decompose_n_grams(sha256: str) -> Tuple[ndarray, ndarray]:
    document = collection.find_one({"FileSHA256": sha256.lower()})
    # transform string corpus to ngrams
    cv = CountVectorizer(decode_error='ignore', ngram_range=(config.n_gram, config.n_gram), analyzer='char')
    try:
        if document is not None:
            n_gram_frequencies: csr_matrix = cv.fit_transform(document["Strings"])
            n_gram_vocabulary: ndarray = cv.get_feature_names_out()
            if n_gram_frequencies is not None and n_gram_vocabulary is not None:
                return n_gram_frequencies.toarray(), n_gram_vocabulary
        else:
            logging.warning(f"Sample {sha256} not found in MongoDB")
    except ValueError as e:
        logging.warning(f"{e} -> {sha256}")
    return [], []


if __name__ == "__main__":

    n_grams: Set[str] = set()
    samples: List[Dict[str, int]] = []
    # Tuple -> (Parent ID, Child ID or None)
    sample_ids: List[Tuple[int, Optional[int]]] = []

    # decompose user-related strings into n-grams for each sample
    with Session(sql_engine) as session:
        # get all parent samples
        parents: List[Sample] = session.exec(select(Sample).where(Sample.fold_id != None).order_by(Sample.id)).all()
        for parent in parents:
            # if sample is not packed or has no children
            if len(parent.children) == 0:
                vector: Tuple[ndarray, ndarray] = decompose_n_grams(sha256=parent.sha256)
                features: Dict[str, int] = {}
                i: int = 0
                for n_gram in vector[1]:
                    n_grams.add(n_gram)
                    if n_gram not in features.keys():
                        features[n_gram] = 0
                    for string in vector[0]:
                        features[n_gram] += string[i]
                    i += 1
                sample_ids.append((parent.id, None,))
                samples.append(features)
            else:
                for child in parent.children:
                    vector: Tuple[ndarray, ndarray] = decompose_n_grams(sha256=child.sha256)
                    features: Dict[str, int] = {}
                    i: int = 0
                    for n_gram in vector[1]:
                        n_grams.add(n_gram)
                        if n_gram not in features.keys():
                            features[n_gram] = 0
                        for string in vector[0]:
                            features[n_gram] += string[i]
                        i += 1
                    sample_ids.append((parent.id, child.id,))
                    samples.append(features)

    # map user-related string n-gram frequencies into numpy feature vector
    n_grams: List = list(n_grams)
    feature_vector: ndarray = ndarray(shape=(len(samples), len(n_grams)))
    for i in range(len(samples)):
        for n_gram, frequency in samples[i].items():
            feature_vector[i][n_grams.index(n_gram)] = frequency

    # export numpy feature vector
    savez_compressed(file=config.numpy_file, X=feature_vector, sample_ids=sample_ids, features=n_grams)
