# `autoblockchainify` — Turn a directory into a git-based Blockchain

`git` is probably the oldest and most widely used Blockchain with the largest
user base and toolset, even though most people think of `git` as a source code
control system. To learn more, see
[GitBlockchainTimestamping.md](./GitBlockchainTimestamping.md).

## How does `autoblockchainify` work?

* Frequently (default: every 10 minutes), the directory tree is checked for
  changes. If there are changes, they are commited to `git` and timestamped
  using Zeitgitter.
* If no changes have been made in a larger period (default: 1 hour), a commit
  is forced and Zeitgitter-timestamped, as an immediate evidence of no changes.
* If at the time of commit the last timestamp using the mail-based *PGP Digital
  Timestamping Service* is older than this larger period (again: 1 hour by
  default) and the mail interface has been configured, a timestamp will be
  requested there.
* All timestamps requested from the Zeitgitter network will be regularily
  cross-timestamped within the Zeitgitter network and with the *PGP Digital
  Timestamping Service* as well as several other Blockchain-based timestamping
  services.

## What do I need to configure?

If you are happy with the default configuration, nothing. This default
configuration includes:
* A commit and Zeitgitter timestamp every 10 minutes, if there have been
  changes.
* A commit and Zeitgitter timestamp every hour, even if there have been no
  changes.

If you would like to change the above intervals, or if you would like the
following additional features, do change `autoblockchainify.conf` in the
working directory or set the `AUTOBLOCKCHAINIFY_*` environment variables:
* Additional, direct timestamping against the *PGP Digital Timestamping
  Service* by mail; or
* Pushing to a remote repository for backup and/or publication purposes on
  every change.
After changes to the configuration, you need to restart `autoblockchainify` (or
the Docker container) to have changes picked up.

If you would like to exclude files from inclusion in the `git` repository (and
therefore the Blockchain, the timestamps, and the remote repositories):
* Modify `.gitignore` in the working directory.

## How do I run it?

The preferred way is to run a Docker image using `docker-compose` and point the
`/blockchain` directory to the directory you want be automatically archived to
your Blockchain. See the files `docker-compose.yml` and `sample.env`.
