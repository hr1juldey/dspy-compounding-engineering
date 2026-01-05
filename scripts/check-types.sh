#!/bin/bash
# Type checking with pyrefly
# Usage: ./scripts/check-types.sh [--strict]

STRICT_MODE=${1:-""}

echo "🔍 Checking types with pyrefly..."
echo ""

uvx pyrefly check --summarize-errors

ERROR_COUNT=$?

if [ "$ERROR_COUNT" -ne 0 ]; then
  echo ""
  echo "⚠️  Type errors detected!"
  echo ""

  if [ "$STRICT_MODE" = "--strict" ]; then
    echo "❌ STRICT MODE: Blocking commit due to type errors"
    exit 1
  else
    echo "ℹ️  INFORMATIONAL MODE: Type errors logged but commit allowed"
    echo "Run with --strict flag to block commits on type errors"
    exit 0
  fi
fi

echo ""
echo "✅ All types check out!"
exit 0
