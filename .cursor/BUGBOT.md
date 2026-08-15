# Bugbot review rules — hope-metrics-platform

Project review guidance for Cursor Bugbot. Process rules (git bans, step-gate) stay in `.cursor/rules/`.

## Language and secrets

- Flag non-English in committed docs, comments, or UI chrome meant for the public repo.
- Flag secrets in the diff: passwords, credentialed `DATABASE_URL`, absolute machine paths, private note paths.

## Architecture / product invariants

- Ingest owns append-only `raw_*`. dbt owns `stg_*` / `mart_*` publish path (`dbt build`). Flag docs or scripts that still treat `warehouse/*.sql` as SoT.
- Dashboard/API read marts; do not invent metrics in the UI that disagree with dbt grains.
- Probe stays in this repo; device simulator stays in a separate repo. Flag attempts to vendor a generator tree here.
- Idle cutoff / US-Eastern day grain are product locks; flag silent changes without an explicit decision.

## Code quality

- Prefer focused diffs. Flag unrelated refactors bundled with feature work.
- Match bland engineering tone; flag marketing filler, emoji, and tutorial padding in READMEs.
- Flag setup docs that omit required steps (e.g. `dbt build` without profiles, deploy without transform apply).
- Flag empty `except:` / broad swallow without logging in ingest or scripts.
