# Autonomous synthetic pipeline

Run from Toolkit root:

    python scripts/validate_data_engineering.py
    python -m unittest discover -s tests -p test_data_engineering.py -v

Three synthetic event batches contain a late arrival. Correct full and incremental runs must match independently declared totals. Repeated batches, a mid-batch failure and synthetic reprocessing cannot duplicate events or advance an uncommitted checkpoint.

The broken_cases.json file contains 25 deliberately corrupted variants, checked by the same independent auditor that accepts the good reference. Only Python standard library and in-memory dictionaries are used. No network, databases, production user data, installation, secrets or billable services.

Demonstrated properties are LOCAL and SYNTHETIC ONLY. Real source accuracy, real-storage atomicity, actual client compatibility, distributed exactly-once and production performance are NOT_MEASURED.
