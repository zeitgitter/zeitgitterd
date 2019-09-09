FROM debian:stable
RUN apt update
RUN apt install -y git python3-pygit2 python3-gnupg python3-configargparse python3-requests python3-pip
RUN pip3 install git-timestamp
WORKDIR /tmp
RUN git clone https://gitlab.com/zeitgitter/zeitgitterd.git
WORKDIR /tmp/zeitgitterd
RUN git checkout docker-test
RUN make install-docker
WORKDIR /
COPY stamper.asc /tmp/
RUN gpg1 --import /tmp/stamper.asc
RUN rm -rf /tmp/zeitgitterd /tmp/stamper.asc
RUN mkdir /zgdata
EXPOSE 8080
ENTRYPOINT /dockgitter.sh --listen-address 0.0.0.0
