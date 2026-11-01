# Maintaining SKST Canva Studio

Canonical repository: https://github.com/taikhoanzaizai-ux/canva . Work from this repository for future changes. Do not publish local voice, video, scripts, credentials, pairing codes, project state or machine-specific logs.

For every user-visible fix: increment the three-part VERSION in canva_studio/core.py; keep the companion manifest version aligned if its code changes; add a concise Vietnamese entry in CHANGELOG.md. Push authorized completed changes to main. The GitHub Actions workflow tests, builds and publishes a versioned GitHub Release if that version does not already exist. Never replace an existing release's code under the same version.

Run `python -m unittest discover -s tests -v` and `node tests/test_adapter.cjs`. For Windows build, use `python scripts/build_release.py`. Check packaged `--self-test` including pairing-code persistence and copy before release. For updater changes, test invalid checksums, archive traversal, ignored/draft releases, version selection, file preservation and rollback.

The updater must only use published releases from the fixed repository, require GitHub's SHA-256 digest, preserve user data, reject unsafe archive paths, and recover the previous version after install/startup failure. No credentials or update service beyond GitHub. Keep Canva UI changes confined to the DOM adapter. Never claim live Canva verification from fixtures or smoke tests.

Storage is portable from 0.2.1: Data, Temp, Cache, update downloads and backups stay beside the executable. Build onedir, never onefile (which extracts into system Temp). Keep runtime updates restricted to explicitly validated _internal names, reject traversal and never include Data in release ZIPs. Do not silently fall back to AppData when the install folder is read-only. Import legacy AppData non-destructively. Full Windows ZIP is required once when moving from 0.2.0 to the new onedir layout.

