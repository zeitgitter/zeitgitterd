#!/bin/sh
d=$1
shift
now=`date +"%Y-%m-%d %H:%M:%S"`
# No new commit in the first 8 minutes
for i in 0 1 2 3 4 5 6 7; do
  for j in 0 1 2 3 4 5 6 7 8 9; do
    sleep 6
    if [ x`git log "HEAD@{$now}..HEAD" | wc -l` != x0 ]; then
      echo "$0: Found a commit in the first 8 minutes" 2>&1
      exit 0
    fi
  done
done

# But now, we should get commit
for i in 8 9; do
  for j in 0 1 2 3 4 5 6 7 8 9; do
    sleep 6
    if [ x`git log "HEAD@{$now}..HEAD" | wc -l` = x0 ]; then
      exit 0
    fi
  done
done

echo "$0: Forced commit missing" 2>&1
exit 1
