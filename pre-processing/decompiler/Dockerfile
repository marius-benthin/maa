FROM ida-pro AS bda-api

# install application requirements
COPY requirements.txt /installation/requirements.txt
RUN pip3 install --no-cache-dir -r /installation/requirements.txt

# copy application code
COPY ./app /app

# copy version file
COPY ./VERSION /

# start web server
WORKDIR /
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]