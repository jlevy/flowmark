---
type: is
id: is-01m1npp7a9x2vf2ch09tm1542k
title: Publish and verify flowmark 0.8.0
kind: task
status: closed
priority: 1
version: 2
labels:
  - release
dependencies: []
parent_id: is-01m1nn494vyzy4w2jqzqdtxxhp
created_at: 2026-09-04T07:56:17.096Z
updated_at: 2026-09-04T11:41:41.322Z
closed_at: 2026-09-04T11:41:41.322Z
close_reason: "Completed: GitHub v0.8.0 release https://github.com/jlevy/flowmark/releases/tag/v0.8.0 points to 7dfd042; trusted publish run https://github.com/jlevy/flowmark/actions/runs/33868862240 passed tests, pin guard, build, and PyPI upload. PyPI 0.8.0 is unyanked; wheel SHA-256 628c9f52b63cdfb78112196ae68c36f6107cc2ee0afdd55d631242a7eb9d15da matches the pre-release build; sdist SHA-256 121f89edb8fca09d3b0d72716e53671457b5ed909eb21c17120ec5850bf053c1 was downloaded, verified, source-built, and smoke-tested. Both flowmark and flowmark-py uvx entrypoints report v0.8.0."
resolution: null
duplicate_of: null
---
After flowmark-rs 0.4.0 is published and resolvable, create the documented v0.8.0 GitHub release/tag, watch the publish workflow, verify PyPI metadata and hashes, and smoke-test both the wheel-installed CLI/library and pinned uvx invocation.
