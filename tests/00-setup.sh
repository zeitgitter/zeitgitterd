#!/bin/bash
exit
d=$1
shift
export HOME=$d
cat << EOF > $d/zeitgitter.conf
own-url     = https://temp.hagrid.snakeoil
owner       = Rubeus Hagrid
contact     = By Owl
country     = Scotland
listen-port = 16675
keyid       = Temporary Timestomping Service <temp@hagrid.snakeoil>
debug       = 2,gnupg=INFO
EOF
./zeitgitterd.py --config-file $d/zeitgitter.conf
