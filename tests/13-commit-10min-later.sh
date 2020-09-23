#!/bin/sh
# Do not run normally (long delay for tests; cannot be run together with 12-*)
# But do (for full test) run *also* with 12-* disabled
if [ -f a.txt ]; then
  echo "$0: Cannot run after 12-*, skipping"
  exit 0
fi

d=$1
shift
for i in 0 1 2 3 4 5 6 7 8 9; do
  for j in 0 1 2 3 4 5 6 7 8 9; do
    sleep 6
    if [ -d $d/.git ]; then
      echo "$0: Forced commit found, great"
      exit 0
    fi
  done
done

echo "$0: Forced commit missing"
exit 1
