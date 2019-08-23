#!/bin/sh
# If config file has not yet been set up, create it and exit with message.
# Otherwise, launch daemon
if [ ! -f /var/lib/zeitgitter/zeitgitter.conf ]; then
	cp /etc/zeitgitter.conf /var/lib/zeitgitter/
	echo "*** Please configure /var/lib/zeitgitter.conf first."
	echo "*** For a first run, edit everything kmarked REQUIRED."
	exit 1
fi
exec /usr/local/sbin/zeitgitterd.py
