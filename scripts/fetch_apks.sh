#!/usr/bin/env bash
set -euo pipefail

repos_file="${1:-repos.txt}"
dest_dir="${2:-repo}"
pattern="${APK_PATTERN:-*.apk}"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh (GitHub CLI) not found in PATH" >&2
  exit 2
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "jq not found in PATH" >&2
  exit 2
fi

mkdir -p "$dest_dir"

if [[ ! -f "$repos_file" ]]; then
  echo "Repos file not found: $repos_file" >&2
  exit 2
fi

while IFS= read -r line || [[ -n "$line" ]]; do
  repo="$(echo "$line" | sed -e 's/#.*$//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  [[ -z "$repo" ]] && continue

  echo "::group::Fetching $repo"

  # Fetch latest non-draft release (includes pre-releases by default via the API).
  # We intentionally keep the newest published/created release regardless of prerelease status.
  if ! releases_json="$(gh api -H "Accept: application/vnd.github+json" "/repos/$repo/releases?per_page=20")"; then
    echo "Failed to query releases for $repo; skipping."
    echo "::endgroup::"
    continue
  fi
  tag="$(
    echo "$releases_json" | jq -r '
      [ .[]
        | select(.draft | not)
        | { tag: .tag_name, ts: (.published_at // .created_at // "") }
      ]
      | sort_by(.ts)
      | reverse
      | .[0].tag // empty
    '
  )"

  if [[ -z "$tag" ]]; then
    echo "No non-draft releases found for $repo; skipping."
    echo "::endgroup::"
    continue
  fi

  echo "Latest release tag: $tag"
  gh release download -R "$repo" "$tag" \
    --pattern "$pattern" \
    --dir "$dest_dir" \
    --clobber

  echo "::endgroup::"
done <"$repos_file"
