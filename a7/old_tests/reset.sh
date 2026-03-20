#!/bin/bash

# Directory to store files
DIR="./data"
PROJECT_NAME=$1

# Number of files
COUNT=1000

# Size per file
SIZE="8K"

echo "Deleting Old Log/Checkpoint"
rm -f table.ckpt table.txn

rm -r "$DIR"

mkdir -p "$DIR"

echo "Generating $COUNT files of size $SIZE in $DIR..."

python3 -c "
import json, os, string, random
os.makedirs('$DIR', exist_ok=True)
for i in range(50):
    filename = f'file_{i:02d}.json'
    # Generate ~200KB of random data per file
    garbage = ''.join(random.choices(string.ascii_letters + string.digits, k=200000))
    with open(os.path.join('$DIR', filename), 'w') as f:
        json.dump({'filename': filename, 'content': garbage}, f)
print('Successfully generated 50 files (~10MB total) in $DIR.')
"

echo "Done."
echo "Total size:"
du -sh "$DIR"

# start server
# echo "Starting Server..."
# python3 HashTableServer.py $PROJECT_NAME &
# SERVER_PID=$!

# Give the server a moment to register with the catalog
# sleep 2

# 3. Add data to the server
echo "Loading Data..."
python3 load_data.py $PROJECT_NAME $DIR

# echo "Data Loaded. Killing Server"
# kill $SERVER_PID
# sleep 1

echo "Done"
