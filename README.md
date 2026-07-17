# Morphe AutoBuilds

Fork of [RookieEnough/Morphe-AutoBuilds](https://github.com/RookieEnough/Morphe-AutoBuilds), trimmed to the apps I use. A GitHub Actions pipeline downloads stock APKs, applies [Morphe](https://github.com/MorpheApp) patch bundles, and publishes signed APKs to a single rolling release. Builds run daily at 06:00 UTC.

[Download the latest release](https://github.com/hxreborn/Morphe-AutoBuilds/releases/latest)

## Apps

| App | Patch bundle | APK source | Arch |
| :-- | :-- | :-- | :-- |
| TikTok | [hxreborn/tiktok-patches-for-morphe](https://github.com/hxreborn/tiktok-patches-for-morphe) | APKMirror, pinned to 43.8.3 | arm64-v8a |
| Showly | [hxreborn/morphe-patches](https://github.com/hxreborn/morphe-patches) | APKMirror | universal |
| Projectivy | [hxreborn/morphe-patches](https://github.com/hxreborn/morphe-patches) | APKPure | universal |
| Forus | [hxreborn/morphe-patches](https://github.com/hxreborn/morphe-patches) | APKPure | universal |

## Running locally

Needs Python 3.11+, a JRE, and `apksigner`.

```bash
pip install -r requirements.txt
APP_NAME=tiktok SOURCE=hxreborn-tiktok python -m src
```

## Workflows

| Workflow | Trigger | What it does |
| :-- | :-- | :-- |
| `patch.yml` | Daily, 06:00 UTC | Builds everything in `patch-config.json`, updates the rolling release |
| `manual-patch.yml` | Manual | Build a single app, arch, or pinned version |
| `sync-upstream.yml` | Weekly | Opens a PR when upstream has new commits |
| `generate-configs.yml` | Manual | Scaffolds `apps/` config files |

## Disclaimer

Not affiliated with the Morphe project. The pipeline patches stock APKs with public patch bundles. Use at your own risk.

[License](LICENSE)
