# Morphe AutoBuilds

Fork of [RookieEnough/Morphe-AutoBuilds](https://github.com/RookieEnough/Morphe-AutoBuilds) for personal use. A GitHub Actions pipeline downloads stock APKs, applies [Morphe](https://github.com/MorpheApp) patch bundles, and publishes signed APKs to a single rolling release. Builds run daily at 06:00 UTC.

[Download the latest release](https://github.com/hxreborn/Morphe-AutoBuilds/releases/latest)

## Apps

| App | Patch bundle | APK source | Version | Arch |
| :-- | :-- | :-- | :-- | :-- |
| TikTok | [hxreborn/tiktok-patches-for-morphe](https://github.com/hxreborn/tiktok-patches-for-morphe) | GitHub mirror | 43.8.3 | arm64-v8a |
| Showly | [hxreborn/morphe-patches](https://github.com/hxreborn/morphe-patches) | APKMirror | latest | universal |
| Projectivy | [hxreborn/morphe-patches](https://github.com/hxreborn/morphe-patches) | APKPure | latest | universal |
| Forus | [hxreborn/morphe-patches](https://github.com/hxreborn/morphe-patches) | APKPure | latest | universal |
| Proton VPN | [Paresh-Maheshwari/paresh-patches](https://gitlab.com/Paresh-Maheshwari/paresh-patches) | APKMirror | 5.19.16.0 | universal |
| SAI | [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches) | APKPure | 2.2.8 | universal |
| Speedtest | [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches) | APKPure | 7.0.7 | universal |
| Splitwise | [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches) | Uptodown | 26.7.2 | universal |
| Send Files To TV | [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches) | APKPure | 1.4.22 | universal |
| Torrent Search Revolution V2 | [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches) | APKPure | 2.3.3 | universal |
| Parcels | [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches) | APKPure | 3.0.11 | universal |
| Network Guru | [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches) | APKPure | 1.9-beta5 | universal |
| SofaScore | [arandomhooman/hoomans-morphe-patches](https://github.com/arandomhooman/hoomans-morphe-patches) | APKMirror | 26.06.23 | universal |

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
