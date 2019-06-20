# Customize

If you would like to customize the files in this directory, copy all the files
you need to a different location and set `webroot` in `/etc/zeitgitter.conf`
to your new location.

:warning: Files in *this* directory will be overwritten by updates, so any
modifications *here* will be lost.

Files starting with `cf-*` will only be served if `--webconfig` is set; some
are treated specially (or even created dynamically) by `server.py` and
`webconfig.py`. In `--webconfig` mode, requesting `/` will serve
`cf-index.html` instead of `index.html`.
