# BDA API

## Description
This Docker image deploys an API to decompile multiple samples in parallel and produce pseudo-like C code using the Hex-Rays Decompiler. 
The C code will be stored on disk in the corresponding folder next to the sample.
Please note that the BinAuthor plugin has been upgraded to Python 3 in order to work with IDA Pro 7.7.

## Development Details
- [Python 3.9](https://peps.python.org/pep-0596/)
- [IDA Pro 7.7](https://www.hex-rays.com/products/ida/news/7_7sp1/)
- [BDA](https://github.com/calaylin/bda)
- [FastAPI](https://fastapi.tiangolo.com/)

## Requirements
This image requires the `ida-pro` Docker image that can be found in the `../ida-pro/` folder.
If you would like to decompile functions labelled by BinAuthor only, you have to run the `bin-author-api` container in parallel.

## Environment
You have to specify certain environment variables, for instance, through a `decompiler/.env` file, which are listed below.

```
IDADIR=/ida
IDAUSR=/root/.idapro
HEXRAYS_LICENSE_FILE=@servername
BIN_AUTHOR_API=http://host.docker.internal:8000/
SAMPLES=/samples
SAMPLES_HOST=/home/maa/data/
API_PORT=8001
```