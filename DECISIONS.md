# Decision index

[Actual CPU retrieval](docs/adr/001-actual-cpu.md) fixes model identity and thread bounds.

[Open-loop comparison](docs/adr/002-open-loop.md) fixes arrivals, denominator, routing and client refusal.

[Public boundary](docs/adr/003-public-boundary.md) fixes session persistence and separates visitor checks from execution.

Package layout uses one small Python package, scaleproof/, rather than empty domain packages. Import-boundary tests enforce the public/private separation. Tests are grouped by contract in tests/ rather than creating empty directories.
