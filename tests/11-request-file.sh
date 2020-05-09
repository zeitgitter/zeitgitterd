#!/bin/sh
d=$1
shift
wget --no-verbose -O $d/11-request-file.css  --content-on-error "$@" \
  'http://localhost:15178/zeitgitter.css'
diff $d/11-request-file.css ./zeitgitter/web/zeitgitter.css
