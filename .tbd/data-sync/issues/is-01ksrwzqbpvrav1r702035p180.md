---
type: is
id: is-01ksrwzqbpvrav1r702035p180
title: "CI/publish: bump GitHub Actions to Node 24-capable versions (checkout@v6, setup-uv@v8.1.0)"
kind: task
status: closed
priority: 1
version: 5
labels: []
dependencies:
  - type: blocks
    target: is-01ksrx01vtyypaf37nj3tz6tvr
created_at: 2026-05-29T03:38:28.597Z
updated_at: 2026-05-29T04:00:31.473Z
closed_at: 2026-05-29T04:00:31.472Z
close_reason: "Merged in PR #55: checkout@v6 + setup-uv@v8.1.0 in ci.yml/publish.yml; validated by CI"
---
Source: comparison with jlevy/simple-modern-uv template (already vetted versions).
In BOTH .github/workflows/ci.yml and publish.yml:
- actions/checkout@v4 -> @v6
- astral-sh/setup-uv@v5 -> @v8.1.0 (exact immutable tag; v8+ no longer publishes floating @v8 tags, so pin the full version and bump explicitly).
Why: GitHub force-migrates Node 20 actions to Node 24 on 2026-06-02; v4/v5 emit deprecation warnings and may break. Template already runs v6/v8.1.0.
Note: subject to SUPPLY-CHAIN-SECURITY.md (cool-off + pinning); these versions are long-established and match the canonical template.
