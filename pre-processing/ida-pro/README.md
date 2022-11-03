# IDA Pro Dockerized

## Description
This Docker images serve as base images for the user-related string extractor `../binauthor/` and decompiler `../decompiler/` components.
Please note that you first have to build the `ida-pro-base` image using `ida-pro/base/Dockerfile` and afterwards the `ida-pro` image using `ida-pro/Dockerfile`.

## Development Details
- [Python 3.9](https://peps.python.org/pep-0596/)
- [IDA Pro 7.7](https://www.hex-rays.com/products/ida/news/7_7sp1/)

## Requirements
To be able to use this image you have to own an IDA Pro 7.7 Linux installer (referred to as `ida.run`) and a proper license.
The Docker image `ida-pro-base` installs all the requirements and the image `ida-pro` automatically answers the questions asked in the IDA installation dialog.
Please note that the dialog differs between different IDA versions and must be adjusted accordingly for versions other than 7.7.

## User Agreement
If you run the `ida-pro` image for the very first time, you may connect via terminal to the Docker container and execute the IDA text interface `./idat`.
You will be prompted to accept the user agreement. Once you agreed, a new IDA registry file `/root/.idapro/ida.reg` will be created in background, which you can use in the future to skip the user agreement for new containers.
Therefore, you place the `ida.reg` file into the root directory `ida-pro/ida.reg` and uncomment the two lines in the `Dockerfile`:

```dockerfile
RUN mkdir -p /root/.idapro
COPY ida.reg /root/.idapro
```

Afterwards, the Docker image has to be built once again so that in the future the container can run without user interaction.