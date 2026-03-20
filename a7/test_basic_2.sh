#!/bin/bash
# test_basic_machine2.sh
#
# Run on machine 2 AFTER test_basic.sh is running on machine 1
# and peerA has been loaded with data.
#
# Starts peerB and peerC simultaneously so they discover each other
# and demonstrate peer-to-peer communication between new peers.
#
# Usage: bash test_basic_machine2.sh <project_name>
#
# Example: bash test_basic_machine2.sh xreese-a7

set -e

PROJECT=${1:?"Usage: bash test_basic_machine2.sh <project_name>"}

SCRIPT_DIR=$(pwd)
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

echo "================================================"
echo " A7 Basic Test (machine 2) — project: $PROJECT"
echo "================================================"

# Create separate data directories for each peer so their
# checkpoint/log files and data/ folders don't collide
mkdir -p "$SCRIPT_DIR/peer_peerB/data"
mkdir -p "$SCRIPT_DIR/peer_peerC/data"

# --- Start peerB and peerC at the same time ---
# The & runs each in the background. We capture PIDs so we can
# cleanly shut them down later.
echo "[1] Starting peerB and peerC simultaneously..."

(cd "$SCRIPT_DIR/peer_peerB" && python3 ../Peer.py "$PROJECT" peerB 2>&1 | tee "$LOG_DIR/peerB.log") &
PEER_B_PID=$!

(cd "$SCRIPT_DIR/peer_peerC" && python3 ../Peer.py "$PROJECT" peerC 2>&1 | tee "$LOG_DIR/peerC.log") &
PEER_C_PID=$!

echo "    peerB PID: $PEER_B_PID"
echo "    peerC PID: $PEER_C_PID"
echo ""
echo "Logs are being written to:"
echo "  $LOG_DIR/peerB.log"
echo "  $LOG_DIR/peerC.log"
echo ""
echo "Tailing both logs below. Press Ctrl+C when done (runs ~2 min)."
echo "================================================"

# Show both logs interleaved. The label shows which peer each line is from.
tail -f "$LOG_DIR/peerB.log" "$LOG_DIR/peerC.log"
