#!/usr/bin/env bash

set -ex

# 0.9.6.dev1
# the version grab from __init__ file
export _JINA_INIT_VER=$(sed -n '/^__version__/p' ./jina/__init__.py | cut -d \' -f2)

# v0.9.5
# the last version grab from git tags, must use under a git repo
export _JINA_LAST_GIT_V_VER=$(git tag -l | sort -V | tail -n1)

# 0.9.5
# the last version grab from git tags, without the heading v
export _JINA_LAST_GIT_VER=${_JINA_LAST_GIT_V_VER/v/}

# 0.9.5 ONLY on GITHUB workflow where $GITHUB_REF is presented
export _JINA_TAG_VER=${GITHUB_REF/refs\/tags\/v/}

# 0.9
export _JINA_TAG_MINOR_VER=${JINA_VER%.*}

# 0.9.6
# the version release to PyPi/Docker on release event
export _JINA_FINAL_VER=$(echo $_JINA_INIT_VER | cut -d '.' -f1,2,3)

# 0.9
# the minor version alias to _JINA_FINAL_VER
export _JINA_FINAL_MINOR_VER=${_JINA_FINAL_VER%.*}

# 0.9.7
# the next final version, should NOT be used directly
export _JINA_NEXT_FINAL_VER=$(echo $_JINA_FINAL_VER | awk -F. -v OFS=. 'NF==1{print ++$NF}; NF>1{$NF=sprintf("%0*d", length($NF), ($NF+1)); print}')

# 0.9.6.dev2
# the next version for __init__.py on every master merge
export _JINA_NEXT_INIT_VER=$(echo $_JINA_INIT_VER | awk -F'dev' -v OFS="dev" '{$NF=sprintf("%0*d", length($NF), ($NF+1)); print}')

# 0.9.7.dev0
# the next version for __init__.py on every release
export _JINA_NEXT_FINAL_INIT_VER="$_JINA_NEXT_FINAL_VER.dev0"

