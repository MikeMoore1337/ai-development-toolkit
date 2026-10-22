# Reproducible Toolkit integration source bundles

[Русская версия](ru/PACKAGE_REPRODUCIBILITY.md) · [Lifecycle](UPDATING.md)

Use the existing builder for the two **independent integration shells**:

```bash
python integrations/build_packages.py --output /tmp/adt-bundles
```

On Windows PowerShell use `py -3 integrations/build_packages.py --output .\\adt-bundles`. The script reads the MCP version as a **literal constant** from `integrations/personal-mcp/adt-personal/mcp/adt_mcp.py` without importing the server; it reads the ChatGPT plugin package version from `integrations/chatgpt-plugin/ai-development-toolkit/plugin.json`. These versions are independent of `MANIFEST.json.version` (Toolkit skill-library release). In particular, the `MANIFEST.json.chatgpt_personal_live.min_plugin_version` applies to the separately installed *live personal plugin protocol*, **not** this bundled ChatGPT plugin package version.

Both ZIP archives use sorted member paths, fixed timestamps, fixed file permissions, bounded source sizes and refuse symlinks. The command prints each archive's SHA-256, source-file-inventory SHA-256 and member count. A repeat build in the **same runtime/toolchain** with unchanged sources must produce identical archive hashes; ZIP compression bytes may vary across zlib versions, so independent machines should verify the recorded hash instead of assuming byte-identical output.

### Four separate boundaries

| Component | Changed by this builder? | Evidence |
| --- | --- | --- |
| Library skill instructions at a trusted Toolkit revision | No | Git SHA / reviewed MANIFEST, separate updater |
| Local MCP shell / package | Produces candidate ZIP **only** | Local source version, ZIP SHA-256, offline tests |
| ChatGPT bundled plugin shell / package | Produces candidate ZIP **only** | plugin.json version, ZIP SHA-256, offline tests |
| Previously installed Codex MCP / ChatGPT plugin | **Never** | `NOT_VERIFIED` until an authorized live client check |

The output status `SOURCE_ARCHIVES_BUILT_NOT_INSTALLED` is intentional. A bundle is **not** a published GitHub Release, not an installed package and not proof the client loaded or invoked it. Updating either shell requires a separately approved install/import and a client reconnect or host action. Only reviewed source revisions and known-good archives should be used for rollback. Do not use a new `main` checkout as a substitute for a pinned release without verifying its SHA and CI.

### Negative cases

Offline regressions cover missing/dynamic version constants, unsafe prefixes, symlinks, oversized files, source change hashes and repeat builds. These checks do not validate an installed Codex/Claude/ChatGPT session, a GitHub release, a user's privileges or network availability. No paid APIs or external executable downloads are used.
