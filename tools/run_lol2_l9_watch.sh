#!/usr/bin/env bash
set -euo pipefail

export OUT_DIR="${OUT_DIR:-/home/bob/lol2_out/dosbox_guest_trace_l9_watch_ready}"
export DOSBOX_GUEST_TRACE_WATCH_FILE='DAT\\L9_DR.MIX'
export DOSBOX_GUEST_TRACE_WATCH_SIZE=135
export DOSBOX_GUEST_TRACE_WATCH_WRITES=8
export DOSBOX_GUEST_TRACE_WATCH_READS=24
export TRACE_MODE="${TRACE_MODE:-guesttrace}"
export TIMEOUT_SECS="${TIMEOUT_SECS:-180}"

exec /home/bob/lol2_dosbox_guest_trace.sh
