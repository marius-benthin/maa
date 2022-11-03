import os
import pefile
import hashlib
import aiofiles
from pathlib import Path
from pydantic import constr
from pymongo.cursor import Cursor
from subprocess import run, CompletedProcess
from fastapi import FastAPI, UploadFile, Depends, BackgroundTasks
from fastapi.logger import logger
from fastapi.responses import RedirectResponse, JSONResponse

from app.mongo import MongoDB
from app.models import JobResponse, UserFunctionsResponse
from app.config import Settings, Secrets, get_secrets

app = FastAPI(**Settings().dict())


# environment variables for IDA Pro
env: dict = {}
# file path to IDA command line tool
idat: Path = None
# file path to BinAuthor plugin
bin_author: Path = None


@app.on_event("startup")
async def startup_event():
    """
    Initializes IDA Pro configuration variables on startup
    """
    global env, idat, bin_author
    secrets: Secrets = get_secrets()
    idat_elf = secrets.ida_path / "idat64"
    idat_exe = secrets.ida_path / "idat64.exe"
    bin_author = secrets.bin_author_path / "BinAuthorPlugin" / "ExternalScripts" / "computeChoices.py"
    if not os.path.isfile(idat_elf) and not os.path.isfile(idat_exe):
        raise Exception("IDA Pro executable not found")
    elif not os.path.isfile(bin_author):
        raise Exception("BinAuthor plugin not found")
    else:
        idat = idat_exe if os.path.isfile(idat_exe) else idat_elf
        env = {
            "TVHEADLESS": "1",
            "BIN_AUTHOR_PATH": str(secrets.bin_author_path),
            "MONGODB_URI": str(secrets.mongodb_uri)
        }
        if secrets.ida_home is not None:
            env["IDAUSR"] = str(secrets.ida_home)
        if secrets.ida_license_server is not None:
            env["HEXRAYS_LICENSE_FILE"] = str(secrets.ida_license_server)


@app.get('/', include_in_schema=False)
async def root():
    """
    Redirect root path to documentation
    """
    return RedirectResponse(app.docs_url)


@app.post('/upload', tags=["Samples"], response_model=JobResponse)
async def upload_file(
        *,
        file: UploadFile,
        secrets: Secrets = Depends(get_secrets)
):
    """
    Upload file and write to disk for further processing
    :param file: file
    :param secrets: credential dependency
    :return: response message
    """
    content = await file.read()
    sha256 = hashlib.sha256(content).hexdigest()
    file_path = Path(secrets.upload_dir, sha256[0:2], sha256, sha256)
    if not os.path.isfile(file_path):
        # write file to disk if not already exists
        async with aiofiles.open(file_path, 'wb') as f:
            while content := await file.read(1024):
                await f.write(content)
        return JobResponse(status="ok", message="Successfully uploaded sample", file=sha256)
    else:
        return JobResponse(status="ok", message="File already exists on disk", file=sha256)


def disassemble(author: str, file: str, log: bool = True):
    """
    Spawns a new process to disassemble file with IDA Pro and BinAuthor plugin
    :param author: author name of file
    :param file: file hash
    :param log: create log file
    """
    try:
        pefile.PE(file, fast_load=True)
    except pefile.PEFormatError:
        logger.error(f"Not a valid PE file: {file}")
        return

    log_file = f"{file}_binauthor.log"
    if os.path.isfile(log_file):
        os.remove(log_file)

    process: CompletedProcess = run(
        args=f'{idat} -A -S"{bin_author} {author}"{f" -L{log_file}" if log else ""} {file}',
        executable='/bin/bash',
        shell=True,
        env=env
    )
    ida_id0 = file + '.id0'
    if os.path.isfile(ida_id0):
        os.remove(ida_id0)
    ida_id1 = file + '.id1'
    if os.path.isfile(ida_id1):
        os.remove(ida_id1)
    ida_nam = file + '.nam'
    if os.path.isfile(ida_nam):
        os.remove(ida_nam)
    ida_til = file + '.til'
    if os.path.isfile(ida_til):
        os.remove(ida_til)
    if not os.path.isfile(file + '.idb') and not os.path.isfile(file + '.i64'):
        logger.error(f"Failed to disassemble file: {file}")
    else:
        logger.info(f"Successfully disassembled file: {file}")


@app.post('/extract/{sha256}', tags=["Samples"])
async def extract_file_features(
        *,
        sha256: constr(regex=r'^[a-fA-F0-9]{64}$'),
        author: str,
        secrets: Secrets = Depends(get_secrets),
        background_tasks: BackgroundTasks
):
    """
    Extract features from file with BinAuthor
    :param sha256: SHA256 of the file
    :param author: author of file
    :param secrets: credential dependency
    :param background_tasks: task queue
    :return: response message
    """
    sha256 = sha256.lower()
    file_path = Path(secrets.upload_dir, sha256[0:2], sha256)
    if not os.path.isfile(file_path / sha256):
        error = JobResponse(status="file_not_found", message="File not found on disk", file=sha256)
        return JSONResponse(status_code=404, content=error.dict())
    else:
        job_response = JobResponse(message="Added feature extraction task", file=sha256)
        background_tasks.add_task(disassemble, author, str(file_path / sha256))
        dumps = file_path / "dumps"
        if os.path.isdir(dumps):
            for dump in os.listdir(dumps):
                dump_path = dumps / dump
                if os.path.isfile(dump_path / dump):
                    job_response.dumps.append(dump)
                    background_tasks.add_task(disassemble, author, str(dump_path / dump))
        return job_response


@app.get('/user-functions/{sha256}', tags=["Samples"])
async def get_user_functions(
        *,
        sha256: constr(regex=r'^[a-fA-F0-9]{64}$'),
        mongodb: MongoDB = Depends(MongoDB)
):
    """
    Returns user-functions for file
    :param sha256: SHA256 of the file
    :param mongodb: database dependency
    :return: user functions
    """
    sha256 = sha256.lower()
    response = UserFunctionsResponse(file=sha256)
    cursor: Cursor = mongodb.collection_function_labels.find({"SHA256": sha256, "type": "user"})
    for user_function in cursor:
        response.user_functions.append(user_function["function"])
    return response
