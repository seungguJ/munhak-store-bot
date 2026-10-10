#!/usr/bin/env sh
# GitHub Pages용 정적 사이트 조립: web/ + data/ → _site/
set -e
cd "$(dirname "$0")/.."
rm -rf _site
cp -r web _site
mkdir -p _site/data
cp data/events.json data/venues.json _site/data/
echo "built _site"
