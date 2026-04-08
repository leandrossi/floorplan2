#!/usr/bin/env bash
set -euo pipefail

SRC="/home/leandrossi/test/ainstallator/export/acala_engine/"
DST="/home/leandrossi/test/floorplantest2/vendor/acala_engine/"

mkdir -p "/home/leandrossi/test/floorplantest2/vendor"
rsync -av --delete "$SRC" "$DST"

cd "/home/leandrossi/test/floorplantest2"
python -m pip install -e "./vendor/acala_engine"

echo "acala_engine synced and reinstalled in editable mode."
