#!/bin/bash

AVATAR_DIR="./.git/avatar"
TITLE="get.jina.ai"
LOGO="logo.png"
OUTPUT_DIR="video"
RESOLUTION="1920x1080"
FORMAT="mp4"

gource jina --user-image-dir $AVATAR_DIR --seconds-per-day 0.1 --hide filenames,dirnames,usernames --title $TITLE --logo $LOGO -$RESOLUTION -o - | ffmpeg -y -r 60 -f image2pipe -vcodec ppm -i - -vcodec libx264 -preset ultrafast -pix_fmt yuv420p -crf 1 -threads 0 -bf 0 $OUTPUT_DIR/gource-jina-$(date +"%Y_%m_%d").$FORMAT
