import os
import pefile
import requests
from typing import List
from pathlib import Path
from urllib.parse import urljoin
from fastapi.logger import logger
from subprocess import run, STDOUT, DEVNULL
from pydantic import AnyHttpUrl, ValidationError

from app.config import Secrets, get_secrets
from app.models import UserFunctions, Status


# file path to IDA command line tools
linux: bool = None
idat32: Path = None
idat64: Path = None

# environment variables for IDA Pro
env: dict = os.environ

# BinAuthor API endpoint
bin_author_api: AnyHttpUrl = None


def ida_setup():
    """
    Setup IDA Pro environment
    """
    # get global variables
    global linux, idat32, idat64, env, bin_author_api

    # get secrets object
    secrets: Secrets = get_secrets()

    # identify IDA Pro executable command line tools
    idat32_elf = secrets.IDADIR / "idat"
    idat64_elf = secrets.IDADIR / "idat64"
    idat32_exe = secrets.IDADIR / "idat.exe"
    idat64_exe = secrets.IDADIR / "idat64.exe"
    if os.path.isfile(idat32_elf) and os.path.isfile(idat64_elf):
        linux = True
        idat32 = idat32_elf
        idat64 = idat64_elf
    elif os.path.isfile(idat32_exe) and os.path.isfile(idat64_exe):
        linux = False
        idat32 = f'"{idat32_exe}"'
        idat64 = f'"{idat64_exe}"'
    else:
        raise Exception("Required IDA Pro executables for 32 and 64 bit not found")

    # identify BinAuthor API endpoint
    bin_author_api = secrets.BIN_AUTHOR_API

    # set environment variables for IDA Pro
    for k, v in secrets.dict(exclude_none=True).items():
        env[k] = str(v)


def get_user_functions(sha256: str) -> List[str]:
    """
    Fetch user-functions of binary from BinAuthor API
    :param sha256: hash of binary
    :return: user-functions
    """
    try:
        # get user-functions of binary from BinAuthor API endpoint
        r: requests.Response = requests.get(urljoin(bin_author_api, f'user-functions/{sha256}'))
        if r.ok:
            # validate response model
            response: UserFunctions = UserFunctions.parse_raw(r.content)
            if response.status != Status.OK:
                logger.warning(f"Unexpected status in response: {response.status}")
            elif response.sha256 == sha256:
                logger.warning(f"File hashes do not match: {response.sha256} != {sha256}")
            else:
                return response.user_functions
        else:
            logger.warning(f"Unexpected status code from BinAuthor API: {r.status_code}")
    except ValidationError as error:
        logger.error(f"Unexpected model received from BinAuthor API: {error}")
    except requests.exceptions.RequestException as error:
        logger.error(f"Unexpected error received from BinAuthor API: {error}")
    return []


def cleanup(file: str):
    # clean up IDA remains
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


def decompile(file: str, user_only: bool = True, log: bool = True):
    """
    Spawns a new process to decompile file with IDA Pro / Hex-Rays
    :param file: path to binary
    :param user_only: decompile only user functions if labelled by BinAuthor
    :param log: create log file
    """
    # skip if sample has already been decompiled
    c_file = file + ".c"
    if os.path.isfile(c_file) and os.path.getsize(c_file) > 312:
        logger.info(f"Sample has already been decompiled: {file}")
        return
    try:
        # check if binary is a valid PE file
        pe = pefile.PE(file, fast_load=True)
        # determine architecture
        pe64: bool = True if pe.FILE_HEADER.Machine == 0x8664 else False
    except pefile.PEFormatError:
        logger.error(f"Not a valid PE file: {file}")
        return

    cleanup(file)

    # check if IDA database already exists to skip parsing of binary
    ida_idb = file + ".idb"
    ida_i64 = file + ".i64"
    if (not pe64 and os.path.isfile(ida_idb)) or (pe64 and os.path.isfile(ida_i64)):
        logger.info(f"Sample has already been analyzed by IDA Pro. Use existing IDA database ...")
        sample = ida_i64 if pe64 else ida_idb
    else:
        sample = file

    # check if BinAuthor already labelled user-functions and if so use them
    functions: str = "ALL"
    if user_only:
        user_functions = get_user_functions(file[-64:])
        if len(user_functions) != 0:
            functions = ":".join(user_functions)
            logger.info(f"Decompile user functions only ...")

    # remove log file if exists
    log_file = f"{file}_bda.log"
    if log and os.path.isfile(log_file):
        logger.info(f"Remove log file: {log_file}")
        os.remove(log_file)

    # spawn a new process to decompile binary with IDA Pro and Hex-Rays
    args = f'{idat64 if pe64 else idat32} -Ohexrays:{c_file}:{functions}{f" -L{log_file}" if log else ""} -A {sample}'
    p = run(args=args, executable="/bin/bash" if linux else None, stderr=STDOUT, stdout=DEVNULL, shell=True, env=env)

    if not os.path.isfile(c_file) or os.path.getsize(c_file) == 0:
        logger.error(f"Failed to decompile file: {file}")
    elif os.path.getsize(c_file) <= 312:
        logger.error(f"No function has been decompiled: {file}")
        os.remove(c_file)
    else:
        logger.info(f"Successfully decompiled file: {file}")

    cleanup(file)
