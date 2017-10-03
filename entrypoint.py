#!/usr/bin/env python
import logging
import os
import shutil
import subprocess
import time
import configparser
from datetime import datetime
from urllib.request import urlopen

import acme_tiny

crt_dir = "crt/"
crt_bak_dir = "crt/backup/"
tmp_dir = "tmp/"
acme_challenge_dir = "acme_challenge/"

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

#DEFAULT_CA = "https://acme-staging.api.letsencrypt.org"
DEFAULT_CA = "https://acme-v01.api.letsencrypt.org"

crt_max_age = os.getenv("CRT_MAX_AGE", 30)  # in days
chained_crt = os.getenv("CHAINED_CRT", "true")
acme_ca = os.getenv("ACME_CA", DEFAULT_CA)
acme_intermediate = os.getenv(
    "ACME_INTERMEDIATE",
    "https://letsencrypt.org/certs/lets-encrypt-x3-cross-signed.pem")
container_notify = os.getenv("CONTAINER_NOTIFY")


def check_crt(name):
    crt_file = "%s/%s.crt" % (crt_dir, name)

    if not os.path.isfile(crt_file):
        return False

    proc = subprocess.Popen(
        ["openssl", "x509", "-noout", "-startdate",
         "-in", crt_file],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    out, err = proc.communicate()
    if proc.returncode != 0:
        raise IOError("OpenSSL Error: {0}".format(err))

    time = datetime.strptime(out.decode("utf8").strip().split("=")[1],
                             "%b %d %H:%M:%S %Y %Z")

    return (datetime.now()-time).days < crt_max_age


def exist_key(name):
    return os.path.isfile("%s/%s.key" % (crt_dir, name))


def create_key(name):
    if exist_key(name):
        shutil.copyfile(
            "%s/%s.key" % (crt_dir, name),
            "%s/%s_%s.key" % (crt_bak_dir,
                              datetime.now().strftime("%Y%m%d_%H%M%S"),
                              name))

    proc = subprocess.Popen(
        ["openssl", "genrsa", "4096"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    out, err = proc.communicate()
    if proc.returncode != 0:
        raise IOError("OpenSSL Error: {0}".format(err))

    with open("%s/%s.key" % (crt_dir, name), "wb") as file:
        file.write(out)


def create_csr(name, domains):
    ssl_conf = tmp_dir + "openssl.cnf"
    shutil.copyfile("/etc/ssl/openssl.cnf", ssl_conf)
    with open(ssl_conf, "a") as file:
        file.write("\n[SAN]\n")
        file.write("subjectAltName=DNS:%s" % ",DNS:".join(domains))

    proc = subprocess.Popen(
        ["openssl", "req", "-new", "-sha256",
         "-key", "%s/%s.key" % (crt_dir, name),
         "-subj", "/",
         "-reqexts", "SAN",
         "-config", ssl_conf],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    out, err = proc.communicate()
    if proc.returncode != 0:
        raise IOError("OpenSSL Error: {0}".format(err))

    with open("%s/%s.csr" % (crt_dir, name), "wb") as file:
        file.write(out)


def create_crt(name):
    if exist_key(name):
        shutil.copyfile(
            "%s/%s.crt" % (crt_dir, name),
            "%s/%s_%s.crt" % (crt_bak_dir,
                              datetime.now().strftime("%Y%m%d_%H%M%S"),
                              name))

    signed_crt = acme_tiny.get_crt("config/account.key",
                            "%s/%s.csr" % (crt_dir, name),
                            acme_challenge_dir,
                            logger,
                            acme_ca)

    if chained_crt == "true":
        signed_crt += urlopen(acme_intermediate).read()

    with open("%s/%s.crt" % (crt_dir, name), "w") as file:
        file.write(signed_crt)


def notify_container():
    if not container_notify:
        return

    logger.info("Send SIGHUP to " + container_notify)

    proc = subprocess.Popen(
        ["docker", "kill",
         "-s", "SIGHUP",
         container_notify],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    out, err = proc.communicate()
    if proc.returncode != 0:
        raise IOError("Docker Error: {0}".format(err))


os.makedirs(crt_dir, exist_ok=True)
os.makedirs(crt_bak_dir, exist_ok=True)
os.makedirs(tmp_dir, exist_ok=True)
os.makedirs(acme_challenge_dir, exist_ok=True)

config = configparser.ConfigParser()
config.read("config/config.ini")

if not os.path.isfile("config/account.key"):
    proc = subprocess.Popen(
        ["openssl", "genrsa", "4096"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    out, err = proc.communicate()
    if proc.returncode != 0:
        raise IOError("OpenSSL Error: {0}".format(err))

    with open("config/account.key", "wb") as file:
        file.write(out)

logger.info("Docker ACME started")
while True:
    changed = False
    for crt in config.sections():
        if check_crt(crt):
            logger.info("[%s] Certificate valid -> Skipping" % crt)
            continue

        # create key if not exist
        if not exist_key(crt):
            logger.info("[%s] Generate RSA private key" % crt)
            create_key(crt)

        # generate CSR
        logger.info("[%s] Generate CSR" % crt)
        create_csr(crt, config[crt]["domains"].split(","))

        # get certificate
        create_crt(crt)
        changed = True

    if changed:
        notify_container()

    # run every hour
    time.sleep(3600)
