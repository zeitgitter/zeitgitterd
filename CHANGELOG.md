# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

# 1.1.0+ - [Unreleased]

## Added

- Support for `favicon.ico` (served as `image/png`, as that is the most common type today)

## Fixed

- The fix for malformed request made things work. Better fix.

## Changed

# 1.1.0 - 2021-11-11

## Added

- `robots.txt` and `sitemap.xml` (and the ability to serve TXT and XML files)

## Fixed

- Be more defensive against malformed requests

## Changed

- Slightly changed explanatory web text and refreshed its appearance
- All text files now go through `ZEITGITTER_*` substitution

# 1.0.6 - 2021-11-04

## Added

## Fixed

## Changed

- Upgraded docker image to debian:bullseye-slim

# 1.0.5 - 2021-03-06

## Added

- Include an optional TLS termination proxy as part of the `docker-compose` setup (requires setting
  `ZEITGITTER_DOMAIN` in addition to `ZEITGITTER_OWN_URL` in `server.env`)

## Fixed

- Fixed Dockerfile for ARM64

## Changed

- Shrank docker image
- No changes to source or PyPI versions (except the version number); only Docker image is affected
  by the modifications leading up to v1.0.5

# 1.0.4 - 2021-03-05

## Added

- `--upstream-sleep` allows to sleep between upstream timestamps, e.g. to ensure a consistent
  ordering of cross-timestamping events for each commit.
- Time intervals (such as "5m3.5s") may skip the seconds indication, `s`. So `--upstream-sleep=0` is
  also valid.

## Fixed

## Changed

- Version numbers of non-tagged versions now end in `.postX`, where `X` is the number of commits
  since the tag (unless overridden by `FORCE_VERSION` environment variable).
- Docker image slightly smaller

# 1.0.3 - 2020-12-07

## Added

- More documentation: (especially in `doc/Docker.md`).
  - Setup and retirement of a timestamping server
  - Document choice/change of PGP key ID (and name)
- On restart, tries to resume waiting for a mail response from PGP Digital Timestamping Service (was
  added some versions ago, but never documented)
- New `tools/zeitgitter-repo-health.sh` allows to probe whether the repo has seen the expected
  updates. Optionally, skip fetches or test for specific files to have been modified and return a
  specific exit code. This is independent from the Docker health checks and can be run on a
  monitoring machine.
- Timespans may also indicate the number of weeks now (e.g., "1w 2d 8h 40m 3.5s")
- Simplified using multiple cross-timestampers:
  - Add support to push all branches using `--push_branch=*`, saving the need to list/update them
    all (see also _Changes_ below)
  - `--upstream-timestamp` no longer needs a branch name, if `git timestamp` will determine it
    correctly. This leads to much shorter and more maintainable lists of cross-timestamping servers
    (e.g., `gitta diversity some.other.server`).

## Fixed

- Code typo on failed key creation
- Docker health check failed due to missing `wget` package
- Docker health check now supports multiple cross-timestamping targets
- Tests test against new commit string (and, therefore, signatures) now

## Changed

