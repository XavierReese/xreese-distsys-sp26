#!/bin/bash
# test_basic.sh
#
# Basic 3-peer test for Assignment 7. Run on MACHINE 1 only.
# Run from the directory containing all your .py files.
#
# Usage: bash test_basic.sh <project_name>
# Example: bash test_basic.sh xreese29-a7

PROJECT=${1:?"Usage: bash test_basic.sh <project_name>"}

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

echo "================================================"
echo " A7 Basic Test (machine 1) — project: $PROJECT"
echo " Working dir: $SCRIPT_DIR"
echo "================================================"

# --- Step 1: Kill any leftover peer processes from previous runs ---
# Stale peers stay in the catalog for ~3 minutes after dying.
# Killing them and waiting ensures load_data.py finds the fresh peer.
echo "[1] Cleaning up any leftover processes..."
pkill -f "Peer.py" 2>/dev/null
pkill -f "load_data.py" 2>/dev/null
sleep 2

# --- Step 2: Wipe previous run's data files ---
# If .ckpt or .txn files exist but data/ is empty (or vice versa),
# HashTable._startup() fails and the peer crashes silently.
# Always start clean.
echo "[2] Wiping previous run data..."
rm -rf data/ table-*.ckpt table-*.txn
mkdir -p data logs
echo "    Clean."

# --- Step 3: Start peerA ---
echo "[3] Starting peerA..."
python3 -u Peer.py "$PROJECT" peerA > logs/peerA.log 2>&1 &
PEER_A_PID=$!
echo "    peerA PID: $PEER_A_PID"

# Wait and verify it actually started — a silent crash shows up here
echo "    Waiting 3s then checking peerA is alive..."
sleep 3
if ! kill -0 "$PEER_A_PID" 2>/dev/null; then
    echo ""
    echo "ERROR: peerA crashed on startup. Last log lines:"
    tail -20 logs/peerA.log
    exit 1
fi

# Confirm clean startup in the log
if grep -q "Failed on startup" logs/peerA.log; then
    echo ""
    echo "ERROR: HashTable failed to start. Log:"
    tail -20 logs/peerA.log
    exit 1
fi

echo "    peerA is running."
echo "    Waiting 8s for catalog registration to settle..."
sleep 8

# --- Step 4: Load test data ---
echo "[4] Loading 40 test files into peerA..."
python3 -u load_data.py "$PROJECT" peerA 40
if [ $? -ne 0 ]; then
    echo "ERROR: load_data.py failed. Check logs/peerA.log"
    exit 1
fi
echo "    Done loading."

# Cleanup handler
cleanup() {
    echo ""
    echo "Stopping peerA (PID $PEER_A_PID)..."
    kill "$PEER_A_PID" 2>/dev/null
}
trap cleanup EXIT

echo ""
echo "================================================"
echo " peerA is running and loaded with 40 files."
echo " Now SSH into machine 2, copy all .py files"
echo " and shell scripts there, then run:"
echo ""
echo "   bash test_basic_machine2.sh $PROJECT"
echo ""
echo " Tailing peerA log below (Ctrl+C to stop)."
echo "================================================"
echo ""

tail -f logs/peerA.log
