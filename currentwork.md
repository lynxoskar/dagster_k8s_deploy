Current Work Summary

Overview
- Deployed the stack to local Kubernetes using the uv CLI (`cli.py`).
- Addressed multiple startup issues across webserver, A/B gRPC pods, and git-sync.
- Added helper `readlog.py` uv script to tail logs.

Key Issues Found and Fixes
1) Invalid resource names (DNS-1123)
- Problem: Uppercase names for A/B resources (`dagster-grpc-A/B`) are invalid.
- Fix: Renamed to lowercase `dagster-grpc-a` and `dagster-grpc-b`, and updated webserver workspace ConfigMap hosts accordingly.

2) Webserver CrashLoop due to subPath mount as file
- Problem: Mounting ConfigMap `workspace.yaml` directly to `/opt/dagster/dagster_home/workspace.yaml` caused "not a directory" during subPath mount.
- Fix: Mount workspace ConfigMap at `/opt/dagster/workspace/workspace.yaml` and point dagster-webserver to that path. Updated both webserver and daemon manifests.

3) git-sync sidecar failures
- Problems:
  - Placeholder/invalid repo URLs; deprecated `--branch` flag; attempted sync into code root with existing files leading to permission errors.
- Fixes:
  - Parameterized git-sync image and repo/refs via `configvalues.yaml` (`images.git_sync`, `environment.repo_url_a/b`, `environment.repo_ref_a/b`).
  - Switched to `--ref` and created a dedicated git-sync root `/opt/dagster/app/repo` to avoid wiping app files.
  - Added initContainer to create minimal `playground` package and `workspace.yaml`, and to grant git-sync write permissions to `/opt/dagster/app/repo`.

4) dagster-grpc container argument issues
- Problems:
  - A used `python -m debugpy` (debugpy not installed in base image).
  - Used `-w` flag incorrectly for `dagster api grpc` (should specify module or file, not workspace path).
- Fixes:
  - Use `dagster api grpc -m playground.definitions -d /opt/dagster/app` to load the bootstrap module reliably.
  - Set `PYTHONPATH=/opt/dagster/app` for gRPC containers.

5) Status after fixes
- Webserver: Running.
- Postgres: Running.
- B gRPC: Reached Running state (2/2) during iteration, then redeployed with new flags; rollout succeeded.
- A gRPC: Logs confirmed git-sync succeeded; gRPC initially failed due to `-w` flag; updated to `-m`+`-d` to fix.
- Daemon: CrashLoopBackOff persists; not yet investigated in depth (likely DB/instance config or migrations). Needs logs review.

Helper Tooling
- CLI: `cli.py` (uv script)
  - `uv run cli.py validate` — sanity checks
  - `uv run cli.py generate --force` — generate manifests to `deploy/`
  - `uv run cli.py deploy` — apply manifests (select components via `--components`)
- Logs: `readlog.py` (uv script)
  - `uv run readlog.py follow -l app=dagster-webserver`
  - `uv run readlog.py follow -l app=dagster-grpc-a -c dagster-grpc`
  - `uv run readlog.py follow -l app=dagster-grpc-a -c git-sync`

Open Tasks / Next Steps
- Inspect `dagster-daemon` logs and fix CrashLoop (DB connectivity, instance config, or schema/migrations).
- Decide on git-sync auth: add SSH Secret and flags for private repos; currently using public HTTPS.
- Add readiness/liveness probes and resource requests/limits for all pods.
- Parameterize git `--root` integration to actually load code from the synced repo (currently loading only bootstrap `playground` to ensure startup).
- Update README to reflect uv scripts and lowercased names, and the new git-sync parameters.
- Optional: split A/B into separate namespaces and/or databases as originally documented.

Notes
- Current defaults in `configvalues.yaml` set A/B `repo_url_*` to this repo on `master` for local testing.
- git-sync image updated to `registry.k8s.io/git-sync/git-sync:v4.2.4`.
