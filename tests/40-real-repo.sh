#!/bin/sh -e
# Needs to be run shortly after the full minute
# so that no rotation occurs during this test
#
export LANG=C # So we can match gpg output
if [ -r ../../git-timestamp/git-timestamp.py ]; then
  ts="`pwd`/../../git-timestamp/git-timestamp.py"
else
  ts="git-timestamp"
fi
repo=`mktemp -d`
cd $repo

git init
echo Hello world > hello.txt
git add hello.txt
git commit -m "First commit"

export IGITT_FAKE_TIME=1551155115
$ts --tag hello-timestamp --server http://localhost:8080
$ts --branch demo-timestamps --server http://localhost:8080
git tag -v hello-timestamp 2>&1 | grep 'gpg: Good signature'
git verify-commit demo-timestamps 2>&1 | grep 'gpg: Good signature'
git diff demo-timestamps

echo Second file > second.txt
git add second.txt
git commit -m "Second commit"
$ts --tag second-timestamp --server http://localhost:8080
$ts --branch demo-timestamps --server http://localhost:8080
git tag -v second-timestamp 2>&1 | grep 'gpg: Good signature'
git verify-commit demo-timestamps 2>&1 | grep 'gpg: Good signature'
git diff demo-timestamps
