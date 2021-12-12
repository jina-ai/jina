#!/usr/bin/env bash

# Requirements
# brew install hub
# npm install -g git-release-notes
# pip install twine wheel

set -ex

INIT_FILE='../../docarray/__init__.py'
VER_TAG='__version__ = '

function escape_slashes {
    sed 's/\//\\\//g'
}

function update_ver_line {
    local OLD_LINE_PATTERN=$1
    local NEW_LINE=$2
    local FILE=$3

    local NEW=$(echo "${NEW_LINE}" | escape_slashes)
    sed -i '/'"${OLD_LINE_PATTERN}"'/s/.*/'"${NEW}"'/' "${FILE}"
    head -n10 ${FILE}
}


function clean_build {
    rm -rf dist
    rm -rf *.egg-info
    rm -rf build
}

function pub_pypi {
    # publish to pypi
    clean_build
    python setup.py sdist
    twine upload dist/*
    clean_build
}

function git_commit {
    git config --local user.email "dev-bot@jina.ai"
    git config --local user.name "Jina Dev Bot"
    git add $INIT_FILE
    git commit -m "chore(version): the next docarray version will be $NEXT_VER" -m "build($RELEASE_ACTOR): $RELEASE_REASON"
}


BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [[ "$BRANCH" != "master" ]]; then
  printf "You are not at master branch, exit\n";
  exit 1;
fi

# release the current version
export RELEASE_VER=$(sed -n '/^__version__/p' $INIT_FILE | cut -d \' -f2)
LAST_VER=$(git tag -l | sort -V | tail -n1)
printf "last version: \e[1;32m$LAST_VER\e[0m\n"

if [[ $1 == "final" ]]; then
  printf "this will be a final release: \e[1;33m$RELEASE_VER\e[0m\n"

  NEXT_VER=$(echo $RELEASE_VER | awk -F. -v OFS=. 'NF==1{print ++$NF}; NF>1{$NF=sprintf("%0*d", length($NF), ($NF+1)); print}')
  printf "bump master version to: \e[1;32m$NEXT_VER\e[0m\n"

  pub_pypi

  VER_TAG_NEXT=$VER_TAG\'${NEXT_VER}\'
  update_ver_line "$VER_TAG" "$VER_TAG_NEXT" "$INIT_FILE"
  RELEASE_REASON="$2"
  RELEASE_ACTOR="$3"
  git_commit
elif [[ $1 == 'rc' ]]; then
  printf "this will be a release candidate: \e[1;33m$RELEASE_VER\e[0m\n"
  DOT_RELEASE_VER=$(echo $RELEASE_VER | sed "s/rc/\./")
  NEXT_VER=$(echo $DOT_RELEASE_VER | awk -F. -v OFS=. 'NF==1{print ++$NF}; NF>1{$NF=sprintf("%0*d", length($NF), ($NF+1)); print}')
  NEXT_VER=$(echo $NEXT_VER | sed "s/\.\([^.]*\)$/rc\1/")
  printf "bump master version to: \e[1;32m$NEXT_VER\e[0m, this will be the next version\n"


  pub_pypi

  VER_TAG_NEXT=$VER_TAG\'${NEXT_VER}\'
  update_ver_line "$VER_TAG" "$VER_TAG_NEXT" "$INIT_FILE"
  RELEASE_REASON="$2"
  RELEASE_ACTOR="$3"
  git_commit
else
  # as a prerelease, pypi update only, no back commit etc.
  COMMITS_SINCE_LAST_VER=$(git rev-list $LAST_VER..HEAD --count)
  NEXT_VER=$RELEASE_VER".dev"$COMMITS_SINCE_LAST_VER
  printf "this will be a developmental release: \e[1;33m$NEXT_VER\e[0m\n"

  VER_TAG_NEXT=$VER_TAG\'${NEXT_VER}\'
  update_ver_line "$VER_TAG" "$VER_TAG_NEXT" "$INIT_FILE"

  pub_pypi
fi
