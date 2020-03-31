#!/usr/bin/env bash

# Requirements
# brew install hub
# npm install -g git-release-notes
# pip install twine wheel

set -e

INIT_FILE='jina/__init__.py'
TMP_INIT_FILE='./__init__.py.tmp'
VER_TAG='__version__ = '
SOURCE_ORIGIN='origin'

function escape_slashes {
    sed 's/\//\\\//g'
}

function change_line {
    local OLD_LINE_PATTERN=$1
    local NEW_LINE=$2
    local FILE=$3

    local NEW=$(echo "${NEW_LINE}" | escape_slashes)
    sed -i .bak '/'"${OLD_LINE_PATTERN}"'/s/.*/'"${NEW}"'/' "${FILE}"
    mv "${FILE}.bak" ${TMP_INIT_FILE}
}


function clean_build {
    rm -rf dist
    rm -rf *.egg-info
    rm -rf build
}

function pub_pypi {
    # publish to pypi
    clean_build
    python setup.py sdist bdist_wheel
    twine upload dist/*
    clean_build
}

function pub_gittag {
    git add $INIT_FILE
    git commit -m "chore(version): bumping version to $VER"
    git tag $VER -m "$(cat ./CHANGELOG.tmp)"
    # git remote add $SOURCE_ORIGIN https://hanxiao:${GITHUB_ACCESS_TOKEN}@github.com/gnes-ai/gnes.git
    git push $SOURCE_ORIGIN $VER
    git checkout master
}


function make_release_note {
    git-release-notes $1..HEAD .github/release-template.ejs > ./CHANGELOG.tmp
    printf '\n%s\n%s\n%s\n%s\n' "## Release Note (\`$2\`)" "> Release time: $(date +'%Y-%m-%d %H:%M:%S')" "$(cat ./CHANGELOG.tmp)" "$(cat ./CHANGELOG.md)" > ./CHANGELOG.md
}

BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [[ "$BRANCH" != "master" ]]; then
  printf "You are not at master branch, exit\n";
  exit 1;
fi

LAST_UPDATE=`git show --no-notes --format=format:"%H" $BRANCH | head -n 1`
LAST_COMMIT=`git show --no-notes --format=format:"%H" origin/$BRANCH | head -n 1`

if [ $LAST_COMMIT != $LAST_UPDATE ]; then
    printf "Your local $BRANCH is behind the remote master, exit\n"
    exit 1;
fi

OLDVER=$(git tag -l | sort -V | tail -n1)
printf "current version:\t\e[1;33m$OLDVER\e[0m\n"

VER=$(echo $OLDVER | awk -F. -v OFS=. 'NF==1{print ++$NF}; NF>1{$NF=sprintf("%0*d", length($NF), ($NF+1)); print}')
printf "bump version to:\t\e[1;32m$VER\e[0m\n"

make_release_note $OLDVER $VER

head -n10 ./CHANGELOG.md

read -p "release this version? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    VER_VAL=$VER_TAG"'"${VER#"v"}"'"
    change_line "$VER_TAG" "$VER_VAL" $INIT_FILE
    pub_pypi
    pub_gittag
    make_chore_pr $VER
fi


