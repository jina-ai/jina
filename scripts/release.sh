#!/usr/bin/env bash

# Requirements
# brew install hub
# npm install -g git-release-notes
# pip install twine wheel

set -ex

INIT_FILE='jina/__init__.py'
VER_TAG='__version__ = '
RELEASENOTE='./node_modules/.bin/git-release-notes'

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

function clean_egg {
    rm -rf *.egg-info
    rm -rf build
}

function pub_pypi {
    # publish to pypi
    clean_egg
    cp extra-requirements.txt jina/resources/
    python setup.py sdist
    twine upload dist/*
    clean_build
}

function git_commit {
    git config --local user.email "dev-bot@jina.ai"
    git config --local user.name "Jina Dev Bot"
    git tag "v$RELEASE_VER" -m "$(cat ./CHANGELOG.tmp)"
    git add $INIT_FILE ./CHANGELOG.md jina/resources/extra-requirements.txt
    git commit -m "chore(version): the next version will be $NEXT_VER" -m "build($RELEASE_ACTOR): $RELEASE_REASON"
}

function slack_notif {
    envsubst < ./.github/slack-pypi.json | curl -X POST -H 'Content-type: application/json' --data "@-" $JINA_SLACK_WEBHOOK
}


function make_release_note {
    ${RELEASENOTE} ${LAST_VER}..HEAD .github/release-template.ejs > ./CHANGELOG.tmp
    head -n10 ./CHANGELOG.tmp
    printf '\n%s\n\n%s\n%s\n\n%s\n\n%s\n\n' "$(cat ./CHANGELOG.md)" "<a name="release-note-${RELEASE_VER//\./-}"></a>" "## Release Note (\`${RELEASE_VER}\`)" "> Release time: $(date +'%Y-%m-%d %H:%M:%S')" "$(cat ./CHANGELOG.tmp)" > ./CHANGELOG.md
}

BRANCH=$(git rev-parse --abbrev-ref HEAD)

LAST_UPDATE=`git show --no-notes --format=format:"%H" $BRANCH | head -n 1`
LAST_COMMIT=`git show --no-notes --format=format:"%H" origin/$BRANCH | head -n 1`

if [ $LAST_COMMIT != $LAST_UPDATE ]; then
    printf "Your local $BRANCH is behind the remote master, exit\n"
    exit 1;
fi

# release the current version
export RELEASE_VER=$(sed -n '/^__version__/p' $INIT_FILE | cut -d \' -f2)
LAST_VER=$(git tag -l | sort -V | tail -n1)
printf "last version: \e[1;32m$LAST_VER\e[0m\n"

# Update new _versions.json if necessary
python ./scripts/prepend_version_json.py --version "v$RELEASE_VER"
git add ./docs/_versions.json

if [[ $1 == "final" ]]; then
  printf "this will be a final release: \e[1;33m$RELEASE_VER\e[0m\n"

  NEXT_VER=$(echo $RELEASE_VER | awk -F. -v OFS=. 'NF==1{print ++$NF}; NF>1{$NF=sprintf("%0*d", length($NF), ($NF+1)); print}')
  printf "bump master version to: \e[1;32m$NEXT_VER\e[0m\n"

  #make_release_note

  pub_pypi

  VER_TAG_NEXT=$VER_TAG\'${NEXT_VER}\'
  update_ver_line "$VER_TAG" "$VER_TAG_NEXT" "$INIT_FILE"
  RELEASE_REASON="$2"
  RELEASE_ACTOR="$3"
  git_commit
  slack_notif
elif [[ $1 == 'rc' ]]; then
  printf "this will be a release candidate: \e[1;33m$RELEASE_VER\e[0m\n"
  DOT_RELEASE_VER=$(echo $RELEASE_VER | sed "s/rc/\./")
  NEXT_VER=$(echo $DOT_RELEASE_VER | awk -F. -v OFS=. 'NF==1{print ++$NF}; NF>1{$NF=sprintf("%0*d", length($NF), ($NF+1)); print}')
  NEXT_VER=$(echo $NEXT_VER | sed "s/\.\([^.]*\)$/rc\1/")
  printf "bump master version to: \e[1;32m$NEXT_VER\e[0m, this will be the next version\n"

  make_release_note

  pub_pypi

  VER_TAG_NEXT=$VER_TAG\'${NEXT_VER}\'
  update_ver_line "$VER_TAG" "$VER_TAG_NEXT" "$INIT_FILE"
  RELEASE_REASON="$2"
  RELEASE_ACTOR="$3"
  git_commit
  slack_notif
else
  # as a prerelease, pypi update only, no back commit etc.
  # previously the INIT_FILE must have been updated
  pub_pypi
fi
