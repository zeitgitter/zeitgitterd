#!/bin/sh -e
# Docker healthcheck

# Have there been commits at all?
if [ ! -f /blockchain/.git/refs/heads/master ]; then
  exit 0
fi

# At least one commit to the master branch and each timestamp branch every ~hour
cd /blockchain/.git/refs/heads
if [ x`find . -name master -mmin -65 -print | wc -l` = x0 ]; then
  echo "No master commit in past ~hour" >&2
  exit 1
fi

for i in `git branch -list '*-timestamps'`; do
  if [ x`git log "$i@{65 minutes ago}..$i" | wc -l` = x0 ]; then
    echo "No $i in past ~hour" >&2
    exit 1
  fi
done

# PGP Timestamper update?
cd /blockchain
if [ -f pgp-timestamp.asc ]
then
  if [ x`find . -name hashes.asc -mmin -90 -print | wc -l` = x0 ]
  then
    echo "No PGP timestamper reply in the past 1.5 hours" >&2
    exit 1
  fi
fi
exit 0
