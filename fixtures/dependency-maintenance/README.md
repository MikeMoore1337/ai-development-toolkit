# Synthetic dependency-maintenance models

Two fictional upgrade assessments, plus 20 distinct mutated fixtures.
No real advisories, CVEs, registries, published release notes, installed packages or production evidence.
Run `python scripts/validate_dependency_maintenance.py` and
`python -m unittest tests/test_dependency_maintenance.py` from the repository.
The oracle only supports simple three-part numeric fixture versions and normalized graphs.
