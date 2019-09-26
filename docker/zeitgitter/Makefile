PERSISTENT_DIR	= /var/lib/zeitgitter

all:	docker-build
docker: docker-build docker-run
docker-daemon: docker-build docker-run-daemon

update:
	wget --quiet -O - http://www.itconsult.co.uk/stamper/stampinf.htm | \
	  sed -n -e '/-----BEGIN PGP PUBLIC KEY BLOCK-----/,/-----END PGP PUBLIC KEY BLOCK-----/p' > stamper.asc

docker-build:
	docker build . -t zeitgitter

docker-run:
	docker run -v ${PERSISTENT_DIR}:/zgdata zeitgitter

docker-run-daemon:
	docker run -d -v ${PERSISTENT_DIR}:/zgdata zeitgitter
