#!/usr/bin/env bash

# Requirements
# brew install hub
# npm install -g git-release-notes
# pip install twine wheel

set -ex

INIT_FILE='jina/__init__.py'
VER_TAG='__version__ = '

function escape_slashes {
    sed 's/\//\\\//g'
}

function update_ver_line {
    local OLD_LINE_PATTERN=$1
    local NEW_LINE=$2
    local FILE=$3

    local NEW=$(echo "${NEW_LINE}" | escape_slashes)
    if [ "$(uname)" == "Darwin" ]; then
      sed -i '' '/'"${OLD_LINE_PATTERN}"'/s/.*/'"${NEW}"'/' "${FILE}";
    else
      sed -i '/'"${OLD_LINE_PATTERN}"'/s/.*/'"${NEW}"'/' "${FILE}";
    fi
    head -n10 ${FILE}
}


BRANCH=$(git rev-parse --abbrev-ref HEAD)

#if [[ "$BRANCH" != "main" ]]; then
#  printf "You are not at main branch, exit\n";
#  exit 1;
#fi

LAST_UPDATE=`git show --no-notes --format=format:"%H" $BRANCH | head -n 1`
LAST_COMMIT=`git show --no-notes --format=format:"%H" origin/$BRANCH | head -n 1`

#if [ $LAST_COMMIT != $LAST_UPDATE ]; then
#    printf "Your local $BRANCH is behind the remote master, exit\n"
#    exit 1;
#fi

# update the current version
export RELEASE_VER=$(sed -n '/^__version__/p' $INIT_FILE | cut -d \' -f2)
LAST_VER=$(git tag -l | sort -V | tail -n1)
printf "last version: \e[1;32m$LAST_VER\e[0m\n"

if [[ $1 == "final" ]]; then
  printf "this will be a final release: \e[1;33m$RELEASE_VER\e[0m\n"

  NEXT_VER=$(echo $RELEASE_VER | awk -F. -v OFS=. 'NF==1{print ++$NF}; NF>1{$NF=sprintf("%0*d", length($NF), ($NF+1)); print}')
  printf "bump master version to: \e[1;32m$NEXT_VER\e[0m\n"

  VER_TAG_NEXT=$VER_TAG\'${NEXT_VER}\'
  update_ver_line "$VER_TAG" "$VER_TAG_NEXT" "$INIT_FILE"

elif [[ $1 == 'rc' ]]; then
  printf "this will be a release candidate: \e[1;33m$RELEASE_VER\e[0m\n"
  DOT_RELEASE_VER=$(echo $RELEASE_VER | sed "s/rc/\./")
  NEXT_VER=$(echo $DOT_RELEASE_VER | awk -F. -v OFS=. 'NF==1{print ++$NF}; NF>1{$NF=sprintf("%0*d", length($NF), ($NF+1)); print}')
  NEXT_VER=$(echo $NEXT_VER | sed "s/\.\([^.]*\)$/rc\1/")
  printf "bump master version to: \e[1;32m$NEXT_VER\e[0m, this will be the next version\n"

  VER_TAG_NEXT=$VER_TAG\'${NEXT_VER}\'
  update_ver_line "$VER_TAG" "$VER_TAG_NEXT" "$INIT_FILE"

else
  # as a prerelease, pypi update only, no back commit etc.
  COMMITS_SINCE_LAST_VER=$(git rev-list $LAST_VER..HEAD --count)
  NEXT_VER=$RELEASE_VER".dev"$COMMITS_SINCE_LAST_VER
  printf "this will be a developmental release: \e[1;33m$NEXT_VER\e[0m\n"

  VER_TAG_NEXT=$VER_TAG\'${NEXT_VER}\'
  update_ver_line "$VER_TAG" "$VER_TAG_NEXT" "$INIT_FILE"

fi