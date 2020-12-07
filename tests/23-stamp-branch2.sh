#!/bin/sh
d=$1
shift
wget --no-verbose -O $d/23-sign-branch2-server.asc --content-on-error "$@" \
  --post-data='request=stamp-branch-v1&commit=5555555555555555555555555555555555555555&tree=6666666666666666666666666666666666666666' \
  'http://localhost:15178/'
cat > $d/23-sign-branch2-verify.asc << EOF
tree 6666666666666666666666666666666666666666
parent 5555555555555555555555555555555555555555
author Hagrid Snakeoil Timestomping Service <timestomping@hagrid.snakeoil> 1551155115 +0000
committer Hagrid Snakeoil Timestomping Service <timestomping@hagrid.snakeoil> 1551155115 +0000
gpgsig -----BEGIN PGP SIGNATURE-----
 
 iF0EABECAB0WIQTKSvqybFiyCVmcgCU1Pf7FEvpHxwUCXHS/qwAKCRA1Pf7FEvpH
 x9nVAJ9kury7Jn2kgAviwDnNTV8+gtdxYQCdEhYt4nwot+jS1zCX+S5yaeYEmP0=
 =PcnY
 -----END PGP SIGNATURE-----

:watch: https://hagrid.snakeoil branch timestamp 2019-02-26 04:25:15 UTC
EOF
diff $d/23-sign-branch2-*.asc
