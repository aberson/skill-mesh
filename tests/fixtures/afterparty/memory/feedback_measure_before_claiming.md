---
name: Measure before claiming
description: Count lines and characters directly; never call them tokens or savings.
type: feedback
---

Measure a file directly before claiming it shrank or grew.

**Why:** a sweep once reported a reduction inferred from output length.

**How to apply:** record entry and exit counts for the same files, and say "not
measured" when a number is not available.
