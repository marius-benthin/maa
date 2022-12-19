import logging
from pathlib import Path
from numpy import ndarray, savez_compressed
from typing import Dict, Set, List, Tuple, Optional
from sklearn.feature_extraction.text import CountVectorizer
from sqlmodel import create_engine, SQLModel, Session, select

from models.config import Config
from models.models import Sample
from vmray import SummaryV1, File, Url, Mutex, Registry, Process, Technique, VmAndAnalyzerDetails, FileCategory


__author__ = "Marius Benthin"


# load secrets from environment
config = Config()

# create database connection and tables
sql_engine = create_engine(config.database_url)
SQLModel.metadata.create_all(sql_engine)


def decompose_artifacts(artifacts: Optional[List[str]]) -> Tuple[Dict[str, int], Set[str]]:
    dynamic_features: Dict[str, int] = {}
    dynamic_vocabulary: Set[str] = set()
    if artifacts is not None:
        try:
            ngram_range = (config.n_gram_model_C, config.n_gram_model_C)
            cv = CountVectorizer(decode_error='ignore', ngram_range=ngram_range, analyzer='char')
            n_gram_frequencies: ndarray = cv.fit_transform(artifacts).toarray()
            n_gram_vocabulary: ndarray = cv.get_feature_names_out()
            if n_gram_frequencies is not None and n_gram_vocabulary is not None:
                j: int = 0
                for n_gram in n_gram_vocabulary:
                    dynamic_vocabulary.add(n_gram)
                    if n_gram not in dynamic_features.keys():
                        dynamic_features[n_gram] = 0
                    for string in n_gram_frequencies:
                        dynamic_features[n_gram] += string[j]
                    j += 1
        except ValueError as e:
            logging.warning(f"{e}")
    return dynamic_features, dynamic_vocabulary


def extract_files(files: List[File], details: VmAndAnalyzerDetails) -> Tuple[Dict[str, int], Set[str]]:
    artifacts: List[str] = []
    for file in files:
        if file.category in [
            FileCategory.dropped, FileCategory.modified, FileCategory.accessed, FileCategory.code_dump
        ]:
            tmp_dir = details.vm_temp_dir.lower()
            usr_dir = details.vm_user_profile.lower()
            short_path = tmp_dir.replace('\\appdata\\local\\temp', '')
            filename = file.filename.lower()
            filename = filename.replace(tmp_dir, '%TMP%')
            filename = filename.replace(short_path, '%USR%')
            filename = filename.replace(usr_dir, '%USR%')
            artifacts.append(filename)
    return decompose_artifacts(artifacts=artifacts)


def extract_urls(urls: List[Url]) -> Tuple[Dict[str, int], Set[str]]:
    artifacts: List[str] = []
    for url in urls:
        artifacts.append(url.url)
    return decompose_artifacts(artifacts=artifacts)


def extract_mutexes(mutexes: List[Mutex]) -> Tuple[Dict[str, int], Set[str]]:
    artifacts: List[str] = []
    for mutex in mutexes:
        artifacts.append(mutex.mutex_name)
    return decompose_artifacts(artifacts=artifacts)


def extract_registry_keys(registry_keys: List[Registry]) -> Tuple[Dict[str, int], Set[str]]:
    artifacts: List[str] = []
    for registry_key in registry_keys:
        artifacts.append(registry_key.reg_key_name)
    return decompose_artifacts(artifacts=artifacts)


def extract_processes(
        processes: List[Process], sha256: str, details: VmAndAnalyzerDetails
) -> Tuple[Dict[str, int], Set[str]]:
    artifacts: List[str] = []
    for process in processes:
        if process.cmd_line is not None and sha256 not in process.cmd_line:
            tmp_dir = details.vm_temp_dir.lower()
            usr_dir = details.vm_user_profile.lower()
            short_path = tmp_dir.replace('\\appdata\\local\\temp', '')
            cmd_line = process.cmd_line.lower()
            cmd_line = cmd_line.replace(tmp_dir, '%TMP%')
            cmd_line = cmd_line.replace(short_path, '%USR%')
            cmd_line = cmd_line.replace(usr_dir, '%USR%')
            artifacts.append(cmd_line)
    return decompose_artifacts(artifacts=artifacts)


def extract_techniques(techniques: List[Technique]) -> Tuple[Dict[str, int], Set[str]]:
    mitre_artifacts: Dict[str, int] = {}
    mitre_vocabulary: Set[str] = set()
    for technique in techniques:
        mitre_artifacts[technique.id] = 1
        mitre_vocabulary.add(technique.id)
    return mitre_artifacts, mitre_vocabulary


