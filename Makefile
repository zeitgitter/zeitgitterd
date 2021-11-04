# Installation
PREFIX		= /usr/local
SBINDIR		= ${PREFIX}/sbin
LIBDIR		= ${PREFIX}/lib
PYMODDIR	= ${LIBDIR}/python/zeitgitter
ZEITGITTERHOME	= /var/lib/zeitgitter
WEBDIR		= ${PYMODDIR}/web
REPODIR		= ${ZEITGITTERHOME}/repo
ETCDIR		= /etc
SYSTEMDDIR	= ${ETCDIR}/systemd/system

OWNER		= zeitgitter

# Color
ACT		= \033[7;34m
INFO		= \033[7;32m
NORM		= \033[0m

# Tests
DAEMONTEMP	:= $(shell mktemp -d)
KEYID		= 353DFEC512FA47C7
KEYHOME		= ${DAEMONTEMP}/gnupg
KEYHOMEIN	= ${CURDIR}/zeitgitter/tests/gnupg/
DAEMONPARAMS	= \
	--number-of-gpg-agents=3 \
	--keyid ${KEYID} \
	--own-url https://hagrid.snakeoil \
	--owner '?' --contact '?' --country '?' \
	--gnupg-home ${KEYHOME} \
	--commit-interval 1m \
	--commit-offset 30s \
	--repository ${DAEMONTEMP} \
	--listen-port 15178 \
	--upstream-timestamp "stupid-timestamps=http://127.0.0.1:15178 gitta https://diversity.zeitgitter.net"

# For `gpg` and `git commit -S`
export GNUPGHOME= ${KEYHOME}
# For tests
export DAEMONREPO=${DAEMONTEMP}

all:
	@echo 'Nothing needs to be done for "all"; use "install", "apt", or "test" instead'

# ----- Installing

install: install-presetup install-files install-postsetup

install-presetup:
	if ! groups ${OWNER} > /dev/null 2>&1; then \
		adduser --system --disabled-password --disabled-login --group \
			--home ${ZEITGITTERHOME} \
			--gecos "Independent GIT Timestamper" ${OWNER}; \
	fi

install-files:
	mkdir -p ${PYMODDIR}
	install -t ${SBINDIR} zeitgitterd.py
	install -t ${PYMODDIR} zeitgitter/*.py
	py3compile ${PYMODDIR}/*.py
	if [ ! -d ${WEBDIR} ]; then \
		install -o ${OWNER} -d ${WEBDIR}; \
		install -o ${OWNER} -m 644 -t ${WEBDIR} zeitgitter/web/*; \
	else \
		echo "${INFO}* Not updating ${WEBDIR}${NORM}"; \
	fi
	if grep -q _ZEITGITTER_ ${WEBDIR}/*; then echo "${ACT}* Please adapt ${WEBDIR} to your needs${NORM}"; fi
	install -d -o ${OWNER} ${REPODIR}
# /etc/zeitgitter.conf contains passwords, so restrict access
	if [ ! -f ${ETCDIR}/zeitgitter.conf ]; then \
		install -o ${OWNER} -m 600 zeitgitter/sample.conf ${ETCDIR}/zeitgitter.conf; \
		echo "${ACT}* Customize ${ETCDIR}/zeitgitter.conf${NORM}"; \
	else \
		echo "${INFO}* Not updating ${ETCDIR}/zeitgitter.conf${NORM}"; \
	fi

install-postsetup:
	if [ ! -f ${SYSTEMDDIR}/zeitgitter.socket ]; then \
		install -m 644 -t ${SYSTEMDDIR} systemd/*; \
		systemctl daemon-reload; \
	else \
		echo "${INFO}* Not updating ${SYSTEMDDIR}/zeitgitter.*${NORM}"; \
	fi
	if [ ! -d ${ZEITGITTERHOME}/.gnupg ]; then \
		systemctl enable zeitgitter.service zeitgitter.socket; \
		echo "${ACT}* Please create an OpenPGP key, see ../doc/Cryptography.md${NORM}"; \
	else \
		systemctl restart zeitgitter.service; \
	fi


apt:
	apt install git python3-pygit2 python3-gnupg python3-configargparse python3-nose

python-package:
	${RM} -f dist/*
	./setup.py sdist bdist_wheel

pypi:	python-package
	twine upload dist/*

# ----- Testing

test tests:	unit-tests system-tests

unit-tests:
	nosetests3

system-tests: prepare-tmp-git kill-daemon
## Start daemon
	ZEITGITTER_FAKE_TIME=1551155115 ./zeitgitterd.py ${DAEMONPARAMS} &
## Wait for daemon to be ready
	sleep 1
## Run tests with daemon
	@d=`mktemp -d`; for i in tests/[0-9][0-9]-*; do echo; echo ===== $$i $$d; $$i $$d || exit 1; done; echo ===== Cleanup; ${RM} -r $$d
## Cleanup
	${RM} -r ${DAEMONTEMP}
	killall zeitgitterd.py

kill-daemon:
	-killall zeitgitterd.py 2>/dev/null; exit 0

prepare-tmp-git:
	git init ${DAEMONTEMP}
	cp -rp ${KEYHOMEIN} ${KEYHOME}
	chmod 700 ${KEYHOME}
# Avoid "gpg: WARNING: unsafe permissions on homedir"
	gpg --export -a ${KEYID} > ${DAEMONTEMP}/pubkey.asc
	cd ${DAEMONTEMP} && git add pubkey.asc
	cd ${DAEMONTEMP} && git commit -S${KEYID} -m "Start timestamping"

run-test-daemon: prepare-tmp-git kill-daemon
	./zeitgitterd.py ${DAEMONPARAMS}
run-test-daemon-fake-time: prepare-tmp-git kill-daemon
	ZEITGITTER_FAKE_TIME=1551155115 ./zeitgitterd.py ${DAEMONPARAMS}

##################################
#
# Create multi-platform docker image. If you have native systems around, using
# them will be much more efficient at build time. See e.g.
# https://netfuture.ch/2020/05/multi-arch-docker-image-easy/
BUILDXDETECT = ${HOME}/.docker/cli-plugins/docker-buildx
# Just one of the many files created
QEMUDETECT = /proc/sys/fs/binfmt_misc/qemu-m68k
# For version x.y.z, output "-t …:x.y -t …:x.y.z";
# for anything else, output nothing
BASETAG     = zeitgitter/zeitgitter
VERSIONTAGS = $(shell sed -n -e 's,^VERSION = .\(\([0-9].[0-9]\).[0-9]\).$$,-t ${BASETAG}:\1 -t ${BASETAG}:\2,p' zeitgitter/version.py)
# debian:bullseye-slim also supports
# linux/arm64/v8,linux/mips64le,linux/ppc64le,linux/s390x. If there is demand,
# I'll happily add them to the default build.
PLATFORMS  = linux/amd64,linux/386,linux/arm64,linux/arm/v7,linux/arm/v6

docker-multiarch: qemu buildx docker-multiarch-builder
	docker buildx build --builder docker-multiarch --pull --push \
		--platform ${PLATFORMS} ${VERSIONTAGS} \
		-t ${BASETAG}:latest zeitgitter

.PHONY: qemu buildx docker-multiarch-builder

qemu:	${QEMUDETECT}
${QEMUDETECT}:
	docker pull multiarch/qemu-user-static
	docker run --privileged multiarch/qemu-user-static --reset -p yes
	docker ps -a | sed -n 's, *multiarch/qemu-user-static.*,,p' \
	  | (xargs docker rm 2>&1 || \
	    echo "Cannot remove docker container on ZFS; retry after next reboot") \
	  | grep -v 'dataset is busy'

buildx: ${BUILDXDETECT}
${BUILDXDETECT}:
	@echo
# Output of `uname -m` is too different 
	@echo '*** `docker buildx` missing. Install binary for this machine architecture'
	@echo '*** from `https://github.com/docker/buildx/releases/latest`'
	@echo '*** to `~/.docker/cli-plugins/docker-buildx` and `chmod +x` it.'
	@echo
	@exit 1

docker-multiarch-builder: qemu buildx
	if ! docker buildx ls | grep -w docker-multiarch > /dev/null; then \
		docker buildx create --name docker-multiarch && \
		docker buildx inspect --builder docker-multiarch --bootstrap; \
	fi

# Create a docker image from the current tree
docker-dev:python-package
	${RM} -rf zeitgitter-dev
	mkdir -p zeitgitter-dev persistent-data-dev
	cp dist/zeitgitterd-*.whl zeitgitter-dev
	for i in Dockerfile sample.conf stamper.asc; do \
		(echo "### THIS FILE WAS AUTOGENERATED, CHANGES WILL BE LOST ###" && \
		sed -e 's/^##DEVONLY## *//' -e '/##PRODONLY##$$/d' \
		< zeitgitter/$$i ) > zeitgitter-dev/$$i; done
	for i in run-zeitgitterd.sh health.sh; do \
		(head -1 zeitgitter/$$i && \
		echo "### THIS FILE WAS AUTOGENERATED, CHANGES WILL BE LOST ###" && \
		sed -e 's/^##DEVONLY## *//' -e '/##PRODONLY##$$/d' \
		< zeitgitter/$$i ) > zeitgitter-dev/$$i && \
		chmod +x zeitgitter-dev/$$i; done
	sudo docker build zeitgitter-dev
