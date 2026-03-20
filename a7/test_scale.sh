#!/bin/bash
# test_scale.sh
#
# Staged scale test for Assignment 7.
# Starts peers in waves: 1, then 2 more, then 4 more (7 total).
# All peers on THIS machine for simplicity, using separate directories.
#
# If you want to spread peers across machines, see the comments below
# marked [MULTI-MACHINE].
#
# Usage: bash test_scale.sh <project_name>
#
# Example: bash test_scale.sh xreese-a7-scale

set -e

PROJECT=${1:?"Usage: bash test_scale.sh <project_name>"}

SCRIPT_DIR=$(pwd)
LOG_DIR="$SCRIPT_DIR/logs_scale"
mkdir -p "$LOG_DIR"

# Keep track of all background PIDs so we can kill them on exit
PIDS=()

cleanup() {
    echo ""
    echo "Stopping all peers..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    echo "All peers stopped. Logs are in $LOG_DIR/"
}
trap cleanup EXIT

start_peer() {
    local name=$1
    mkdir -p "$SCRIPT_DIR/peer_${name}/data"
    (cd "$SCRIPT_DIR/peer_${name}" && python3 ../Peer.py "$PROJECT" "$name" 2>&1 | tee "$LOG_DIR/${name}.log") &
    local pid=$!
    PIDS+=($pid)
    echo "    Started $name (PID $pid)"
}

echo "================================================"
echo " A7 Scale Test — project: $PROJECT"
echo "================================================"

# --- Stage 1: peerA alone ---
echo ""
echo "[Stage 1] Starting peerA..."
start_peer peerA
echo "    Waiting 10s for peerA to register..."
sleep 10

echo "    Loading 40 test files into peerA..."
python3 load_data.py "$PROJECT" peerA 40
echo "    Done. Waiting 30s so peerA is stable before adding peers..."
sleep 30

# --- Stage 2: add peerB and peerC ---
echo ""
echo "[Stage 2] Adding peerB and peerC..."
start_peer peerB
start_peer peerC
echo "    Waiting 60s to observe syncing at 2-peer stage..."
sleep 60

# --- Stage 3: add peerD, peerE, peerF, peerG ---
echo ""
echo "[Stage 3] Adding peerD, peerE, peerF, peerG..."
start_peer peerD
start_peer peerE
start_peer peerF
start_peer peerG
echo "    Waiting 90s to observe syncing at 7-peer stage..."
sleep 90

echo ""
echo "================================================"
echo " Scale test complete."
echo " All 7 peers ran. Logs are in $LOG_DIR/"
echo " Review logs to reconstruct the connection diagram."
echo "================================================"
