# Based on: https://github.com/intezer/docker-ida/blob/master/ida-base/Dockerfile

# This is the foundation for all language-stack images (see: https://hub.docker.com/_/buildpack-deps/)
FROM buildpack-deps AS ida-pro-base

# Add 32 bit architecture support for IDA
RUN dpkg --add-architecture i386 && apt-get -y update

# Replace the python version in the original image with a 32-bit version, so when we install external libraries -
# IDAPython (32bit) could import them
RUN apt-get -y install python3.9-minimal:i386
RUN apt-get -y install python3.9:i386
# Create a symlink for python for convenience (instead of typing python3.9)
RUN link /usr/bin/python3.9 /usr/bin/python

# Install necessary libraries for IDA and IDAPython to work
RUN apt-get -y install --fix-missing \
    lib32gcc-s1 \
    libc6-i686:i386 \
    libfontconfig:i386 \
    libfreetype6:i386 \
    libglib2.0-0:i386 \
    libpython3.9:i386 \
    libsm6:i386 \
    libssl-dev:i386 \
    libstdc++6:i386 \
    libxext6:i386 \
    libxrender1:i386 \
    python3.9-dev

# Remove packages that are no longer required
RUN apt -y autoremove

# Install pip for python 3.9
RUN apt-get -y install python3-pip
RUN pip3 install --upgrade pip