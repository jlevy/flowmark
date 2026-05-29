---
type: is
id: is-01ksrwzbtz285t201cs709fxde
title: "publish.yml: use 'uv sync --all-extras --frozen' to match ci.yml and SUPPLY-CHAIN-SECURITY.md"
kind: task
status: in_progress
priority: 2
version: 4
labels: []
dependencies:
  - type: blocks
    target: is-01ksrx01vtyypaf37nj3tz6tvr
created_at: 2026-05-29T03:38:16.798Z
updated_at: 2026-05-29T03:52:14.755Z
---
Source: flowmark ci.yml already uses 'uv sync --all-extras --frozen' per SUPPLY-CHAIN-SECURITY.md, but publish.yml uses 'uv sync --all-extras' (re-resolves). Make publish.yml frozen too so the published artifact is built from the locked, vetted dependency set. One-line change in .github/workflows/publish.yml.
