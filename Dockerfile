FROM docker.io/python:3.9

RUN apt-get update && apt-get install -y \
    iproute2  \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /ddupdate

RUN pip install --no-cache-dir requests

COPY ddupdate.py ./

CMD [ "python", "-u", "./ddupdate.py", "--config", "/ddupdate/config.ini" ]
