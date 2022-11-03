# BinAuthor API

## Description
This Docker image deploys an API to disassemble multiple samples in parallel and extract user-related functions using the BinAuthor IDA Pro plugin developed by Alrabaee et al. 
The strings will be stored in a MongoDB which is deployed via the `docker-compose.yml`.
Please note that the BinAuthor plugin has been upgraded to Python 3 in order to work with IDA Pro 7.7.

## Development Details
- [Python 3.9](https://peps.python.org/pep-0596/)
- [IDA Pro 7.7](https://www.hex-rays.com/products/ida/news/7_7sp1/)
- [BinAuthor](https://github.com/marius-benthin/BinAuthor)
- [FastAPI](https://fastapi.tiangolo.com/)
- [MongoDB](https://www.mongodb.com/)

## Requirements
This image requires the `ida-pro` Docker image that can be found in the `../ida-pro/` folder.
The BinAuthor plugin will be automatically pulled from GitHub.

## Environment
You have to specify certain environment variables, for instance, through a `binauthor/.env` file, which are listed below.

```
MONGODB_URI="mongodb://mongo:27017"
MONGODB_DATABASE="BinAuthor"
MONGODB_STORAGE="/home/binauthor/mongodb/"
IDA_PATH=/ida
IDA_HOME=/root/.idapro
IDA_LICENSE_SERVER=@servername
BIN_AUTHOR_PATH=/ida/python/3
UPLOAD_DIR=/samples
UPLOAD_DIR_HOST=/home/binauthor/data/
API_PORT=8000
```