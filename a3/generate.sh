#!/bin/bash

# Directory to store files
DIR="testdata"

# Number of files
COUNT=1000

# Size per file
SIZE="8K"

mkdir -p "$DIR"

echo "Generating $COUNT files of size $SIZE in $DIR..."

for i in $(seq 1 $COUNT)
do
    dd if=/dev/urandom \
       of="$DIR/file_$i.dat" \
       bs=$SIZE \
       count=1 \
       status=none
done

echo "Done."
echo "Total size:"
du -sh "$DIR"

