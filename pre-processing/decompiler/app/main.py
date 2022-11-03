import os
from pathlib import Path
from pydantic import constr
from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse

from app.models import Status, Task
from app.decompile import ida_setup, decompile
from app.config import Version, Settings, Secrets, get_secrets


# create FastAPI with custom parameter values
app: FastAPI = FastAPI(**Settings().dict())

# set version number from VERSION file
app.version = Version().version


@app.on_event("startup")
async def on_startup():
    """
    Configure environment on startup
    """
    # setup IDA Pro environment
    ida_setup()


@app.get('/', include_in_schema=False)
async def root():
    """
    Redirect user to swagger documentation
    """
    # redirect to documentation
    return RedirectResponse(app.docs_url)


@app.post('/decompile/{sha256}', response_model=Task, tags=["Samples"], status_code=201)
async def add_decompile_task(
        *,
        sha256: constr(regex=r'^[a-fA-F0-9]{64}$'),
        user_only: bool = True,
        secrets: Secrets = Depends(get_secrets),
        background_tasks: BackgroundTasks
):
    """
    Decompile binary
    :param sha256: hash of binary
    :param user_only: decompile only user functions if labelled by BinAuthor
    :param secrets: credential dependency
    :param background_tasks: task queue
    :return: response message
    """
    sha256: str = sha256.lower()
    # construct directory path of binary
    file_path: Path = Path(secrets.SAMPLES, sha256[0:2], sha256)
    # check if binary is already uploaded to sample volume
    if not os.path.isfile(file_path / sha256):
        error: Task = Task(status=Status.FILE_NOT_FOUND, message="File not found on disk", sha256=sha256)
        return JSONResponse(status_code=404, content=error.dict())
    else:
        response: Task = Task(message="Added decompile task", sha256=sha256)
        # add decompile task for parent binary
        background_tasks.add_task(decompile, str(file_path / sha256), user_only)
        # check if binary has unpacked children
        dumps: Path = file_path / "dumps"
        if os.path.isdir(dumps):
            for dump in os.listdir(dumps):
                dump_path: Path = dumps / dump
                if os.path.isfile(dump_path / dump):
                    # add decompile task for unpacked children of binary
                    background_tasks.add_task(decompile, str(dump_path / dump), user_only)
                    response.children.append(dump)
        return response
