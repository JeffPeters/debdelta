#!/bin/sh

## This script can build the debdelta package
## in a safe way

set -e

## you can force the signing key as follows
#KEY=-k0x57CCF4596A1353C2!

## you can give this command options that will be passed to debuild
## make sure that `-S` if present is the first option

B=`dirname $0`

cd $B

if git status -s | grep '^ M' ; then
 echo === !!!!!!!! there are modified files
 echo ===  Hit enter to continue
 read pippo
fi

BRANCH=`git branch  | grep '^*' | cut -c3-`

D=`mktemp -d --tmpdir=$B/build_area`

echo === temporary build directory $B/$D

#if test -d build_area/debdelta ; then
# echo build_area/debdelta
# exit 1
#fi

git archive  $BRANCH debdelta | ( cd $B/$D/ ; tar -xf - )

cp $B/debdelta/doc/debdelta_suite.pdf -t  $B/$D/debdelta/doc/
cp $B/debdelta/doc/debdelta_suite.txt -t  $B/$D/debdelta/doc/
mkdir --mode=0755 $B/$D/debdelta/doc/html/
cp $B/debdelta/doc/html/* -t  $B/$D/debdelta/doc/html/



#debuild
if test "$1" = "-S" ; then
    cd  $B/$D/debdelta
    ## this chooses the wrong key see Bug #980909
    #dpkg-buildpackage --build=source  $KEY
    debuild  $KEY "$@"
elif which pdebuild ; then
    cd  $B/$D/debdelta
    pdebuild "$@"
    cd ..
    cp -vb /var/cache/pbuilder/result/* -t .
    trash -v debdelta_*_source.changes
    debsign $KEY debdelta*.changes
else
    echo '** consider using pdebuild '
    cd  $B/$D/debdelta
    debuild $KEY  "$@"
    #dpkg-buildpackage -k$KEY
fi

cd $B

echo === results in $B/$D

echo === should   rm -r $B/$D/debdelta

