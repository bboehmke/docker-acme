FROM python:3.6-alpine

MAINTAINER Benjamin Böhmke <benjamin@boehmke.net>

RUN apk add --no-cache openssl wget && \
    wget https://download.docker.com/linux/static/stable/x86_64/docker-17.09.0-ce.tgz && \
    tar xvzf docker-17.09.0-ce.tgz docker/docker && mv docker/docker /bin/docker && \
    rm -r docker-17.09.0-ce.tgz docker && \
    mkdir /acme/

ADD https://raw.githubusercontent.com/diafygi/acme-tiny/master/acme_tiny.py /acme_tiny.py
ADD entrypoint.py /entrypoint.py

VOLUME /acme/config/
VOLUME /acme/crt/
VOLUME /acme/acme_challenge/

WORKDIR /acme/

ENTRYPOINT ["python", "/entrypoint.py"]
