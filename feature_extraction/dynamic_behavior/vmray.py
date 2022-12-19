import enum
from pydantic import BaseModel
from typing import List, Optional


class VmAndAnalyzerDetails(BaseModel):
    type: str = "vm_and_analyzer_details"
    version: int = 3
    vm_username: str
    vm_user_profile: str
    vm_user_domain: str
    vm_temp_dir: str
    vm_system_root: str
    vm_computer_name: str


class Reference(BaseModel):
    type: str = "reference"
    version: int = 1
    ref_id: str
    ref_source: str
    ref_type: str


class MemoryDump(BaseModel):
    type: str = "region_dump"
    version: int = 1
    ref_memory_dump: Reference


class Process(BaseModel):
    type: str = "process_artifact"
    version: int = 1
    cmd_line: Optional[str]
    image_name: str


class Network(BaseModel):
    type: str = "network"
    version: int = 1
    dns_requests: List
    http_requests: List
    https_requests: List
    tcp_sessions: List
    udp_sessions: List


class Technique(BaseModel):
    type: str = "mitre_attack_technique"
    version: int = 1
    technique_version: int = 1
    id: str
    description: str
    tactics: List[str]
    ref_vtis: List[Reference]


class MitreAttack(BaseModel):
    type: str = "mitre_attack"
    version: int = 1
    vmray_version: int = 1
    matrix_version: str
    techniques: List[Technique]


class ExtractedFile(BaseModel):
    type: str = "extracted_file"
    version: int = 3
    id: str
    file_type: str
    archive_path: Optional[str]
    filenames: List[str]
    ssdeep_hash: str
    size: int
    sha256_hash: str
    sha1_hash: str
    md5_hash: str
    imp_hash: str
    severity: str
    ref_static_data: Reference
    norm_filename: str


class Domain(BaseModel):
    type: str = "domain_artifact"
    version: int = 3
    domain: str


class Filename(BaseModel):
    type: str = "filename_artifact"
    version: int = 1
    filename: str


class FileCategory(str, enum.Enum):
    embedded = "EMBEDDED"
    code_dump = "CODE_DUMP"
    memory_dump = "MEMORY_DUMP"
    accessed = "ACCESSED"
    modified = "MODIFIED"
    script = "SCRIPT"
    misc = "MISC"
    dropped = "DROPPED"
    sample = "SAMPLE"


class File(BaseModel):
    type: str = "file_artifact"
    version: int = 3
    filename: Optional[str]
    category: FileCategory


class Operation(str, enum.Enum):
    delete = "delete"
    read = "read"
    access = "access"
    write = "write"
    create = "create"


class Registry(BaseModel):
    type: str = "registry_artifact"
    version: int = 2
    reg_key_name: str
    operations: List[Operation]


class Url(BaseModel):
    type: str = "url_artifact"
    version: int = 4
    url: str
    user_agents: List
    categories: List


class Mutex(BaseModel):
    type: str = "mutex_artifact"
    version: int = 2
    mutex_name: str
    operations: List[Operation]


class Ip(BaseModel):
    type: str = "ip_address_artifact"
    version: int = 3
    ip_address: str


class Email(BaseModel):
    type: str = "email_address_artifact"
    version: int = 2
    email_address: str


class Artifacts(BaseModel):
    type: str = "artifacts"
    version: int = 3
    urls: List[Url]
    registry: List[Registry]
    processes: List[Process]
    mutexes: List[Mutex]
    ips: List[Ip]
    files: List[File]
    filenames: List[Filename]
    email_addresses: List[Email]
    domains: List[Domain]


class SampleDetails(BaseModel):
    sha256_hash: str


class SummaryV1(BaseModel):
    type: str = "summary"
    version: int = 7
    artifacts: Artifacts
    mitre_attack: MitreAttack
    sample_details: SampleDetails
    vm_and_analyzer_details: VmAndAnalyzerDetails
