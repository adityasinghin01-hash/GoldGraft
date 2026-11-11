#!/bin/zsh
# Convert the generated chapter photos into web images: 1600px JPEG, quality 82 (macOS sips).
SRC=${1:-$HOME/reports/goldgraft-web-20261111/images-codex}
OUT=$(dirname $0)/../public/world
mkdir -p $OUT
for f in $SRC/*.png; do
  n=$(basename $f .png)
  [ -f $OUT/$n.jpg ] && [ $OUT/$n.jpg -nt $f ] && continue
  sips -s format jpeg -s formatOptions 82 -Z 1600 "$f" --out "$OUT/$n.jpg" >/dev/null && echo "made $n.jpg ($(du -h $OUT/$n.jpg | cut -f1))"
done
