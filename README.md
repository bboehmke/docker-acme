Docker ACME
===========

Docker image based on [acme-tiny](https://github.com/diafygi/acme-tiny).


Usage
-----

Create a `config.ini` in a directory (eg `/srv/acme_config/`) with content like:
```ini
[cert_1]
domains=a.domain.de,b.domain.de,domain.com
[cert_2]
domains=a.domain.de,b.domain.de,domain.com
```

Note: if no account.key exist in `/srv/acme_config/` a new one is created.


Start the acme client:
```
docker run --rm \
    -v /srv/acme_config/:/acme/config/ \
    -v /srv/nginx/crt/:/acme/crt/ \
    -v /srv/nginx/www/.well-known/acme-challenge/:/acme/acme_challenge/ \
    bboehmke/docker-acme
```

This will result in two certificates in `/srv/nginx/crt/` with the name
`cert_1.crt` and `cert_2.crt`.

If a different container should be triggered on certificate change start the client like:
```
docker run --rm \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /srv/acme_config/:/acme/config/ \
    -v /srv/nginx/crt/:/acme/crt/ \
    -v /srv/nginx/www/.well-known/acme-challenge/:/acme/acme_challenge/ \
    -e CONTAINER_NOTIFY=nginx \
    bboehmke/docker-acme
```

Available Configuration Parameters
----------------------------------

- **ACME_CA**: URL to ACME CA (Default: `https://acme-v01.api.letsencrypt.org`)
- **ACME_INTERMEDIATE**: Path to intermediate certificate (Default: `https://letsencrypt.org/certs/lets-encrypt-x3-cross-signed.pem`)
- **CHAINED_CRT**: If true add intermediate certificate to *.crt (Default: true)
- **CONTAINER_NOTIFY**: Name of container for notification
- **CRT_MAX_AGE**: Max age of certificate before renew in days (Default: 30)
