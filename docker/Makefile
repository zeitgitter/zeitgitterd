PERSISTENT_DIR	= /var/lib/zeitgitter

all:	docker

docker:
	docker build . -t zeitgitter
	docker run -v ${PERSISTENT_DIR}:/root zeitgitter

daemon:
	docker run -d -v ${PERSISTENT_DIR}:/root zeitgitter
