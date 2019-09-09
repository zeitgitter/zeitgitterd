PERSISTENT_DIR	= /var/lib/zeitgitter

all:	docker

update:
	wget --quiet -O - http://www.itconsult.co.uk/stamper/stampinf.htm | \
	  sed -n -e '/-----BEGIN PGP PUBLIC KEY BLOCK-----/,/-----END PGP PUBLIC KEY BLOCK-----/p' > stamper.asc

docker:
	docker build . -t zeitgitter
	docker run -v ${PERSISTENT_DIR}:/zgdata zeitgitter

daemon:
	docker run -d -v ${PERSISTENT_DIR}:/zgdata zeitgitter
