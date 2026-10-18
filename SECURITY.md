# Security and private materials

Report security issues privately through the maintainer's GitHub profile contact options rather than by publishing credentials in issues.

Agent skills are instructions and may point to executable scripts. Metadata validity does not mean that running external code is safe. Review third-party code, permissions, network actions and data handling before execution.

**Never commit:** private API keys, cookies, tokens, production data, personal license texts or personally licensed Make Feature archives. The opt-in Make Feature skill source is included with its own notices; personally issued license documents and identifiers are not included.

Public repository history persists even after deletion: rotate exposed credentials and follow GitHub's secret-removal guidance if an accidental commit occurs.


## Automated publication checks

`python scripts/check_public_package.py` is a basic offline safeguard.
It now rejects linked files, environment files and disallowed binaries and
uses high-confidence signatures for select private keys and provider tokens.
It reports only file paths and rule names, never a matched credential.

**Limitations:** The patterns are neither complete nor proof that no secrets
exist. Binary contents, renamed credentials, obfuscated values and external
dependencies require independent review and dedicated secret scanning.
Never run untrusted skill scripts merely to determine whether they are safe.
