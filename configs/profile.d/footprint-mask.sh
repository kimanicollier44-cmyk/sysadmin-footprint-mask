#!/usr/bin/env bash
# footprint-mask.sh — Shell Profile Configuration (as supplied).
# Controls shell history logging, preventing sensitive shell history
# from persisting to disk by forcing history into volatile
# memory (tmpfs).

# Disable permanent history
unset HISTFILE
export HISTSIZE=0
export HISTFILESIZE=0

# Disable core dumps to prevent memory leakage
ulimit -c 0

# Mask UMASK for strict file creation
umask 077
