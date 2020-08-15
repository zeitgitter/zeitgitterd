#!/bin/bash -e
# Docker runner

# This needs to go *into* the volume, which is probably mapped by
# docker-compose. So at start only… (as opposed to image creation)
if [[ ! -d /persistent-data/.gnupg/ ]]; then
  gpg1 --pgp2 --import /root/stamper.asc
fi
if [[ ! -f /persistent-data/zeitgitter.conf ]]; then
  cp --verbose /root/sample.conf /persistent-data/
fi
exec zeitgitterd "$@"
