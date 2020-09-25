# Tests
DAEMONTEMP	:= $(shell mktemp -d)
DAEMONPARAMS	= \
	--commit-interval 1m \
	--commit-offset 30s \
	--force-after-intervals 10 \
	--repository ${DAEMONTEMP}
# To check that environment variables are also consulted
DAEMONENV	= AUTOBLOCKCHAINIFY_IDENTITY="Test User <test@user.example>"


all:
	@echo 'Nothing needs to be done for "all"'
	@echo 'Use "apt", "python-package", "docker-dev", or "test" instead'

# ----- Installing

apt:
	apt install git python3-pygit2 python3-gnupg python3-configargparse python3-nose

python-package wheel:
	${RM} -f dist/*
	./setup.py sdist bdist_wheel

pypi:	python-package
	twine upload dist/*

# ----- Testing

test tests:	unit-tests system-tests

unit-tests:
	nosetests3

system-tests: kill-daemon
## Start daemon; check whether environment variables are consulted
	${DAEMONENV} ./autoblockchainify.py ${DAEMONPARAMS} &
## Wait for daemon to be ready
	sleep 0.5
## Run tests with daemon
	@for i in tests/[0-9][0-9]-*; do echo; echo ===== $$i ${DAEMONTEMP}; $$i ${DAEMONTEMP} || exit 1; done
## Cleanup
#	${RM} -r ${DAEMONTEMP}
	killall autoblockchainify.py

kill-daemon:
	-killall autoblockchainify.py 2>/dev/null; exit 0

run-test-daemon: kill-daemon
	./autoblockchainify.py ${DAEMONPARAMS}

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
BASETAG     = zeitgitter/autoblockchainify
VERSIONTAGS = $(shell sed -n -e 's,^VERSION = .\(\([0-9].[0-9]\).[0-9]\).$$,-t ${BASETAG}:\1 -t ${BASETAG}:\2,p' autoblockchainify/version.py)
# debian:buster-slim also supports
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
	docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

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
	${RM} -rf autoblockchainify-dev
	mkdir -p autoblockchainify-dev blockchain-dev
	cp autoblockchainify/stamper.asc dist/autoblockchainify-*.whl autoblockchainify-dev
	for i in Dockerfile; do \
		(echo "### THIS FILE WAS AUTOGENERATED, CHANGES WILL BE LOST ###" && \
		sed -e 's/^##DEVONLY## *//' -e '/##PRODONLY##$$/d' \
		< autoblockchainify/$$i ) > autoblockchainify-dev/$$i; done
	for i in health.sh; do \
		(head -1 autoblockchainify/$$i && \
		echo "### THIS FILE WAS AUTOGENERATED, CHANGES WILL BE LOST ###" && \
		sed -e 's/^##DEVONLY## *//' -e '/##PRODONLY##$$/d' \
		< autoblockchainify/$$i ) > autoblockchainify-dev/$$i && \
		chmod +x autoblockchainify-dev/$$i; done
	sudo docker build autoblockchainify-dev
