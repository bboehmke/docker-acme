Docker ACME client
==================

Docker image based on [acme-tiny](https://github.com/diafygi/acme-tiny)
and [docker-gen](https://github.com/jwilder/docker-gen).

It is designed to use with [nginx-proxy](https://github.com/jwilder/nginx-proxy).


Usage
-----

### Basic settings

```
docker run --rm \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /srv/acme_config/:/acme/config/ \
    -v /srv/nginx/crt/:/acme/crt/ \
    -v /srv/nginx/www/.well-known/acme-challenge/:/acme/acme_challenge/ \
    bboehmke/docker-acme
```

Note: if no account.key exist in `/acme/config/` a new one is created.


### Predefined certificates

Use the environment variable `CERT_TEST=domainA,domainB` to create a 
certificate `test.crt` for all `domainA` and `domainB`.


### Automatic generated certificates

Add the environment variables `VIRTUAL_HOST`, `CERT_NAME` and `AUTO_CERT` to 
a docker container.

- **VIRTUAL_HOST**: List of domains
- **CERT_NAME**: Name of certificate
- **AUTO_CERT**: `true` to enable automatic generation


### Notify container

Set the variable `CONTAINER_NOTIFY` to a list of container names that should be 
notified if the certificates changed.


Available Configuration Parameters
----------------------------------

- **ACME_CA**: URL to ACME CA (Default: `https://acme-v01.api.letsencrypt.org`)
- **ACME_INTERMEDIATE**: Path to intermediate certificate (Default: `https://letsencrypt.org/certs/lets-encrypt-x3-cross-signed.pem`)
- **CHAINED_CRT**: If true add intermediate certificate to *.crt (Default: true)
- **CONTAINER_NOTIFY**: Names of container for notification (`,` separated for multiple container)
- **CRT_MAX_AGE**: Max age of certificate before renew in days (Default: 30)
