# ChatGPT routing evidence receipt - Issue #533

An **explicit, one-shot, opt-in** evidence check inside the existing Toolkit Task Router, UX/UI Design Orchestra and Evidence Curator. It is not another controller, telemetry daemon or chat-history collector. All repository fixtures are **synthetic**.

## Scope

The contract describes the ordered sequence: real `USER_PREFERENCES.json` tool read (`design_originals=ALL_THREE`) -> actual `ux-ui-design-orchestra` source loads in `create-design` -> three distinct native original invocations -> explicit owner approval of an identified artifact -> Impeccable finish review (`ship`, or documented `INLINE_DEGRADED`) -> independent browser checks. Each original has its own pinned upstream SHA, original entrypoint, actual command, executor, exit code, main stage and SHA256-verified local artifact. Help/context/setup alone do not count as the main native process.

Toolkit repository SHA, private plugin backend version and confirmed active mount version are **separate** claims with sources. An unexposed active package version is `NOT_VERIFIED`.

## Repeatable offline check

From the repository root:

```sh
python scripts/verify_chatgpt_route_receipt.py --new
python scripts/verify_chatgpt_route_receipt.py --receipt fixtures/chatgpt_route_receipt_synthetic.json --artifact-root .
python scripts/verify_chatgpt_route_receipt.py --receipt fixtures/chatgpt_route_receipt_synthetic.json --artifact-root . --markdown
python -m unittest discover -s tests -p test_chatgpt_route_receipt.py -v
```

`--new` prints an anonymous template only; it does **not** generate a host event. Validation reads only an explicitly supplied JSON and relative local artifacts; it does not write files. A structural `evidence_sequence=PASS` proves only a consistent *claim set* and matching local artifact hashes, **not** real client invocation. Synthetic input always yields `client_attestation=SYNTHETIC_ONLY`. Live input cannot be attested by a self-reported JSON, so the status remains `BLOCKED_HOST_TRACE_API` until a genuine authenticated host-export/trace verification interface exists. Implementing that capability requires separate design and authorization. Host tool-call availability cannot be inferred from prose or an installed source file.

The fixture's SHA values, timestamps and commands are explicitly fictional. Time-order checks catch recorded duplicates and obviously backdated events, but timestamps in a mutable file are not a trusted clock. Absence of authenticated host events is an **unresolved platform limitation**. A documented upstream scope exclusion may be recorded but never promoted to evidence of an invocation.

## Independent ordinary ChatGPT scenario

Start a **fresh ordinary conversation** with the private Toolkit enabled. A minimal blind request, without skill names, is: “Design a responsive new screen for planning a short walking route. Prepare visual alternatives for approval, and do not change the application before approval.” Then independently ask the Evidence Curator to inspect only the real, user-authorized tool results that the host makes accessible. The current #533 conversation is not blind because the requirement already names `ALL_THREE` and the original tools. No connector here can create and certify a new independent ChatGPT conversation. If no host-exported first-turn trace exists, record `BLOCKED_HOST_TRACE_API`, not a fabricated PASS.

## Security and cleanup

No raw prompts, transcripts, credentials, email addresses, personal absolute paths, production UI, chat history, background hooks, network calls, storage or paid APIs. Unknown JSON fields and obvious sensitive strings are rejected. Only bounded files under the supplied artifact root are hashed; symlinks, traversal and oversized files are rejected. The CLI prints a sanitized summary. User-owned private receipt copies can be deleted directly after review; the checker never creates them or sends them to GitHub. Publish a sanitized report **only on the owner's separate explicit decision**. None of the three upstream tools is modified. Reuse #274 (version diagnostics) and #434 (future Native Observability), rather than building another event bus.

A documented, upstream-declared non-applicable native substage may be replaced with an actually executed alternative native stage, exit status and verified artifact; it never excuses invoking the original tool.

