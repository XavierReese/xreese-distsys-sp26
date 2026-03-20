#!/bin/bash
# test_scale.sh
#
# Staged scale test: starts peers in waves (1 → 3 → 7).
# All peers run from the same directory.
# Run from the directory containing all your .py files.
#
# Usage: bash test_scale.sh <project_name>
# Example: bash test_scale.sh xreese01-a7-scale

# Wipe previous run's data so peers start fresh
rm -rf data/ table-*.ckpt table-*.txn
mkdir -p data

PROJECT=${1:?"Usage: bash test_scale.sh <project_name>"}

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

mkdir -p data logs_scale

PIDS=()

# Kill all peers cleanly on exit or Ctrl+C
cleanup() {
    echo ""
    echo "Stopping all peers..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    echo "Done. Logs are in logs_scale/"
}
trap cleanup EXIT

start_peer() {
    local name=$1
    python3 -u Peer.py "$PROJECT" "$name" > "logs_scale/${name}.log" 2>&1 &
    local pid=$!
    PIDS+=($pid)
    echo "    Started $name (PID $pid)"
    sleep 1
    if ! kill -0 "$pid" 2>/dev/null; then
        echo "    WARNING: $name may have failed. Check logs_scale/${name}.log"
    fi
}

echo "================================================"
echo " A7 Scale Test — project: $PROJECT"
echo " Working dir: $SCRIPT_DIR"
echo "================================================"

# --- Stage 1: peerA alone ---
echo ""
echo "[Stage 1] Starting peerA..."
start_peer peerA

echo "    Waiting 10s for peerA to register with catalog..."
sleep 10

echo "    Loading 40 test files into peerA..."
python3 load_data.py "$PROJECT" peerA 40
echo "    Done loading. Waiting 30s before adding more peers..."
sleep 30

# --- Stage 2: add peerB and peerC ---
echo ""
echo "[Stage 2] Adding peerB and peerC..."
start_peer peerB
start_peer peerC
echo "    Waiting 60s to observe 3-peer syncing..."
sleep 60

# --- Stage 3: add peerD, peerE, peerF, peerG ---
echo ""
echo "[Stage 3] Adding peerD, peerE, peerF, peerG..."
start_peer peerD
start_peer peerE
start_peer peerF
start_peer peerG
echo "    Waiting 90s to observe 7-peer syncing..."
sleep 90

echo ""
echo "================================================"
echo " Scale test complete. All 7 peers ran."
echo " Run:  python3 parse_logs.py logs_scale/"
echo " to extract the connection diagram data."
echo "================================================"
