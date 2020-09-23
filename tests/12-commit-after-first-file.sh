#!/bin/sh
d=$1
shift
cd $d
echo "Test 1" > $d/a.txt
for i in 0 1 2 3 4 5 6 7 8 9; do
  for j in 0 1 2 3 4 5; do
    sleep 6
    if [ `git log 2>/dev/null | wc -l` -ge 1 ]; then
      echo "$0: Automatically committed, great"
      exit 0
    fi
  done
done

echo "$0: Missing commit"
exit 1
