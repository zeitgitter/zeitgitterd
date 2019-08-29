# Running Zeitgitter server in Docker

To run a Zeitgitter server in a [Docker](https://www.docker.com) container, the
following steps are necessary:

1. `make` (runs `docker build . -t zeitgitter; docker run -v
   /var/lib/zeitgitter:/root zeitgitter`)
2. Edit `/var/lib/zeitgitter/zeitgitter.conf` and search for the four occurences
   of `EASYCONFIG`. Modify them to include your real name (`owner`), contact,
   country, and the server's URL (`own-url`).
3.  Ensure that `/var/lib/zeitgitter/` is persistent (e.g., RAID and backup), as
   this contains the information that ensures the validity of your timestamping
   service
4. Check that everything is correct by running `make`; hit Ctrl-C twice to
   terminate
5. Reiterate items 2 and 4 until you are happy
6. `make daemon` will run Zeitgitter in the background
