FROM debian:stable
RUN apt update
RUN apt install -y git python3-pygit2 python3-gnupg python3-configargparse python3-requests python3-pip
RUN pip3 install git-timestamp
WORKDIR /tmp
ENV GUGUS=dada
RUN git clone  https://gitlab.com/zeitgitter/zeitgitterd.git
WORKDIR /tmp/zeitgitterd
RUN git checkout docker-test
RUN make install-docker
RUN rm -rf /tmp/zeitgitterd
ENTRYPOINT /usr/local/sbin/zeitgitterd.py
