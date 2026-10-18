# Clear Voice installation

Install the complete directory with the Toolkit installer (dry-run first):

```bash
python scripts/install.py --target /path/to/repo --profile editorial
python scripts/install.py --target /path/to/repo --profile editorial --apply
```

A generic standalone installation may copy `clear-voice/` into the agent client's supported skills directory. Confirm discovery in the actual client; installation does not imply activation. For embedding into a writing worker, review `adapters/editorial-worker/README.md`. Never deploy, overwrite existing prompts or alter structured schemas without repository-specific approval.
