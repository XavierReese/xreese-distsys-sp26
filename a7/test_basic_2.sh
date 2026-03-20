#!/bin/bash
# test_basic_machine2.sh
#
# Run on MACHINE 2 after test_basic.sh is running on machine 1.
# Copy all .py files and scripts to the same directory on machine 2 first.
#
# Usage: bash test_basic_machine2.sh <project_name>
# Example: bash test_basic_machine2.sh xreese01-a7

PROJECT=${1:?"Usage: bash test_basic_machine2.sh <project_name>"}

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

mkdir -p data logs

echo "================================================"
echo " A7 Basic Test (machine 2) — project: $PROJECT"
echo " Working dir: $SCRIPT_DIR"
echo "================================================"

# --- Start peerB and peerC at exactly the same time ---
# Both run from this directory. Their data files won't collide because
# HashTable names files with the peer suffix (table-peerB.ckpt etc.)
# and data/ files are UUIDs.
echo "[1] Starting peerB and peerC simultaneously..."

python3 -u Peer.py "$PROJECT" peerB > logs/peerB.log 2>&1 &
PEER_B_PID=$!

python3 -u Peer.py "$PROJECT" peerC > logs/peerC.log 2>&1 &
PEER_C_PID=$!

echo "    peerB PID: $PEER_B_PID"
echo "    peerC PID: $PEER_C_PID"

# Give them a moment to start before tailing
sleep 2

# Sanity check
for pid in $PEER_B_PID $PEER_C_PID; do
    if ! kill -0 "$pid" 2>/dev/null; then
        echo "ERROR: a peer failed to start. Check logs/"
        exit 1
    fi
done

echo ""
echo "Logs: logs/peerB.log and logs/peerC.log"
echo "Tailing both below (Ctrl+C to stop both peers)."
echo "================================================"
echo ""

# Trap Ctrl+C to cleanly kill both peers
cleanup() {
    echo ""
    echo "Stopping peerB and peerC..."
    kill "$PEER_B_PID" "$PEER_C_PID" 2>/dev/null
}
trap cleanup EXIT

# tail -f on two files interleaves them and prefixes each line with the filename
tail -f logs/peerB.log logs/peerC.log
