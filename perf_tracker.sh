#!/usr/bin/env bash

set -ex

function run_perf_tracker {
  for j in `seq 3`;
  do
    docker run --rm -v /tmp:/tmp jinaai/jina:devel hello-world > /tmp/hw.log;
    perl -lne 'print "$1\t$2" if(/done in ⏱ (.*)s 🐎 (.*)\/s/)' /tmp/hw.log
  done
}

function git_push {
  git config --local user.email "dev-bot@jina.ai"
  git config --local user.name "Jina Dev Bot"
  git add tracking_history.txt
  git commit -m "Update tracking_history"
  git push --set-upstream origin master
}


function run_and_publish {
  git clone https://github.com/jina-ai/perf-tracker.git
  run_perf_tracker >> perf-tracker/tracking_history.txt
  cd perf-tracker
  git_push
}

run_and_publish
