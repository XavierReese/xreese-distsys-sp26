#!/bin/bash
# test_basic_machine2.sh
#
# Run on MACHINE 2 after test_basic.sh is fully running on machine 1
# and has printed "peerA is running and loaded with 40 files."
#
# Copy all .py files and shell scripts to the same directory first.
#
# Usage: bash test_basic_machine2.sh <project_name>
# Example: bash test_basic_machine2.sh xreese29-a7

PROJECT=${1:?"Usage: bash test_basic_machine2.sh <project_name>"}

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

echo "================================================"
echo " A7 Basic Test (machine 2) — project: $PROJECT"
echo " Working dir: $SCRIPT_DIR"
echo "================================================"

# --- Step 1: Kill leftover processes and wipe old data ---
echo "[1] Cleaning up any leftover processes..."
pkill -f "Peer.py" 2>/dev/null
sleep 2

echo "[2] Wiping previous run data..."
rm -rf data/ table-*.ckpt table-*.txn
mkdir -p data logs
echo "    Clean."

# --- Step 2: Start peerB and peerC simultaneously ---
# Both run from the same directory. Their checkpoint/log files are
# namespaced by peer suffix (table-peerB.ckpt, table-peerC.ckpt)
# and data files are UUIDs, so there is no collision.
echo "[3] Starting peerB and peerC simultaneously..."

python3 -u Peer.py "$PROJECT" peerB > logs/peerB.log 2>&1 &
PEER_B_PID=$!

python3 -u Peer.py "$PROJECT" peerC > logs/peerC.log 2>&1 &
PEER_C_PID=$!

echo "    peerB PID: $PEER_B_PID"
echo "    peerC PID: $PEER_C_PID"

# Give them a moment to start before checking
sleep 5

# Verify both are still running
for name in peerB peerC; do
    pid_var="PEER_${name^^}_PID"
    pid=${!pid_var}
    if ! kill -0 "$pid" 2>/dev/null; then
        echo ""
        echo "ERROR: $name crashed on startup. Last log lines:"
        tail -20 "logs/${name}.log"
        exit 1
    fi
    if grep -q "Failed on startup" "logs/${name}.log"; then
        echo ""
        echo "ERROR: HashTable failed to start for $name. Log:"
        tail -20 "logs/${name}.log"
        exit 1
    fi
done

echo "    Both peers are running."

# Cleanup handler — kills both peers on Ctrl+C
cleanup() {
    echo ""
    echo "Stopping peerB and peerC..."
    kill "$PEER_B_PID" "$PEER_C_PID" 2>/dev/null
}
trap cleanup EXIT

echo ""
echo "Logs: logs/peerB.log and logs/peerC.log"
echo "Tailing both below (Ctrl+C to stop both peers)."
echo "================================================"
echo ""

# tail -f on two files interleaves output and prefixes each line
# with the filename so you can tell which peer said what
tail -f logs/peerB.log logs/peerC.log
