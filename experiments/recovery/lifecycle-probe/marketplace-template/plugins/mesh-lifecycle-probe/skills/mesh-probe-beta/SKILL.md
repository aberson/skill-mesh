---
name: mesh-probe-beta
description: Read exact lifecycle markers from this disposable plugin's shared reference and helper asset. Use when a request contains the unique trigger {{TRIGGER_BETA}}.
---

# Mesh Probe Beta

Instruction revision: {{RELEASE}}

1. Read `../../shared/probe-reference.md` relative to this file.
2. Read `../../assets/probe-helper.txt` relative to this file.
3. Return one line with this exact field order:

`BETA|run=<run_id>|version=<version>|reference=<reference_marker>|helper=<helper_marker>`

Copy each value exactly. Do not infer a missing value.