def parse_report(sha256: str) -> Tuple[Dict[str, Dict[str, int]], Dict[str, Set[str]]]:
    vmray_report: Path = config.sample_folder / sha256[0:2] / sha256 / f'{sha256}_vmray.json'
    logging.info(f"Parsing {vmray_report}")
    dynamic_features: Dict[str, Dict[str, int]] = {
        "files": {},
        "urls": {},
        "mutexes": {},
        "registries": {},
        "processes": {},
        "mitre": {},
    }
    dynamic_vocabulary: Dict[str, Set[str]] = {
        "files": set(),
        "urls": set(),
        "mutexes": set(),
        "registries": set(),
        "processes": set(),
        "mitre": set(),
    }
    try:
        content: SummaryV1 = SummaryV1.parse_file(vmray_report)

        vector_files: Tuple[Dict[str, int], Set] = extract_files(
            files=content.artifacts.files,
            details=content.vm_and_analyzer_details
        )
        dynamic_features["files"] = vector_files[0]
        dynamic_vocabulary["files"] = vector_files[1]

        vector_urls: Tuple[Dict[str, int], Set] = extract_urls(
            urls=content.artifacts.urls
        )
        dynamic_features["urls"] = vector_urls[0]
        dynamic_vocabulary["urls"] = vector_urls[1]

        vector_mutexes: Tuple[Dict[str, int], Set] = extract_mutexes(
            mutexes=content.artifacts.mutexes
        )
        dynamic_features["mutexes"] = vector_mutexes[0]
        dynamic_vocabulary["mutexes"] = vector_mutexes[1]

        vector_registry_keys: Tuple[Dict[str, int], Set] = extract_registry_keys(
            registry_keys=content.artifacts.registry
        )
        dynamic_features["registries"] = vector_registry_keys[0]
        dynamic_vocabulary["registries"] = vector_registry_keys[1]

        vector_processes: Tuple[Dict[str, int], Set] = extract_processes(
            processes=content.artifacts.processes,
            sha256=sha256,
            details=content.vm_and_analyzer_details
        )
        dynamic_features["processes"] = vector_processes[0]
        dynamic_vocabulary["processes"] = vector_processes[1]

        vector_mitre: Tuple[Dict[str, int], Set] = extract_techniques(
            techniques=content.mitre_attack.techniques
        )
        dynamic_features["mitre"] = vector_mitre[0]
        dynamic_vocabulary["mitre"] = vector_mitre[1]

    except FileNotFoundError as e:
        logging.error(e)

    return dynamic_features, dynamic_vocabulary


if __name__ == "__main__":

    vocabulary: Dict[str, Set[str]] = {
        "files": set(),
        "urls": set(),
        "mutexes": set(),
        "registries": set(),
        "processes": set(),
        "mitre": set(),
    }
    samples: List[Dict[str, Dict[str, int]]] = []
    # Tuple -> (Parent ID, Child ID or None)
    sample_ids: List[Tuple[int, Optional[int]]] = []

    # parse all VMRay reports and extract dynamic artifacts for each sample
    with Session(sql_engine) as session:
        # get all parent samples
        parents: List[Sample] = session.exec(select(Sample).where(Sample.fold_id != None).order_by(Sample.id)).all()
        for parent in parents:
            features: Tuple[Dict[str, Dict[str, int]], Dict[str, Set[str]]] = parse_report(sha256=parent.sha256)
            sample_ids.append((parent.id, None,))
            samples.append(features[0])
            vocabulary["files"] = vocabulary["files"].union(features[1]["files"])
            vocabulary["urls"] = vocabulary["urls"].union(features[1]["urls"])
            vocabulary["mutexes"] = vocabulary["mutexes"].union(features[1]["mutexes"])
            vocabulary["registries"] = vocabulary["registries"].union(features[1]["registries"])
            vocabulary["processes"] = vocabulary["processes"].union(features[1]["processes"])
            vocabulary["mitre"] = vocabulary["mitre"].union(features[1]["mitre"])

    # map dynamic artifact frequencies into numpy feature vector
    dynamic_artifacts: List = []
    dynamic_artifacts.extend(vocabulary["files"])
    dynamic_artifacts.extend(vocabulary["urls"])
    dynamic_artifacts.extend(vocabulary["mutexes"])
    dynamic_artifacts.extend(vocabulary["registries"])
    dynamic_artifacts.extend(vocabulary["processes"])
    dynamic_artifacts.extend(vocabulary["mitre"])
    feature_vector: ndarray = ndarray(shape=(len(samples), len(dynamic_artifacts)))
    for i in range(len(samples)):
        for dynamic_artifact, frequency in samples[i]["files"].items():
            feature_vector[i][dynamic_artifacts.index(dynamic_artifact)] = frequency
        for dynamic_artifact, frequency in samples[i]["urls"].items():
            feature_vector[i][dynamic_artifacts.index(dynamic_artifact)] = frequency
        for dynamic_artifact, frequency in samples[i]["mutexes"].items():
            feature_vector[i][dynamic_artifacts.index(dynamic_artifact)] = frequency
        for dynamic_artifact, frequency in samples[i]["registries"].items():
            feature_vector[i][dynamic_artifacts.index(dynamic_artifact)] = frequency
        for dynamic_artifact, frequency in samples[i]["processes"].items():
            feature_vector[i][dynamic_artifacts.index(dynamic_artifact)] = frequency
        for dynamic_artifact, frequency in samples[i]["mitre"].items():
            feature_vector[i][dynamic_artifacts.index(dynamic_artifact)] = frequency

    # export numpy feature vector
    savez_compressed(file=config.numpy_file_model_C, X=feature_vector, sample_ids=sample_ids, features=dynamic_artifacts)
