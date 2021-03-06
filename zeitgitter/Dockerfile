FROM debian:buster-slim

# gnupg1/gpg1 steps are for interfacing with the PGP Timestamping Service only.
# Explicit python3-pygit2 install is required for ARMv6 only.
# Explicit dpkg install seens to be required for arm64 only.
RUN apt update && \
    apt install -y --no-install-recommends gnupg gnupg1 libgit2-dev python3-pygit2 \
	python3-pip python3-setuptools python3-wheel git wget dpkg ssh-client && \
    apt clean && \
    rm -rf /var/lib/apt/lists

# Verify that OS packages, Python version and Python package can interoperate
# (apt libgit2+python3-pygit2 with Python interpreter, pip pygit2)
RUN python3 -c "import pygit2"

# For development docker builds, install from local package instead from PyPI.
# For this, `##DEVONLY##` strings at the start of the line will be removed for
# the dev # build Dockerfile, whereas lines ending in `##PRODONLY##` will be
# deleted.
RUN pip3 install zeitgitterd ##PRODONLY##
##DEVONLY## COPY zeitgitterd-*.whl /root/
##DEVONLY## RUN pip3 install /root/zeitgitterd-*.whl

# Ensure SSH keys also survive an update
# `usermod --home /persistent-data root` refuses, as there are running procs
RUN sed 's,:/root:,:/persistent-data:,' < /etc/passwd > /etc/passwd+ && \
    mv /etc/passwd+ /etc/passwd

# Store outside of the volume (as it will most likely be mounted over) and copy
# only at first start
COPY stamper.asc sample.conf /root/

COPY health.sh run-zeitgitterd.sh /

# Ensure data is persistent from here as much as possible.
# Nevertheless, it is recommended to override this to be named volume, e.g.
# using `docker-compose`.
# Therefore, do not populate this directory yet, but only in `run-zeitgitter.sh`.
VOLUME /persistent-data

# Runtime settings
EXPOSE 15177
CMD ["/run-zeitgitterd.sh", "--listen-address", "0.0.0.0"]
HEALTHCHECK --timeout=3s CMD ["/health.sh"]
