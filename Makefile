# Installation
PREFIX		= /usr/local
SBINDIR		= ${PREFIX}/sbin
LIBDIR		= ${PREFIX}/lib
PYMODDIR	= ${LIBDIR}/python/zeitgitter
ZEITGITTERHOME	= /var/lib/zeitgitter
WEBDIR		= ${ZEITGITTERHOME}/web
REPODIR		= ${ZEITGITTERHOME}/repo
ETCDIR		= /etc
SYSTEMDDIR	= ${ETCDIR}/systemd/system

# Color
ACT		= \033[7;34m
INFO		= \033[7;32m
NORM		= \033[0m

# Tests
DAEMONTEMP	:= $(shell mktemp -d)
KEYID		= 353DFEC512FA47C7
KEYHOME		= ${CURDIR}/zeitgitter/tests/gnupg/
DAEMONPARAMS	= \
	--keyid ${KEYID} \
	--own-url https://hagrid.snakeoil \
	--owner '?' --contact '?' --country '?' \
	--gnupg-home ${KEYHOME} \
	--commit-interval 1m \
	--commit-offset 30s \
	--repository ${DAEMONTEMP} \
	--upstream-timestamp stupid-timestamps=http://127.0.0.1:8080

# For `gpg` and `git commit -S`
export GNUPGHOME= ${KEYHOME}
# For tests
export DAEMONREPO=${DAEMONTEMP}

all:
	@echo 'Nothing needs to be done for "all"; use "install", "apt", or "test" instead'

install:
	if ! groups zeitgitter > /dev/null 2>&1; then \
		adduser --system --disabled-password --disabled-login --group --home ${ZEITGITTERHOME} --gecos "Independent GIT Timestamper" zeitgitter; \
	fi
	mkdir -p ${PYMODDIR}
	install -t ${SBINDIR} zeitgitterd.py
	install -t ${PYMODDIR} zeitgitter/*.py
	py3compile ${PYMODDIR}/*.py
	if [ ! -d ${WEBDIR} ]; then \
		install -o zeitgitter -d ${WEBDIR}; \
		install -o zeitgitter -m 644 -t ${WEBDIR} web/*; \
	else \
		echo "${INFO}* Not updating ${WEBDIR}${NORM}"; \
	fi
	if grep -q _ZEITGITTER_ ${WEBDIR}/*; then echo "${ACT}* Please adapt ${WEBDIR} to your needs${NORM}"; fi
	install -d -o zeitgitter ${REPODIR}
# /etc/zeitgitterd.conf contains passwords, so restrict access
	if [ ! -f ${ETCDIR}/zeitgitterd.conf ]; then \
		install -o zeitgitter -m 600 sample-zeitgitterd.conf ${ETCDIR}/zeitgitterd.conf; \
		echo "${ACT}* Customize ${ETCDIR}/zeitgitterd.conf${NORM}"; \
	else \
		echo "${INFO}* Not updating ${ETCDIR}/zeitgitterd.conf${NORM}"; \
	fi
	if [ ! -d ${REPODIR}/.git ]; then \
		sudo -Hu zeitgitter git init ${REPODIR}; \
		echo "${INFO}* Initialized repo${NORM}"; \
	fi
	if [ ! -s ${REPODIR}/pubkey.asc ]; then \
		if sudo -Hu zeitgitter wget --no-verbose -O ${REPODIR}/pubkey.asc 'http://127.0.0.1:15177/?request=get-public-key-v1'; then \
			(cd ${REPODIR} && sudo -Hu zeitgitter git add pubkey.asc); \
			echo "${INFO}* Added public key${NORM}"; \
			if sudo -Hu zeitgitter gpg --list-packets ${REPODIR}/pubkey.asc | \
				sudo -Hu zeitgitter tools/set-git-config-from-pubkey.py ${REPODIR}; then \
				echo "${INFO}* Set git repo user identity from pubkey.asc${NORM}"; \
			fi; \
		else \
			echo "${ACT}* Cannot obtain public key${NORM}"; \
			rm ${REPODIR}/pubkey.asc; \
		fi; \
	fi
	sudo -Hu zeitgitter touch ${REPODIR}/hashes.work

apt:
	apt install git python3-pygit2 python3-gnupg python3-configargparse python3-nose


test tests:	unit-tests system-tests

unit-tests:
	nosetests3

system-tests: prepare-tmp-git kill-daemon
## Start daemon
	ZEITGITTER_FAKE_TIME=1551155115 ./zeitgitterd.py ${DAEMONPARAMS} &
## Wait for daemon to be ready
	sleep 0.5
## Run tests with daemon
	@d=`mktemp -d`; for i in tests/*; do echo; echo ===== $$i $$d; $$i $$d || exit 1; done; echo ===== Cleanup; ${RM} -r $$d
## Cleanup
	${RM} -r ${DAEMONTEMP}
	killall zeitgitterd.py

kill-daemon:
	-killall zeitgitterd.py 2>/dev/null; exit 0

prepare-tmp-git:
	git init ${DAEMONTEMP}
	chmod 700 ${KEYHOME}
# Avoid "gpg: WARNING: unsafe permissions on homedir"
	gpg --export -a ${KEYID} > ${DAEMONTEMP}/pubkey.asc
	cd ${DAEMONTEMP} && git add pubkey.asc
	cd ${DAEMONTEMP} && git commit -S${KEYID} -m "Start timestamping"

run-test-daemon: prepare-tmp-git kill-daemon
	./zeitgitterd.py ${DAEMONPARAMS}
run-test-daemon-fake-time: prepare-tmp-git kill-daemon
	ZEITGITTER_FAKE_TIME=1551155115 ./zeitgitterd.py ${DAEMONPARAMS}
