FROM ida-pro AS bin-author-api

# Installing requirements for image
COPY requirements.txt /installation/requirements.txt
RUN pip3 install --no-cache-dir -r /installation/requirements.txt

WORKDIR /ida/python/3/
RUN git init
RUN git remote add origin https://github.com/marius-benthin/BinAuthor.git
RUN git pull origin master

RUN pip3 install --no-cache-dir -r requirements.txt

COPY ./app /app

WORKDIR /

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]