# This fails when cross-compiling to ARM with a libgit version mismatch
# `docker buildx build --pull --load --platform linux/arm64 .`
FROM python:3.8
RUN apt update && apt install -y libgit2-dev
RUN pip3 install pygit2
RUN python3 -c "import pygit2"