- Docker image is now based on `debian:buster-slim`. As the same number of packages (171) has to be
  added on top of it, starting with the smaller image is preferable. (See
  [#0.9.6---2020-08-13](v0.9.6 below) for why not using one of the `python` base images.)
- Default for `--push-branch` is now `*`, meaning `--all` (which cannot be expressed in the config
  file)
- `ZEITGITTER_FAKE_TIME` (needed only for tests) is removed from the environment of `git timestamp`
  clients that connect to cross-timestamping servers specified as server name only (as opposed to
  `branch=server` tuples) to allow both testing against our local timeserver (which does not use
  wall clock to achieve reproducible signatures) and against real-world timeservers obeying wall
  clock.

# 1.0.2 - 2020-08-15

## Added

- Allow testing docker images without having to publish to PyPI and DockerHub. This will allow
  better testing in the future before releasing. (If you wonder why this Changelog does not say
  anything about v1.0.1, this is why.)

## Fixed

- Data loss can occur (and did in fact occur on `gitta.zeitgitter.net`) if `git` is not installed,
  due to `FileNotFoundError` signalling both harmless events (whether a file tested for presence
  exists) and important events (`git` cannot be executed, as it cannot be found). This resulted in
  destructive file operations being performed, as it was wrongly believed that the data was already
  recorded persistently in `git`. This has been fixed. :warning: Please refrain from using Docker
  image versions 1.0.0 or 0.9.6, and do update to 1.0.1 also for non-Docker instances, as they will
  fail more harmlessly (i.e., just lengthen the interval until `git` is present (again), resulting
  in precision loss from cross-timestamping, instead of with data loss).
- `git` included in Docker image
- Recovering from dangling repositories

## Changed

- A commit will be created after creating the timestamping repository and adding `pubkey.asc` to it,
  so that cross-timestamping can start then. Otherwise, cross-timestamping would result in error
  messages until the first external timestamping request arrives.

# 1.0.0 - 2020-08-13

## Added

## Fixed

## Changed

- Releasing 0.9.6 as 1.0.0

# 0.9.6 - 2020-08-13

## Added

## Fixed

## Changed

- Commit/tag message now starts with :watch:; this is not only useful for projects following
  [gitmoji](https://gitmoji.carloscuesta.me/) style, but also for visually distinguishing timestamps
  from regular commits/tags
- Base Docker image on `debian:buster`, as
  [`python:*` is on purpose not meant to be used with local system packages](https://github.com/docker-library/python/issues/482).
  However, `pygit2` is impractical to install without relying on system packages.

# 0.9.5 - 2020-05-13

## Added

- README for the Docker file
- Support for ARM and ARM64 docker images
- Documented support for multiple debug classes

## Fixed

- Web files again included in wheel
- `async_email_timestamp()` now really waits in a new thread for the mail reply

## Changed

- Reduced logging for PGP Timestamping Server mail handling
- Updated gnupg config documentation
- Newer GnuPG versions seem to ignore the symlink trick, now copying for real
- Restarting the server tries to resume a pending `async_email_timestamp()` waiting for the reply
  mail

# 0.9.4 - 2020-05-09

## Added

- Support for data in binary packages

## Fixed

## Changed

- Default port is now 15177 (as has been for systemd); tests use 15178
- Default debug level is now INFO. Numeric debug levels are now deprecated.
- Default commit interval has been set to 1h
- Simplified Docker setup/usage. Now created from pypi images.
- Docker is now the recommended usage platform.

# 0.9.3 - 2020-05-08

## Added

- Allow dots in tag names, as long as they are not next to each other (i.e., `..` is not allowed)
- Added support for [PGP Digital Timestamping Service](http://www.itconsult.co.uk/stamper.htm) and
  improved documentation
- Timestamp our commit id as well with PGP Timestamper
- Configuration now easier: Just look for `EASYCONFIG` in `zeitgitter.conf`
- Added support for (semi-)automatic configuration
- Configuration through environment variables
- Support Docker
- More detailed debug support (see `--debug-level`)
- Minimal support for HTTP `HEAD` requests
- Can use IMAP servers without `IDLE` support (are there still any out there?)
- Work around a bug in some(?) Dovecot mail servers which cannot match the last character of a mail
  domain. I.e., `mailer@itconsult.co.uk` does not match the `From: Stamper <mailer@itconsult.co.uk>`
  header in IMAP SEARCH, but `mailer@itconsult.co.u` (note the missing `k`!) does match the header.
  This can be turned off via `--no-dovecot-bug-workaround`.

## Fixed

- Correctly handles IMAP `IDLE` responses other than `EXISTS` (especially Dovecot's
  `* OK still here`)
- End line in stamper mails may now also be in last line.
- Not receiving a stamper mail in time does no longer raise an exception

## Changed

- Split into client (git-timestamp) and server (zeitgitterd).
- Calculate a default for `--gnupg-home` to allow `--number-of-gpg-agents` > 1
- Commit log message includes timestamp as well to improve readability for `git blame` etc.
- Log message timestamps (including "Found uncommitted data") now say "UTC"
- Renamed all PGP Digital Timestamper related parameters to a common `--stamper-` prefix (the old
  names are still accepted, but deprecated)
- Mail tests now include a (local) configuration file for the site secrets.
- Maintainer affiliation
- Release on PyPI

# 0.9.2 - 2019-05-10

## Added

- `make apt` installs dependencies on systems supporting `apt`

### Client

- Distributable via PyPI
- Added Python 2.x compatibility; tested with 2.7
- Automatically derive default timestamp branch name from servername (first component not named
  'igitt') followd by '-timestamps'.
- Better error message when wrong `gnupg` module has been installed

## Fixed

### Client

- Fetch GnuPG key again if missing from keyring. This fixes unexpected behavior when running as sudo
  vs. natively as root.
- Work around a bug in older GnuPG installs (create `pubring.kbx` if it does not yet exist before
  attempting `scan_keys()`).

## Changed

- Higher-level README

### Client

- Is now implemented as a package (`make install` still installs a flat file though, for simplicity)

# 0.9.1 - 2019-04-19

## Added

### Client

- `--server` can be set in git config
- Prevent actual duplicate entries created by `git timestamp --branch`
- Documented that `git timestamp --help` does not work and to use `-h`, as `--help` is swallowed by
  `git` and not forwarded to `git-timestamp`.
- Client system tests (require Internet connectivity)

### Server

- Ability to run multiple GnuPG processes (including gpg-agents) in parallel
- Handle missing `--push-repository` (again)

## Fixed

- Made tests compatible with older GnuPG versions

## Changed

### Client

- Made some error messages more consistent
- `--tag` overrides `--branch`. This allows to store a default branch in `git config`, yet timestamp
  a tag when necessary.

# 0.9.0 - 2019-04-04

Initial public release
