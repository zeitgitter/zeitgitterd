FROM debian:buster
# gnupg1/gpg1 steps are for interfacing with the PGP Timestamping Service only
# python3-pygit2 explicit install is required for ARMv6 only
RUN apt update && apt install -y gnupg1 libgit2-dev python3-pygit2 python3-pip git && rm -rf /var/lib/apt/lists
# Verify that OS packages, Python version and Python package can interoperate
# (apt libgit2+python3-pygit2 with Python interpreter, pip pygit2)
RUN python3 -c "import pygit2"
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
