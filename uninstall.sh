#!/bin/sh

SCRIPT="import sys
for p in sys.path:
  if p.endswith('site-packages'):
    print p
    break
"
SITEPKGS=`python -c "$SCRIPT"`
rm -rf $SITEPKGS/pywebmvc
rm -rf /opt/pywebmvc
