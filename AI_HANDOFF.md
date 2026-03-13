# AI Handoff: `fdroid-repo-auto`

## What this repo does

This repository is a “meta” F-Droid repo builder:
- Downloads APK release assets (`*.apk`) from a list of GitHub repos (`repos.txt`) using `gh release download`.
- Runs `fdroid update --create-metadata` to:
  - generate missing app metadata skeletons
  - produce a signed F-Droid index (`index-v1.jar`, `index.xml`)
- Publishes the resulting F-Droid repo via GitHub Pages by committing artifacts to the `gh-pages` branch.

The main branch contains the automation and templates; the `gh-pages` branch contains the hosted output (`repo/`, `metadata/`, etc.).

## Key files

- `.github/workflows/update.yml`: scheduled + manual workflow that builds and publishes the F-Droid repo to `gh-pages`.
- `repos.txt`: one `OWNER/REPO` per line to track for APK assets.
- `scripts/fetch_apks.sh`: picks the newest non-draft release (including pre-releases) and downloads `*.apk` assets.
- `scripts/restore_keystore.sh`: decodes the Base64 keystore secret into a file for fdroidserver to use.
- `config.yml.example`: template describing the fdroidserver config keys; CI writes the real `site/config.yml` at runtime from secrets.
- `README.md`: setup steps (Pages, secrets, keystore generation, metadata notes).

## How the workflow publishes

The workflow uses a git worktree:
- Checks out `main` as normal.
- Adds a worktree at `site/` pointing to `gh-pages` (creating the branch if missing).
- Writes generated content into `site/repo` + `site/metadata`.
- Runs `fdroid update` inside `site/`.
- Removes `site/config.yml` and `site/keystore.jks` before committing.
- Commits and pushes to `gh-pages`.

## Required GitHub Secrets

Signing:
- `FDROID_KEYSTORE_BASE64`: Base64-encoded `*.jks`
- `FDROID_KEYSTORE_PASS`
- `FDROID_KEY_ALIAS`
- `FDROID_KEY_PASS` (can match keystore password)

Repo identity:
- `FDROID_REPO_URL` (usually `https://<user>.github.io/<repo>/repo`)
- `FDROID_REPO_NAME`
- `FDROID_REPO_DESCRIPTION`

Optional:
- `FDROID_GH_TOKEN`: PAT if downloading release assets from private repositories.

## Metadata customization

`fdroid update --create-metadata` creates skeletons when missing.

Custom edits should be made on `gh-pages`:
- `metadata/<applicationId>.yml` (summary/description/etc.)
- `metadata/<applicationId>/...` (icons/screenshots, locale-specific assets as supported by your fdroidserver version)

The workflow keeps and reuses existing metadata; it only regenerates missing skeletons.

## Common failure modes / debugging

- **No APKs downloaded**: verify `repos.txt` entries and that the release assets actually include `*.apk` (or set `APK_PATTERN` in the workflow env if you need a different pattern).
- **Private repo download failures**: set `FDROID_GH_TOKEN` with access to those repos.
- **Signing errors**: ensure alias/passwords match the keystore; regenerate keystore if unsure.
- **Pages not serving**: ensure GitHub Pages is configured to deploy from `gh-pages` (root).

To debug a workflow run, look at logs for:
- “Download latest APK assets…” step (per-repo grouping)
- `fdroid update` output
- final “Commit and push…” step

## Next steps / customization

- Populate `repos.txt` with your actual `OWNER/REPO` list.
- Optional: add a repo icon and reference it from config (or extend CI to copy it into `gh-pages`).
- Optional: pin apt package versions or move to a container if you need full reproducibility.

