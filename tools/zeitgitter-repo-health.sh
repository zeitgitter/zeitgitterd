#!/bin/bash
# Check for healthiness of the repository by checking for updates of a branch
# in general or of a specific file in the branch.
#
# Usage:
#   check-repo-healthy.sh <repo-dir> <repo-url> <branch> <max-age> [file]
# - repo-dir: The directory to check the repository out in.
# - repo-url: The URL to pull from.
#             Will only be used if <repo-dir> does not yet exist.
#             If it is specified as "-", will prevent clone/fetch operation,
#             assuming that the repo has been made current by another means
#             or an immediately preceding run of `check-repo-health.sh`.
# - branch:   The branch to check for recent commits.
#             Use branch names such as "origin/master" instead of "master".
# - max-age:  The maximum age of the most recent commit in <branch>.
#             Use "5 minutes ago" etc. (requires quotes)
# - file:     If used, will check whether the specified file has been updated.
#             MAY NOT CONTAIN SPACES or other shell metacharacters!
#
# Make sure the current user has read access to the repository. This means that
# - the remote repository needs to be public,
# - there is a valid ssh key for that repository in ~/.ssh, or
# - (not recommended) the credentials are part of the URL.
#
# Exit code (compatible with [Vigil](https://github.com/valeriansaliou/vigil#how-can-i-create-script-probes)):
# - 0: Healthy
# - 1: Sick (not used right now)
# - >=2: Dead
#
# Example:
#   ./check-repo-healthy.sh /tmp/github-gitta \
#	https://github.com/zeitgitter/gitta-timestamps.git \
#	origin/master \
#	"1 hour ago"
#   # No need to fetch again, as the repo was just updated
#   ./check-repo-healthy.sh /tmp/github-gitta \
#	- \
#	origin/diversity-timestamps \
#	"1 hour ago"
#   # Check whether the PGP Digitial Timestamp was updated
#   ./check-repo-healthy.sh /tmp/github-gitta \
#	- \
#	origin/diversity-timestamps \
#	"1 hour ago" \
#	hashes.asc

mkdir -p "$1"
cd "$1" || exit 2

# Possibly pull from the repository (clone or fetch)
if [[ "x$2" != "x-" ]]; then
  repo="$2"
  if [[ -r ".git" ]]; then
    git fetch -q || exit 2
  else
    git clone -q "$2" . || exit 2
  fi
else
  repo="$1"
fi

# Check whether there have been updates in the specified time window
if [[ $(git log --since "$4" "$3" $5 | wc -l) -ne 0 ]]; then
  # At least one log entry in the time frame
  exit 0
else
  echo "No commit to $repo $3 since $4" >&2
  exit 2
fi
