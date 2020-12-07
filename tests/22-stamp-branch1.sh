#!/bin/sh
d=$1
shift
wget --no-verbose -O $d/22-stamp-branch1-server.asc --content-on-error "$@" \
  --post-data='request=stamp-branch-v1&commit=2222222222222222222222222222222222222222&parent=3333333333333333333333333333333333333333&tree=4444444444444444444444444444444444444444' \
  'http://localhost:15178/'
cat > $d/22-stamp-branch1-verify.asc << EOF
tree 4444444444444444444444444444444444444444
parent 3333333333333333333333333333333333333333
parent 2222222222222222222222222222222222222222
author Hagrid Snakeoil Timestomping Service <timestomping@hagrid.snakeoil> 1551155115 +0000
committer Hagrid Snakeoil Timestomping Service <timestomping@hagrid.snakeoil> 1551155115 +0000
gpgsig -----BEGIN PGP SIGNATURE-----
 
 iF0EABECAB0WIQTKSvqybFiyCVmcgCU1Pf7FEvpHxwUCXHS/qwAKCRA1Pf7FEvpH
 x23cAKCfieDDAbfxM4hECEshWJwrG1OCPwCeIylYzCtfybGbyFlUjER2O9VRySM=
 =ScxK
 -----END PGP SIGNATURE-----

:watch: https://hagrid.snakeoil branch timestamp 2019-02-26 04:25:15 UTC
EOF
diff $d/22-stamp-branch1-*.asc
