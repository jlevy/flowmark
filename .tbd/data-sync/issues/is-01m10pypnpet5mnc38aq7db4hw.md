---
type: is
id: is-01m10pypnpet5mnc38aq7db4hw
title: "Decide whether to split the .tbd/config.yml f06 to f08 upgrade out of PR #71"
kind: task
status: open
priority: 3
version: 1
labels: []
dependencies: []
created_at: 2026-08-27T04:16:51.894Z
updated_at: 2026-08-27T04:16:51.894Z
---
Review suggestion from PR #71 (jlevy/flowmark#71): 'Split the unrelated .tbd/config.yml format upgrade if practical, so the preservation review remains focused.'

Still bundled at head 783b445; the upgrade rides in commit 94f9a78. The earlier review response deferred this pending the author's agreement, noting it needs either a history rewrite of the branch or a follow-up revert-and-reapply.

Author decision needed: leave it bundled, or lift it onto its own PR.
