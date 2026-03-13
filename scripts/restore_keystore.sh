#!/usr/bin/env bash
set -euo pipefail

out_path="${1:-keystore.jks}"

if [[ -z "${FDROID_KEYSTORE_BASE64:-}" ]]; then
  echo "FDROID_KEYSTORE_BASE64 is not set" >&2
  exit 2
fi

mkdir -p "$(dirname "$out_path")"

if command -v base64 >/dev/null 2>&1; then
  printf '%s' "$FDROID_KEYSTORE_BASE64" | base64 --decode >"$out_path"
else
  python3 - <<'PY' >"$out_path"
import base64, os, sys
data = os.environ.get("FDROID_KEYSTORE_BASE64", "")
sys.stdout.buffer.write(base64.b64decode(data))
PY
fi

chmod 600 "$out_path"
echo "Wrote keystore to $out_path"

