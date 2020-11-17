#!/bin/sh -e
# Docker healthcheck

# Web server responsive?
if ! wget --quiet -O /dev/null 'http://localhost:15177/'
then
  echo "Cannot retrieve web page"
  exit 1
fi
if ! wget --quiet -O /dev/null 'http://localhost:15177/?request=get-public-key-v1'
then
  echo "Cannot retrieve public key"
  exit 1
fi

# Have there been commits at all?
if [ ! -f /persistent-data/repo/.git/refs/heads/master ]
then
  exit 0
fi

# At least one commit to the master branch and each timestamp branch every ~hour
cd /persistent-data/repo/.git/refs/heads
if [ x`find . -name master -mmin -65 -print | wc -l` = x0 ]
then
  echo "No master commit in past ~hour"
  exit 1
fi

for i in *-timestamps
do
  if [ -e "$i" -a x`find . -name $i -mmin -65 -print | wc -l` = x0 ]
  then
    echo "No $i in past ~hour"
    exit 1
  fi
done

# PGP Timestamper update?
cd /persistent-data/repo
if [ -f hashes.stamp ]
then
  if [ x`find . -name hashes.stamp -mmin -65 -print | wc -l` = x0 ]
  then
    echo "No PGP timestamper query in the past ~hour"
    exit 1
  fi
  if [ x`find . -name hashes.asc -mmin -90 -print | wc -l` = x0 ]
  then
    echo "No PGP timestamper reply in the past 1.5 hours"
    exit 1
  fi
fi
exit 0
