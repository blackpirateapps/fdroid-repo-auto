# F-Droid Meta-Repository (GitHub Actions + GitHub Pages)

This repository builds and hosts a custom F-Droid repo on **GitHub Pages**.

The workflow:
1. Uses the **GitHub CLI** to fetch the *latest* release assets (`*.apk`) from multiple GitHub repositories (including **pre-releases**).
2. Runs `fdroid update --create-metadata` to generate missing metadata skeletons and build the signed index (`index-v1.jar`, `index.xml`).
3. Commits the results to the `gh-pages` branch (GitHub Pages serves from there).

## 1) Repo list

Edit `repos.txt` and list one repository per line:

```
my-org/my-app
someone-else/another-app
```

The workflow downloads `*.apk` assets from the latest non-draft release for each repo.

## 2) Generate a keystore locally (one-time)

Run:

```bash
keytool -genkeypair -v \
  -keystore fdroid-keystore.jks \
  -alias fdroid \
  -keyalg RSA -keysize 4096 \
  -validity 10000
```

Notes:
- Remember the **keystore password**, the **key password** (often same), and the **alias** (example above: `fdroid`).
- Keep `fdroid-keystore.jks` private.

## 3) Encode keystore for GitHub Secrets

Linux:

```bash
base64 -w0 fdroid-keystore.jks
```

macOS:

```bash
base64 fdroid-keystore.jks | tr -d '\n'
```

Copy the output and save it as a GitHub Actions secret.

## 4) Configure GitHub Pages

In your repo settings:
- **Pages → Build and deployment**
- Source: **Deploy from a branch**
- Branch: `gh-pages` (root)

Your repo URL in F-Droid will typically be:
`https://YOUR_GITHUB_USERNAME.github.io/YOUR_REPO_NAME/repo`

## 5) GitHub Secrets to set

Add these **Actions secrets** in repo settings:

### Required (signing)
- `FDROID_KEYSTORE_BASE64`: Base64-encoded `fdroid-keystore.jks`
- `FDROID_KEYSTORE_PASS`: keystore password
- `FDROID_KEY_ALIAS`: key alias (e.g. `fdroid`)
- `FDROID_KEY_PASS`: key password (can be same as keystore password)

### Required (repo identity)
- `FDROID_REPO_URL`: e.g. `https://YOUR_GITHUB_USERNAME.github.io/YOUR_REPO_NAME/repo`
- `FDROID_REPO_NAME`: display name in F-Droid client
- `FDROID_REPO_DESCRIPTION`: description shown in F-Droid client

### Optional (private source repos)
- `FDROID_GH_TOKEN`: a GitHub Personal Access Token (classic) with `repo` scope, if you need to download releases from **private** repositories.
  - If you only track public repos, you can omit this (the workflow falls back to `GITHUB_TOKEN`).

## 6) Metadata: how to customize

The workflow runs:

```bash
fdroid update --create-metadata
```

This creates skeleton metadata for apps that don’t already have it.

You can customize metadata on the `gh-pages` branch:
- `metadata/<applicationId>.yml`: primary app metadata (summary/description/etc).
- `metadata/<applicationId>/`: optional per-locale assets. Common layouts include:
  - `metadata/<applicationId>/en-US/icon.png`
  - `metadata/<applicationId>/en-US/phoneScreenshots/*.png`

Tip: After the first workflow run, open the generated files in `metadata/` and edit them as desired, then commit to `gh-pages`. Future runs will keep your edits and only update the repo index/APKs.

## Notes / caveats

- GitHub CLI prereleases: this setup selects the newest non-draft release via the GitHub API (which includes pre-releases), then downloads that tag’s `*.apk` assets with `gh release download`.
- “Private” repos + Pages: GitHub Pages is typically public. If you require private distribution, use an internal web host or a Pages-like solution that supports auth.

## 7) Run it

Trigger manually:
- GitHub → **Actions** → “Update F-Droid repo” → **Run workflow**

Or wait for the scheduled run (every 6 hours).
