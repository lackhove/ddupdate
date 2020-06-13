FROM python:3

WORKDIR /ddupdate

RUN pip install --no-cache-dir requests

COPY ddupdate.py ./

CMD [ "python", "./ddupdate.py", "--config", "/ddupdate/config.ini" ]
