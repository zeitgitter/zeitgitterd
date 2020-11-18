# Running Zeitgitter server in Docker

To run a Zeitgitter server in a [Docker](https://www.docker.com) container, the
following steps are necessary:

## Quick setup

1. Copy `sample.env` to `server.env` and update it with your information:
   - `ZEITGITTER_OWN_URL`: Choose a name, such as `<funny-name>.example.ch`,
     which will make the Server known under a short name of *funny-name*. Or,
     `zeitgitter.example.org`, which will make it known as *example*.
   - `ZEITGITTER_OWNER`: Who (person, affiliation) maintains the time server.
   - `ZEITGITTER_KEYID`: The unique name and mail address your OpenPGP key should be
     created for, e.g.
     `funny-name Timestamping Service <funny-name@example.ch` or
     `Example.org Timestamping service <zeitgitter@example.org>`.
   - `ZEITGITTER_CONTACT` and `ZEITGITTER_COUNTRY` should be self-explanatory.
1. Set up a [TLS reverse proxy](#setting-up-a-tls-reverse-proxy)
   to accept your HTTPS traffic and forward it to
   port 15177, where the Zeitgitter timestamping server will pick it up and
   process it.
1. Run `docker-compose up --quiet-pull -d`
1. Done! **Congratulations, you have a running timestamping server!**
1. To enable trust in your server:
   - Ensure `./persistent-data/repo` is persistent, i.e., will not be deleted by
     hardware or software failures or human error (this typically implies RAID
     and backup)
   - Protect `./persistent-data/.gnupg` from prying eyes, especially ensure that
     absolutely no one not listed as owner has access to your private
     timestamping key
   - Consider publishing your timestamps (see [next section](#advanced-setup))
   - Consider allowing other timestamping servers to cross-timestamp with you
     (see [next section](#advanced-setup))

## Advanced setup

1. Chose a machine where as few people as possible have access to.
1. Check out this repository into it.
1. Copy `./sample.env` to `./server.env` and update it with your information
   (see [explanation above](#quick-setup)).
1. Copy `./zeitgitter/zeitgitter.conf` to `./persistent-data/zeitgitter.conf`
1. Update the information in there, ignoring those five labeled with
   `EASYCONFIG` (the settings in `./server.env` will take precedence).
1. Set up a TLS reverse proxy to accept your HTTPS traffic and forward it to
   port 15177, where the Zeitgitter timestamping server will pick it up and
   process it.
1. Ensure `./persistent-data/repo` is persistent, i.e., will not be deleted by
   hardware or software failures or human error (this typically implies RAID
   and backup).
   - Missing timestamping entries in your repo will cast doubt on the
     trustworthiness of your timestamping server.
   - If you *do* run into problems with losing some data, immediately
     document your data losses in your repository (signed and timestamped)
     and, if possible, inform your users that they should resubmit any
     timestamping requests that have been lost.
1. Publish your timestamp repository to a public `git` repository.
   - Create one or more public repositories.
   - Create an SSH key and put it in `./persistent-data/.ssh`.
   - Add the key as a trusted push source to the public repositories.
   - Configure `zeitgitter.conf` to push to those repositories
     (`push-repository` and `push-branch` configuration variables).
1. Protect `./persistent-data/.gnupg` from prying eyes, especially ensure that
   absolutely no one not listed as owner has access to your private
   timestamping key.
   - Anyone with knowledge of the private key can create (false)
     timestamps in your name, casting doubt on *all* your timestamps
     ever created.
   - Cross-timestamping does help reduce the impact of this, but everyone
     will have to go the extra mile to show that their timestamps were
     issued at the time they claim to be and not back-dated.
   - See [Key Loss](#key-loss) below.
1. Set up cross-timestamping:
   - Obtain timestamps from other servers (by default, this will be
     `https://gitta.zeitgitter.net` and `https://diversity.zeitgitter.net`)
   - If possible, provide your data to the [list of public timestamping
     servers](https://gitlab.com/zeitgitter/git-timestamp/-/blob/master/doc/ServerList.md)
     using a pull request.
   - If possible, get in touch with other timestamping server providers, so
     they can cross-timestamp with you.
1. Run `docker-compose up -d`
1. Start monitoring, e.g. by running `./tools/zeitgitter-repo-health.sh` on a
   monitoring server. (It maintains a copy of the repository, pulled from the
   remote repository in regular intervals, so ensure there is enough space
   available on that machine.)
1. Done! **Congratulations, you have a professionally-run timestamping server!**

# Setting up a TLS reverse proxy

If you serve multiple web sites or services via Docker, you probably already have done that before. If this is your first time, you may use the following instructions or search the WWW for "TLS reverse proxy".

## Using Apache on Debian/Ubuntu

We use the sample configuration data (`https://hagrid.snakeoil`, `rubeus@hagrid.snakeoil`) for our example. Of course, you have to adopt this to your needs.

1. Ensure the DNS entry for `hagrid.snakeoil` points to your server.
1. Install Apache and Let's Encrypt, if you have not done that already:
   ```sh
   apt install apache python3-certbot-apache
   ```
1. Put the following into a new file
   `/etc/apache2/sites-available/hagrid.snakeoil.conf`; this is for HTTP service
   for the domain; we will later upgrade to HTTPS):
   ```Apache
   <VirtualHost *:80>
     ServerAdmin rubeus@hagrid.snakeoil
     ServerName hagrid.snakeoil
     DocumentRoot /var/www/hagrid
     ErrorLog ${APACHE_LOG_DIR}/hagrid_error.log
     CustomLog ${APACHE_LOG_DIR}/hagrid.log combined

     ProxyPreserveHost On
     ProxyPass /.well-known !
     ProxyPass / http://localhost:15177/
     ProxyPassReverse / http://localhost:15177/
   </VirtualHost>
   ```
1. Activate the site:
   ```sh
   a2ensite hagrid.snakeoil.conf
   a2enmod proxy_http
   systemctl restart apache2
   ```
1. Upgrade to HTTPS with Let's Encrypt (the options after `--apache` are
   optional, but recommended):
   ```sh
   letsencrypt -d hagrid.snakeoil --apache --must-staple --redirect --hsts --uir
   ```
1. Done!

# Key Loss

## Prevent loss

Your **repository** can (and, for trust reasons, should) be publicly available.
Pushing your git repository to a remote repository such as GitLab or GitHub
provides both as an effective means of publication as well as independent
second storage, colloquially known as "backup". Just to be sure, this should
not be your only means of backup, but you get the idea.

Your **PGP private key** is slightly more complicated: It should not be lost
(i.e., destroyed) and should also not be leaked (i.e., made available to anyone
else). The confidentiality is one important step toward the prevention of key
abuse, i.e., providing signatures which are not recorded and cross-timestamped
and therefore cannot be distinguished from illegitimate or fraudulent
timestamps.

To **prevent loss,** it is recommended to store the PGP key on a reliable long-term
medium (e.g., 2 different brands of USB stick or printed on a piece of paper)
and locked away in a safe.

To **prevent leakage,** the system should be kept up-to-date both in terms of
software but also network security:
* Do limit the number of people with access to the machine (both physical and virtual),
* do limit the number of services running on the machine, and
* configure it securely, if possible with security monitoring.

## If anything bad happened

All clients by default record the Key ID they first saw when talking to your
timestamping service and will verify the key of all future timestamping
signatures against this recorded ID ("trust on first use", TOFU).

Therefore, the recommended way to deal with the destruction or leakage of the
private key is to do the following:

1. Stop running the timestamping service.
1. Commit any remaining signatures to the repository and push it.
1. Put up a notice of what happened on the old server (or, better, its TLS
   proxy).
1. Put up a notice of what happened into the repository happened and commit
   this information (preferably signed by your personal key) and push this
   information to the remote repositories.
   not-yet-published signatures).
1. Create an entirely new replacement server with different URL, shortname,
   email address, and repository.
1. Retire the old server.
