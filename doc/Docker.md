# Running Zeitgitter server in Docker

To run a Zeitgitter server in a [Docker](https://www.docker.com) container, the
following steps are necessary:

## Quick setup

1. Copy `sample.env` to `server.env` and update it with your information
2. Set up a [TLS reverse proxy](#setting-up-a-tls-reverse-proxy)
   to accept your HTTPS traffic and forward it to
   port 15177, where the Zeitgitter timestamping server will pick it up and
   process it.
3. Run `docker-compose up --quiet-pull -d`
4. Done! **Congratulations, you have a running timestamping server!**
5. To ensure trust in your server:
   - Ensure `./zgdata/repo` is persistent, i.e., will not be deleted by
     hardware or software failures or human error (this typically implies RAID
     and backup)
   - Protect `./zgdata/.gnupg` from prying eyes, especially ensure that
     absolutely no one not listed as owner has access to your private
     timestamping key
   - Consider publishing your timestamps (see next section)
   - Consider allowing other timestamping servers to cross-timestamp with you
     (see next section)

## Advanced setup

1. Chose a machine where as few people as possible have access to.
2. Copy `./sample.env` to `./server.env` and update it with your information
3. Copy `./zeitgitter/zeitgitter.conf` to `./zgdata/zeitgitter.conf`
4. Update the information in there, ignoring those five labeled with
   `EASYCONFIG` (the settings in `./server.env` will take precedence).
5. Set up a TLS reverse proxy to accept your HTTPS traffic and forward it to
   port 15177, where the Zeitgitter timestamping server will pick it up and
   process it.
6. Ensure `./zgdata/repo` is persistent, i.e., will not be deleted by
   hardware or software failures or human error (this typically implies RAID
   and backup).
   - Missing timestamping entries in your repo will cast doubt on the
     trustworthiness of your timestamping server.
   - If you *do* run into problems with losing some data, immediately
     document your data losses in your repository (signed and timestamped)
     and, if possible, inform your users that they should resubmit any
     timestamping requests that have been lost.
7. Publish your timestamp repository to a public `git` repository.
8. Protect `./zgdata/.gnupg` from prying eyes, especially ensure that
   absolutely no one not listed as owner has access to your private
   timestamping key.
   - Anyone with knowledge of the private key can create (false)
     timestamps in your name, casting doubt on *all* your timestamps
     ever created.
   - Cross-timestamping does help reduce the impact of this, but everyone
     will have to go the extra mile to show that their timestamps were
     issued at the time they claim to be and not back-dated.
9. Set up cross-timestamping:
   - Obtain timestamps from other servers (by default, this will be
     `https://gitta.zeitgitter.net` and `https://diversity.zeitgitter.net`)
   - If possible, provide your data to the [list of public timestamping
     servers](https://gitlab.com/zeitgitter/git-timestamp/-/blob/master/doc/ServerList.md)
     using a pull request.
   - If possible, get in touch with other timestamping server providers, so
     they can cross-timestamp with you.
10. Run `docker-compose up -d`
11. Done! **Congratulations, you have a professionally run timestamping server!**

# Setting up a TLS reverse proxy

If you serve multiple web sites or services via Docker, you probably already have done that before. If this is your first time, you may use the following instructions or search the WWW for "TLS reverse proxy".

## Using Apache on Debian/Ubuntu

We use the sample configuration data (`https://hagrid.snakeoil`, `rubeus@hagrid.snakeoil`) for our example. Of course, you have to adopt this to your needs.

1. Ensure the DNS entry for `hagrid.snakeoil` points to your server.
2. Install Apache and Let's Encrypt, if you have not done that already:
   ```sh
   apt install apache python3-certbot-apache
   ```
3. Put the following into a new file
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
4. Activate the site:
   ```sh
   a2ensite hagrid.snakeoil.conf
   a2enmod proxy_http
   systemctl restart apache2
   ```
5. Upgrade to HTTPS with Let's Encrypt (the options after `--apache` are
   optional, but recommended):
   ```sh
   letsencrypt -d hagrid.snakeoil --apache --must-staple --redirect --hsts --uir
   ```
6. Done!
