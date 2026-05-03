#!/bin/bash
echo "=== Memory ==="
free -m
echo ""
echo "=== Bot process ==="
ps aux | grep "run.py" | grep -v grep
echo ""
echo "=== Top memory processes ==="
ps aux --sort=-%mem | head -10
