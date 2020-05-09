FROM python:3.8
# gnupg1/gpg1 steps are for interfacing with the PGP Timestamping Service only
RUN apt update && apt upgrade -y && apt install -y gnupg1 && rm -rf /var/lib/apt/lists/
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
