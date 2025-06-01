#!/bin/sh
# system-disk-usage-filter.sh

du -h -d 1 2>/dev/null | grep -v "Permission denied" | awk '$1 ~ /[0-9.]+[GTP]/ || ($1 ~ /[0-9.]+M/ && $1+0 > 500)'
