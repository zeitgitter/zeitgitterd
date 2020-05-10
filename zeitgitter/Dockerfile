FROM python:3.8
# gnupg1/gpg1 steps are for interfacing with the PGP Timestamping Service only
# python3-pygit2 explicit install is required for ARMv6 only
RUN apt update && apt upgrade -y && apt install -y gnupg1 libgit2-dev python3-pygit2 && rm -rf /var/lib/apt/lists
# Somehow, in the ARM docker builds, PYTHON does not know about the system install path
ENV PYTHONPATH=/usr/lib/python3/dist-packages
RUN pip3 install zeitgitterd
ENV HOME=/persistent-data
# Store outside of the volume
COPY stamper.asc sample.conf /root/
COPY health.sh run-zeitgitterd.sh /
# Ensure it is persistent, but overriding to a named volume e.g. with
# `docker-compose` is recommended. Therefore, do not populate it yet, but only
# in `run-zeitgitter.sh`.
VOLUME /persistent-data
EXPOSE 15177
ENTRYPOINT ["/run-zeitgitterd.sh", "--listen-address", "0.0.0.0"]
HEALTHCHECK --timeout=3s CMD ["/health.sh"]
