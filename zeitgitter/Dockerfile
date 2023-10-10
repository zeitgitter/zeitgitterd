# For development docker builds, install from local package instead from PyPI.
# For this, `##DEVONLY##` strings at the start of the line will be removed for
# the dev build Dockerfile, whereas lines ending in `##PRODONLY##` will be
# deleted.
FROM debian:bookworm-slim

# The next line is hardcoded in Makefile as PRODONLY,
# as ARG does not support comments
ARG VERSIONMATCH=

# gnupg1/gpg1 steps are for interfacing with the PGP Timestamping Service only.
RUN apt update && \
    apt install -y --no-install-recommends gnupg gnupg1 libgit2-dev python3-pygit2 \
        python3-pip python3-setuptools python3-wheel git wget dpkg ssh-client && \
    apt clean && \
    rm -rf /var/lib/apt/lists

# Verify that OS packages, Python version and Python package can interoperate
# (apt libgit2+python3-pygit2 with Python interpreter, pip pygit2)
RUN python3 -c "import pygit2"

# Provide `--build-arg VERSIONMATCH===0.9.4` or similar to ask
# for a specific version (instead of `==`, also other comparison
# operators could be used.
RUN pip3 install --break-system-packages zeitgitterd${VERSIONMATCH} ##PRODONLY##
##DEVONLY## COPY zeitgitterd-*.whl /root/
##DEVONLY## RUN pip3 install --break-system-packages /root/zeitgitterd-*.whl

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
