#!/bin/bash
# test_basic.sh
#
# Basic 3-peer test for Assignment 7.
#
# Run this script from the directory containing all your .py files.
# It starts peerA on THIS machine, loads 40 files into it, then
# prints instructions for starting peerB and peerC on a second machine.
#
# Usage: bash test_basic.sh <project_name> <machine2_hostname>
#
# Example: bash test_basic.sh xreese-a7 student02.cse.nd.edu

set -e  # exit on any error

PROJECT=${1:?"Usage: bash test_basic.sh <project_name> <machine2_hostname>"}
MACHINE2=${2:?"Usage: bash test_basic.sh <project_name> <machine2_hostname>"}

SCRIPT_DIR=$(pwd)
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

echo "================================================"
echo " A7 Basic Test — project: $PROJECT"
echo "================================================"

# --- Step 1: Start peerA in its own data directory ---
echo "[1] Starting peerA..."
mkdir -p "$SCRIPT_DIR/peer_peerA/data"
cd "$SCRIPT_DIR/peer_peerA"
python3 ../Peer.py "$PROJECT" peerA 2>&1 | tee "$LOG_DIR/peerA.log" &
PEER_A_PID=$!
cd "$SCRIPT_DIR"

echo "    peerA PID: $PEER_A_PID"
echo "    Waiting 8 seconds for peerA to register with catalog..."
sleep 8

# --- Step 2: Load 40 test files into peerA ---
echo "[2] Loading 40 test files into peerA..."
python3 load_data.py "$PROJECT" peerA 40
echo "    Done loading. Waiting 5 seconds before starting other peers..."
sleep 5

# --- Step 3: Instructions for machine 2 ---
echo ""
echo "================================================"
echo " Now SSH into $MACHINE2 and run:"
echo ""
echo "   bash test_basic_machine2.sh $PROJECT"
echo ""
echo " Logs will appear in logs/ on that machine."
echo " When done, come back here and press Ctrl+C to stop peerA."
echo "================================================"
echo ""
echo "[3] peerA is running. Tailing log (Ctrl+C to stop)..."
tail -f "$LOG_DIR/peerA.log"
