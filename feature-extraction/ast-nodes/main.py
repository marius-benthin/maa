import logging
from pathlib import Path
from typing import Dict, Set, List, Tuple, Optional
from numpy import ndarray, savez_compressed
from sqlmodel import create_engine, SQLModel, Session, select
from models import Sample, Config

__author__ = "Marius Benthin"


# load secrets from environment
config = Config()

# create database connection and tables
sql_engine = create_engine(config.database_url)
SQLModel.metadata.create_all(sql_engine)


def parse_ast(sha256: str) -> Dict[str, int]:
    ast_file: Path = config.sample_folder / sha256[0:2] / sha256 / f'{sha256}.ast'
    logging.info(f"Parsing {ast_file}")
    ast_features: Dict[str, int] = {}
    try:
        with open(ast_file, 'r') as f:
            # iterate over all lines of AST format
            for line in f:
                # if line starts with "type:" -> AST node type
                if line[0:5] == "type:":
                    ast_type = line[5:-1]
                    # exclude separators such as "\\"
                    if ast_type.isalpha():
                        ast_types.add(ast_type)
                        if ast_type in ast_features.keys():
                            ast_features[ast_type] += 1
                        else:
                            ast_features[ast_type] = 1
    except FileNotFoundError as e:
        logging.error(e)
    return ast_features


if __name__ == "__main__":

    ast_types: Set[str] = set()
    samples: List[Dict[str, int]] = []
    # Tuple -> (Parent ID, Child ID or None)
    sample_ids: List[Tuple[int, Optional[int]]] = []

    # parse all ASTs and extract nodes for each sample
    with Session(sql_engine) as session:
        # get all parent samples
        parents: List[Sample] = session.exec(select(Sample).where(Sample.fold_id != None).order_by(Sample.id)).all()
        for parent in parents:
            # if sample is not packed or has no children
            if len(parent.children) == 0:
                features: Dict[str, int] = parse_ast(sha256=parent.sha256)
                # NEW -> prevent fallback groups if no features are present
                if len(features) > 0:
                    sample_ids.append((parent.id, None,))
                    samples.append(features)
            else:
                for child in parent.children:
                    features: Dict[str, int] = parse_ast(sha256=child.sha256)
                    # NEW -> prevent fallback groups if no features are present
                    if len(features) > 0:
                        sample_ids.append((parent.id, child.id,))
                        samples.append(features)

    # map AST node frequencies into numpy feature vector
    ast_types: List = list(ast_types)
    feature_vector: ndarray = ndarray(shape=(len(samples), len(ast_types)))
    for i in range(len(samples)):
        for ast_node, frequency in samples[i].items():
            feature_vector[i][ast_types.index(ast_node)] = frequency

    # export numpy feature vector
    savez_compressed(file=config.numpy_file, X=feature_vector, sample_ids=sample_ids, features=ast_types)
