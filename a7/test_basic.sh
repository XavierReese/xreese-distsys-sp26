#!/bin/bash
# test_basic.sh
#
# Basic 3-peer test for Assignment 7.
# Run from the directory containing all your .py files.
#
# This script runs on MACHINE 1 only.
# After it loads data, SSH into machine 2 and run test_basic_machine2.sh
#
# Usage: bash test_basic.sh <project_name>
# Example: bash test_basic.sh xreese01-a7

PROJECT=${1:?"Usage: bash test_basic.sh <project_name>"}

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

mkdir -p data logs

echo "================================================"
echo " A7 Basic Test (machine 1) — project: $PROJECT"
echo " Working dir: $SCRIPT_DIR"
echo "================================================"

# --- Step 1: Start peerA ---
# All peers run from the same directory. HashTable names its files
# table-peerA.ckpt / table-peerA.txn so peers don't collide.
echo "[1] Starting peerA..."
python3 -u Peer.py "$PROJECT" peerA > logs/peerA.log 2>&1 &
PEER_A_PID=$!
echo "    peerA PID: $PEER_A_PID"

echo "    Waiting 8s for peerA to register with catalog..."
sleep 8

# Sanity check — did the peer actually start?
if ! kill -0 "$PEER_A_PID" 2>/dev/null; then
    echo "ERROR: peerA failed to start. Check logs/peerA.log"
    exit 1
fi

# --- Step 2: Load test data ---
echo "[2] Loading 40 test files into peerA..."
python3 load_data.py "$PROJECT" peerA 40
echo "    Done loading."

echo ""
echo "================================================"
echo " peerA is running and loaded."
echo " Now SSH into machine 2, copy all .py files and"
echo " the shell scripts there, then run:"
echo ""
echo "   bash test_basic_machine2.sh $PROJECT"
echo ""
echo " Tailing peerA log below (Ctrl+C to stop peerA)."
echo "================================================"
echo ""

# Tail the log so you can watch activity as machine 2 connects
tail -f logs/peerA.log
