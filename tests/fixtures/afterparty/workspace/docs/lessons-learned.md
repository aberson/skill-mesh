# Lessons learned (acceptance fixture)

## Quote the gate command exactly

A retyped gate command dropped a flag, so the run reported green without running the
suite. Copy the command from the project instructions instead of retyping it.

## Measure before claiming

A report claimed a size reduction from output length alone. Line and character counts
are storage measures; they are not token counts or savings.
