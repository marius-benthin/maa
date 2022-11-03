# Based on: https://github.com/intezer/docker-ida/blob/master/ida/Dockerfile
FROM ida-pro-base AS ida-pro

ARG IDA_INSTALLATION_FILE=ida.run
ARG IDA_PASSWORD

# Run IDA installation
COPY $IDA_INSTALLATION_FILE /installation/
RUN chmod a+x /installation/$IDA_INSTALLATION_FILE
# -> echo keyboard input including installation password, "yes" commands, Python3 (option [2]) and Hex-Rays Decompilers
RUN printf "\n\n\n\n\n\ny\n/ida\n2\n$IDA_PASSWORD\nY\n\n" | /installation/ida.run

RUN mkdir -p /ida

# Copy IDA registry file to accept license
#RUN mkdir -p /root/.idapro
#COPY ida.reg /root/.idapro

ENV PATH /ida:$PATH
ENV TERM xterm
ENV PYTHONPATH /usr/local/lib/python3.9/dist-packages:/usr/local/lib/python3.9/site-packages:/usr/lib/python3.9/:$PYTHONPATH