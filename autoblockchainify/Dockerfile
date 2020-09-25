FROM debian:buster-slim

# gnupg1/gpg1 steps are for interfacing with the PGP Timestamping Service only.
# Explicit python3-pygit2 install is required for ARMv6 only.
RUN apt update && \
    apt install -y gnupg1 libgit2-dev python3-pygit2 python3-pip git && \
    rm -rf /var/lib/apt/lists

# Verify that OS packages, Python version and Python package can interoperate
# (apt libgit2+python3-pygit2 with Python interpreter, pip pygit2)
RUN python3 -c "import pygit2"

# For development docker builds, install from local package instead from PyPI.
# For this, `##DEVONLY##` strings at the start of the line will be removed for
# the dev # build Dockerfile, whereas lines ending in `##PRODONLY##` will be
# deleted.
RUN pip3 install autoblockchainify ##PRODONLY##
##DEVONLY## COPY autoblockchainify-*.whl /root/
##DEVONLY## RUN pip3 install /root/autoblockchainify-*.whl

# Import (old-style) PGP key for PGP Digital Timestamping Service, so it is
# ready if anyone wants to use it
COPY stamper.asc /tmp
RUN gpg1 --pgp2 --import /tmp/stamper.asc
RUN rm /tmp/stamper.asc

COPY health.sh /

# Runtime settings
CMD ["autoblockchainify", "--repository", "/blockchain"]
HEALTHCHECK --timeout=3s CMD ["/health.sh"]
