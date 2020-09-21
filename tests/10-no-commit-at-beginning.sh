#!/bin/sh
d=$1
shift
cd $d
if git log >/dev/null 2>&1; then
  echo "$0: Unexpected git commit"
  exit 1
fi
