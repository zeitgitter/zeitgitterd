# `zeitgitter` — Independent `git` Timestamper

## Timestamping: Why?

Being able to provide evidence that **you had some piece of information at a
given time** and **it has not changed since** are important in many aspects of
personal, academic, or corporate life.

It can help provide evidence
- that you had some idea already at a given time,
- that you already had a piece of code, or
- that you knew about a document at a given time.

Timestamping does not assure *authorship* of the idea, code, or document. It
only provides evidence to the *existence* at a given point in time. Depending
on the context, authorship might be implied, at least weakly.

## `zeitgitter` for Timestamping

`zeitgitter` consists of two components:

1. A timestamping client, which can add a timestamp as a digital signature to
   an existing `git` repository. Existing `git` mechanisms can then be used
   to distribute these timestamps (stored in commits or tags) or keep them
   private.
2. A timestamping server, which supports timestamping `git` repositories and
   stores its history of commits timestamped in a `git` repository as well.
   Anybody can operate such a timestamping server, but using an independent
   timestamper provides strongest evidence, as collusion is less likely.
   - Publication of the timestamps history; as well as
   - getting cross-timestamps of other independent timestampers on your
     timestamp history
   both provide mechanisms to assure that timestamping has not been done
   retroactively ("backstamping").

The timestamping client is called `git timestamp` and allows to issue
timestamped, signed tags or commits.

To simplify deployment, we provide a free timestamping server at
[https://gitta.zeitgitter.ch](https://gitta.zeitgitter.ch). It is able to provide several
million timestamps per day. However, if you or your organization plan to issue
more than a hundred timestamps per day, please consider installing and using
your own timestamping server and have it being cross-timestamped with other
servers.

## Setting up your own timestamping server

Having your own timestamping server provides several benefits:

* The number of timestamps you request, their commit ID, as well as
  the times at which they are stamped, remain you business alone.
* You can request as many timestamps as you like.
* If you like, you can provide a service to the community as well,
  by timestamping other servers in turn. This strengthens the
  overall trust of these timestamps.

There are currently two options for installation:
* [Running a Zeitgitter timestamper in Docker](docker/README.md) (recommended; only requires setting four variables)
* [Traditional install on a Linux server](doc/Install.md) (more work)

## General Documentation

- [Timestamping: Why and how?](doc/Timestamping.md)
- [Protocol description](doc/Protocol.md)
- [Discussion of the use of (weak) cryptography](doc/Cryptography.md)

## Server Documentation

- [Docker server (recommended)](doc/Docker.md)
- [Native server (deprecated)](doc/Install.md)
- [How the server works](doc/ServerOperation.md)
- [The server's state machine](doc/StateMachine.md)
