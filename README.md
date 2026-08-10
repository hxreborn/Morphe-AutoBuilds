# Morphe AutoBuilds

Fork of [RookieEnough/Morphe-AutoBuilds](https://github.com/RookieEnough/Morphe-AutoBuilds) for personal use. A GitHub Actions pipeline downloads stock APKs, applies [Morphe](https://github.com/MorpheApp) patch bundles, and publishes signed APKs to a single rolling release. Builds run daily at 06:00 UTC.

[Download the latest release](https://github.com/hxreborn/Morphe-AutoBuilds/releases/latest)

## Apps

| App | Patch bundle | APK source | Version | Arch |
| :-- | :-- | :-- | :-- | :-- |
| TikTok | [hxreborn/tiktok-patches-for-morphe](https://github.com/hxreborn/tiktok-patches-for-morphe) | GitHub mirror | 46.2.3 | arm64-v8a |
| Showly | [hxreborn/morphe-patches](https://github.com/hxreborn/morphe-patches) | APKMirror | latest | arm64-v8a |
| Projectivy | [hxreborn/morphe-patches](https://github.com/hxreborn/morphe-patches) | APKPure | latest | arm64-v8a |
| Forus | [hxreborn/morphe-patches](https://github.com/hxreborn/morphe-patches) | APKPure XAPK | latest | arm64-v8a |
| Proton Mail | [hxreborn/morphe-patches](https://github.com/hxreborn/morphe-patches) | APKMirror | 4.15.0 | arm64-v8a |
| Proton VPN | [Paresh-Maheshwari/paresh-patches](https://gitlab.com/Paresh-Maheshwari/paresh-patches) | APKMirror | 5.19.16.0 | arm64-v8a |
| SAI | [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches) | APKPure | 2.3.1 | arm64-v8a |
| Speedtest | [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches) | APKPure | 7.0.7 | arm64-v8a |
| Splitwise | [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches) | APKPure | 26.7.2 | arm64-v8a |
| Send Files To TV | [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches) | APKPure | 1.4.22 | arm64-v8a |
| Parcels | [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches) | APKPure | 3.0.11 | arm64-v8a |
| Network Guru | [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches) | APKPure XAPK | 1.9-beta5 | arm64-v8a |
| SofaScore | [arandomhooman/hoomans-morphe-patches](https://github.com/arandomhooman/hoomans-morphe-patches) | APKMirror | 26.06.23 | arm64-v8a |

The release only publishes standalone APKs that pass signature, split-manifest,
and native ABI validation for `arm64-v8a`.

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
