#!/bin/sh
d=$1
shift
wget --no-verbose -O $d/20-stamp-tag-server.asc --content-on-error "$@" \
  --post-data='request=stamp-tag-v1&commit=1111111111111111111111111111111111111111&tagname=sample-timestamping-tag' \
  'http://localhost:15178/'
cat > $d/20-stamp-tag-verify.asc << EOF
object 1111111111111111111111111111111111111111
type commit
tag sample-timestamping-tag
tagger Hagrid Snakeoil Timestomping Service <timestomping@hagrid.snakeoil> 1551155115 +0000

:watch: https://hagrid.snakeoil tag timestamp
-----BEGIN PGP SIGNATURE-----

iF0EABECAB0WIQTKSvqybFiyCVmcgCU1Pf7FEvpHxwUCXHS/qwAKCRA1Pf7FEvpH
xz10AJ4iSQRbbKVPFSk2hhORPBe8mEkzhQCcCmz/GQwmv4ZwTWE6G0ltXJ5oZ+Y=
=fFsz
-----END PGP SIGNATURE-----
EOF
diff $d/20-stamp-tag-*.asc
