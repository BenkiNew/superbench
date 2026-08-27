#!/usr/bin/env bash
# compute_agreement.sh — compare two independent AI review passes and decide
# whether the "Узгодження" (agreement) badge on the dashboard should read
# agreed or conflict.
set -euo pipefail
REVIEWER_A="${1:?reviewer A findings json}"
REVIEWER_B="${2:?reviewer B findings json}"

agreement="$(jq -n --slurpfile a "$REVIEWER_A" --slurpfile b "$REVIEWER_B" '
  [ $a[0].findings[] | [.id,.severity,.repo,.file,.line] ] as $x |
  [ $b[0].findings[] | [.id,.severity,.repo,.file,.line] ] as $y |
  if $x==$y then "agreed" else "conflict" end
')"
agreement="${agreement//\"/}"
echo "agreement=$agreement"
