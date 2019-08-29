#!/bin/sh
# If config file has not yet been set up, create it and exit with message.
# Otherwise, launch daemon
if [ ! -f /root/zeitgitter.conf ]; then
	cp /etc/zeitgitter.conf /root/
	echo
	echo "*** Please configure /var/lib/zeitgitter/zeitgitter.conf first."
	echo "*** For a first run, edit everything marked EASYCONFIG."
	echo
	exit 1
fi
exec /zeitgitterd.py -c /root/zeitgitter.conf
