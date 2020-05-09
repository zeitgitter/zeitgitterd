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
KEYHOME		= ${DAEMONTEMP}/gnupg/
KEYHOMEIN	= ${CURDIR}/zeitgitter/tests/gnupg/
DAEMONPARAMS	= \
	--keyid ${KEYID} \
	--own-url https://hagrid.snakeoil \
	--owner '?' --contact '?' --country '?' \
	--gnupg-home ${KEYHOME} \
	--commit-interval 1m \
	--commit-offset 30s \
	--repository ${DAEMONTEMP} \
  --listen-port 15178 \
	--upstream-timestamp stupid-timestamps=http://127.0.0.1:15178

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

pypi:
	${RM} -f dist/*
	./setup.py sdist bdist_wheel
	twine upload dist/*

# ----- Testing

test tests:	unit-tests system-tests

unit-tests:
	nosetests3

system-tests: prepare-tmp-git kill-daemon
## Start daemon
	ZEITGITTER_FAKE_TIME=1551155115 ./zeitgitterd.py ${DAEMONPARAMS} &
## Wait for daemon to be ready
	sleep 0.5
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
