# zeitgitter/zeitgitter docker image

Zeitgitter is a distributed timestamping service. It is based on *GIT*
(probably the most widely used Blockchain, if you think about it) and
*PGP/GPG*, providing cryptographic protection.

The distinguishing features are

* leverages the power of standard tools,
* very efficient (in terms of power, storage, bandwidth, cost),
* can be integrated into any workflow which can uses or can benefit from `git`,
* because the list of issued timestamps on (remote) `git` repositories is
  recorded in a local `git` repository, the same timestamping mechanism can be
  used for **cross-timestamping.**

I think despite the coolness of ease of use, efficiency, and universality,
**cross-timestamping** is the actual killer feature: Zeitgitter timestampers
can empower other members of the Zeitgitter network by confirming their
credibility. This effect is much stronger than in traditional distributed (or
Blockchain) systems, as only a single honest member in the entire network can
essentially prevent everyone else from secretly issuing fake, spoofed
timestamps. And you do not even need to know who the honest server is!

The trust and power of the network comes thus (also) from the diversity of its
members. Therefore, **we need you to operate a Zeitgitter timeserver**. And it
can be as tiny as a Raspberry Pi Zero W, as long as you prevent data loss and
the leakage of the private key.

# Setting up a simple timestamper

Have a DNS name point at your server, have a TLS reverse proxy there, create
the following two files, and then run `docker-compose up -d`. That's it!

If you want to know more, including looking at the source or see more setup
options, visit https://github.com/zeitgitter/zeitgitterd

## `server.env`

Obviously, adapt this according to your data:

```env
# Your real name (you may use HTML)
ZEITGITTER_OWNER=Rubeus Hagrid

# Contact information (you should use HTML)
ZEITGITTER_CONTACT=<a href="mailto:rubeus@hagrid.snakeoil">Rubeus Hagrid</a><br/>Hogwarts

# State your jurisdiction (you may use HTML)
ZEITGITTER_COUNTRY=Scotland

# This server's URL
ZEITGITTER_OWN_URL=https://hagrid.snakeoil

# This server's name and mail address (a GnuPG key with that ID is generated)
ZEITGITTER_KEYID=Hagrid Timestomping Service <timestomping@hagrid.snakeoil>
```

# `docker-compose.yml`

```yml
version: "2"

services:
  zeitgitter:
    restart: unless-stopped
    image: zeitgitter/zeitgitter
    container_name: zeitgitter
    env_file:
      - "server.env"
    ports:
      - 15177:15177
    volumes:
      - ./persistent-data:/persistent-data
```
