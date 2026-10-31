# Installing skills safely

[Русский](ru/INSTALLATION.md) · [Windows](INSTALL_WINDOWS.md) · [Linux](INSTALL_LINUX.md) · [macOS](INSTALL_MACOS.md)

## Automatic setup for the current task

When the user asks to work with Toolkit, the host agent checks actual project/ancestor/user skill directories and required tools, then installs only missing requirements for the current task within granted permissions. Prefer user scope; preserve existing files. Explicit reference-only/no-install requests and project, network, sandbox and payment restrictions take precedence. Verify source, license, pinned revision and files before installing external originals or dependencies through a reviewed native installer. A required original cannot be silently replaced by reference methods.

For bundled skills, the existing manager supports a repeatable `ensure` operation (Python 3.12+):

```bash
python scripts/skill_manager.py ensure --target "~" --layout codex --skills qa-strategy
```

After reviewing the preview, apply within granted permissions:

```bash
python scripts/skill_manager.py ensure --target "~" --layout codex --skills qa-strategy --apply
```

Then inspect managed status:

```bash
python scripts/skill_manager.py status --target "~" --layout codex
```

Select the skills actually needed, inspect the preview and execute through the host without repeating already granted approval. Use `--layout claude` for Claude Code. `ensure` installs absent bundled skills, preserves readable existing skills without adopting or updating them, and retains existing link, drift, lock and recovery guards. Unknown, incomplete or unsafe entries fail closed; no packages are downloaded by the manager. User-scope state/history lives under `~/.adt/`. Project scope requires its applicable approval.

MCP remains read-only: Personal MCP returns `required_setup`, Project MCP returns the manifest policy and a missing-only preview; the host performs installation. An unknown inventory requires discovery first. Verify installed files, client discovery and a relevant invocation separately. If setup is blocked, name the concrete missing capability/permission and continue independent permitted work. Reading instructions alone is not installation. Installing a skill does not establish its effectiveness.

## Choose the AI client and interface

Installation audit: **2026-10-31**. Choose the actual application and execution environment, not just the model name. Toolkit does not install or authenticate AI clients. Install the selected client separately using its official instructions, then choose **one** Toolkit route: native skill files, read-only MCP, a compatible plugin, or reference material in chat. A CLI command below is an installation step; it does not make a desktop application a CLI-only client.

| Client / interface | Start here | Toolkit route |
| --- | --- | --- |
| Codex Desktop, local project | [Desktop steps](#codex-desktop) | Project MCP or managed `.agents/skills`; Personal MCP optional |
| Codex CLI | [Terminal steps](#codex-cli) | Same project files; Personal MCP optional |
| Codex IDE extension / Cloud | [IDE and Cloud steps](#codex-ide-and-cloud) | Local files for IDE; files in the selected environment for Cloud |
| Claude Code Desktop, Code tab | [Desktop steps](#claude-code-desktop) | Project MCP or managed `.claude/skills` |
| Claude Code CLI / IDE / cloud | [CLI and remote steps](#claude-code-cli-and-remote) | Same layout in the actual execution environment |
| ChatGPT Desktop | [Plugin steps](#chatgpt-desktop) | Repository marketplace or supported plugin import |
| ChatGPT web / mobile | [Web and mobile steps](#chatgpt-web-and-mobile) | Supported plugin import, otherwise chat references |
| Claude chat / Projects / Desktop / mobile | [Hosted Skills steps](#claude-chat) | Native skill ZIP where supported, otherwise references |
| Gemini CLI, Qwen Code, Cursor, Copilot, OpenCode, Roo Code, Windsurf / Devin Local | [Compatible coding clients](#compatible-coding-clients) | Documented shared `.agents/skills`, with client-specific discovery checks |
| Cline, Kiro | [Dedicated skill folders](#dedicated-skill-folders) | Reviewed copy to the client's own folder |
| Hermes Agent | [Hermes steps](#hermes-agent) | Trusted Git project; no dedicated managed Hermes integration |
| DeepSeek Harness | [Harness steps](#deepseek-harness) | Shared skill files or optional Cordis MCP bundle |
| DeepSeek Chat, Qwen Chat, Gemini chat and other chatbots | [Reference-only steps](#other-chat-clients) | Readable URL/files; no universal plugin install |

**Evidence:** the additional coding clients below have official documentation for the listed format/path, not a Toolkit runtime certification. The existing [offline registry](CLIENT_COMPATIBILITY.md) and [dated live observations](CLIENT_CAPABILITIES.md) retain their own scopes. Client discovery/use in this installation audit: **NOT_RUN**; benefit: **NOT_MEASURED**. Optional frontmatter, tools, scripts and permissions differ across clients. Copying a skill does not supply the tools it mentions.

Native-skill check examples use `qa-strategy`, included in the `general` profile. If you install a different selection, check a skill you actually installed. MCP can read this skill directly from Toolkit without a native copy.

### Codex Desktop

1. Install/open the [official desktop client](https://developers.openai.com/codex/app/), select an **existing local project**, and review its `AGENTS.md` and trust settings. Cloud tasks use a different environment.
2. For read-only guidance, follow [Project MCP](MCP_INSTALL.md): preview, review and apply with `--client codex`. This uses Python 3.12+ and **does not require Codex CLI**. For native files instead, follow the managed install below with `--layout codex`; the result is `<project>/.agents/skills/`.
3. Restart Desktop, reopen that project and inspect **Settings → MCP servers** or the available tool/skill list. For Project MCP request `toolkit_catalog`, then `toolkit_read_skill` for `qa-strategy`. For native skills, check that an installed skill is listed and actually read in a relevant task.
4. To share guidance across projects, use [Personal MCP](ONE_COMMAND_SETUP.md). Its automatic registration currently requires **Codex CLI**, even when the eventual client is Desktop. Updating an already registered Windows package with `-McpOnly` is a separate operation; it does not register a fresh server.

Desktop, CLI and IDE can share MCP configuration **on the same Codex host**. A registration does not establish that every surface connected. See [official MCP setup](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

### Codex CLI

1. Install/authenticate [Codex CLI](https://developers.openai.com/codex/cli) separately; check `codex --version`.
2. Choose either [Project MCP](MCP_INSTALL.md) (`--client codex`), [Personal MCP](ONE_COMMAND_SETUP.md) for user scope, or managed skills below (`--layout codex`). Do not register two different servers with the same `ai-development-toolkit` name and assume precedence.
3. Open a terminal **in the target project** and run `codex`. For MCP inspect `codex mcp list`, then `/mcp` inside the session. Invoke `toolkit_catalog` / `toolkit_read_skill` for Project MCP, or `toolkit_info` / `toolkit_prepare_task` for Personal MCP. These are different tool sets.
4. For native skills, inspect the skill selector and request the installed skill by name. Record actual source reads separately from filesystem `status`.

### Codex IDE and Cloud

For the IDE extension, open the target folder, use the same local install as Desktop, then reconnect the extension and verify tools/skills **there**. If the extension runs in WSL, SSH or a container, Python, Toolkit and project paths must exist in that host. Windows user settings are not evidence of a remote connection.

For [Codex Cloud](https://learn.chatgpt.com/docs/cloud), select an authorized repository/environment and make reviewed project skills available **inside that checkout**, for example by including the selected skill files in the repository after review. Local Personal MCP and home-directory skills are not uploaded by these installers. Do not use a laptop's absolute stdio paths in a cloud environment.

### Claude Code Desktop

1. Install/open [Claude Code Desktop](https://code.claude.com/docs/en/desktop), choose the **Code tab** and an existing local project. Ordinary Claude chat is a separate route below.
2. For native skills use the managed install below with `--layout claude`. For MCP use [Project MCP](MCP_INSTALL.md) with `--client claude`; it writes project `.mcp.json` after preview and `--apply`, without requiring the standalone `claude` command.
3. Start a new local Code session, approve the project MCP if prompted and inspect its connected tools. Call `toolkit_catalog` and read `qa-strategy` through `toolkit_read_skill`. For native skills type `/` and select an installed skill, then verify actual use.

Desktop Code and CLI share project skill/MCP files, but other user/Desktop MCP definitions can override a duplicate name. Check the effective server; do not configure the same name twice. [Official shared configuration](https://code.claude.com/docs/en/desktop#shared-configuration).

### Claude Code CLI and remote

Install/authenticate [Claude Code](https://code.claude.com/docs/en/overview), check `claude --version`, then prepare the same `--layout claude` skills or `--client claude` Project MCP. Start `claude` **from the target project**. Use `/mcp` to check the connection or `/qa-strategy` to request that skill when installed. The Toolkit `doctor` command checks files, not this session.

For an IDE extension, start a fresh session against that folder. For web/cloud/SSH sessions, provide reviewed skills and dependencies in **their** checkout; local files are not transferred by Toolkit. Hosted account skill sync, where available, is independently configured by Claude. [Official skill scope](https://code.claude.com/docs/en/skills).

### ChatGPT Desktop

Use the [repository marketplace instructions](ONE_COMMAND_SETUP.md#install-the-plugin-directly-from-the-github-repository) or [plugin ZIP import](../integrations/chatgpt-plugin/README.md), according to the installed host's capabilities. `codex plugin marketplace add MikeMoore1337/ai-development-toolkit` registers a **source only**; then select **AI Development Toolkit (local)** in Plugins Directory and **Install** the plugin. CLI-free users can open a trusted local Toolkit checkout in a supported desktop workspace; if it does not expose the marketplace, use supported ZIP import or references rather than claiming installation. Start a new chat, select the plugin and verify a relevant bundled skill is read. This does not connect Personal MCP or expose arbitrary local files.

### ChatGPT web and mobile

1. Open ChatGPT and check whether that account/client offers plugin import. Where available, import the reviewed Toolkit plugin ZIP following the [plugin guide](../integrations/chatgpt-plugin/README.md), select it in a new chat and verify a skill read.
2. If import is unavailable, provide a readable Toolkit URL or selected public skill files as [reference material](#other-chat-clients). A desktop marketplace command does not install a plugin on web/mobile.
3. Supply authorized project files separately. These installers provide no hosted HTTP endpoint for connecting local Toolkit stdio MCP to web/mobile.

### Claude chat

For Claude web, ordinary Desktop chat, Projects and mobile, use [native custom Skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills) **where that interface supports upload**:

1. Select one needed skill, such as `.agents/skills/qa-strategy`, with all its local resources and license notices. ZIP the **skill folder**, so the archive contains `qa-strategy/SKILL.md` and its resources, without an extra Toolkit wrapper. A project ZIP and a skill ZIP are different inputs.
2. In **Customize → Skills**, upload the ZIP and enable the skill. Code execution and organization/account controls must permit it. The entire Toolkit repository and the ChatGPT plugin ZIP are not individual Claude Skills.
3. Start a new chat, request a relevant task and inspect whether the skill was actually used. If a mobile/client UI lacks upload, use a supported web/desktop UI or reference material; do not invent a mobile import button.

This is independent of Claude Code's `.claude/skills` installation; Skill Manager does not manage hosted Skills or their updates.

### Compatible coding clients

The following official sources document shared project `.agents/skills`. Install the client separately, open the target project, then use **the existing managed install below with `--layout codex`**. Here `codex` selects the destination folder; no Codex executable or account is needed. Start a fresh client session and check the client-specific discovery surface:

| Client / interface | Discovery and verification after the shared install | Official source, checked 2026-10-31 |
| --- | --- | --- |
| Gemini CLI | Launch `gemini` in the project; `/skills list`, then request `qa-strategy` and review the activation consent | [Skills](https://geminicli.com/docs/cli/skills/) |
| Qwen Code CLI / IDE | Launch `qwen` in the project or open its IDE session; `/skills`, then request the skill | [Skills and shared paths](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/) |
| Cursor IDE | Open local Agent chat in that project, inspect Skills and request the installed skill | [Skill directories](https://cursor.com/docs/skills) |
| GitHub Copilot in VS Code | Open the project and Agent Customizations → Skills; check `chat.useAgentSkills` if discovery is disabled | [VS Code Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills) |
| GitHub Copilot CLI | Launch `copilot` in the project; `/skills reload`, then `/skills info qa-strategy` | [CLI Skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills) |
| OpenCode local CLI / Desktop | Select the project or launch `opencode` there; request a read through the native `skill` tool | [Skill discovery](https://opencode.ai/docs/skills) |
| Roo Code IDE extension | Open the project, start a new task in a mode with skill access, request the installed skill | [Shared skill directories](https://docs.roocode.com/features/skills) |
| Windsurf / Devin Local, current documented desktop harness | Open the project, inspect Customize → Skills and request the skill; older Windsurf builds need their own version check | [Current customizations and legacy paths](https://docs.devin.ai/desktop/devin-local/customizations) |

For **Cursor CLI**, select the same project using the [official CLI](https://cursor.com/docs/cli/overview), then check that version's skill discovery; this audit has not established identical CLI/IDE behavior. For cloud/web variants of any coding client, provide skills in the remote workspace and verify again. A local shared directory alone is insufficient. Toolkit's MCP installer still accepts **only `codex` and `claude`**; do not invent `--client gemini`, `--client cursor` or other adapter flags.

### Dedicated skill folders

For **Cline** use project `.cline/skills` ([official Skills guide](https://docs.cline.bot/customization/skills)); inspect the extension's **Skills** tab. For **Kiro IDE / CLI** use project `.kiro/skills` ([official Skills guide](https://kiro.dev/docs/skills/)); inspect **Agent Steering & Skills** or request `/qa-strategy` in a supporting session. This audit does not assume shared `.agents/skills` discovery for these two clients.

Use the existing one-time copier for a dedicated path. From the Toolkit root, with Python 3.12+, replace **both** absolute paths with real paths; the target project must exist. Example for Cline:

~~~bash
python scripts/install.py --target /path/to/repo --skills qa-strategy --skills-dir /path/to/repo/.cline/skills
~~~

Review the preview, then separately apply:

~~~bash
python scripts/install.py --target /path/to/repo --skills qa-strategy --skills-dir /path/to/repo/.cline/skills --apply
~~~

For Kiro replace `.cline/skills` with `.kiro/skills` in **both commands**. On Windows use `py -3.14` (or your installed 3.12+ interpreter) and quote Windows paths. Copy the complete folder, not just `SKILL.md`. The copier refuses existing destinations; it provides **no managed update/rollback history**. Review and back up these files before manual updates. Reopen/reload the client and verify discovery/use separately.

### Hermes Agent

Use a trusted **Git project** and follow the [pinned Hermes contract and limitations](CLIENT_COMPATIBILITY.md#hermes-specific-boundaries). A reviewed whole-skill copy under `.hermes/skills` or `.agents/skills` may be inspected by Hermes; use the custom copier above for `.hermes/skills` if needed. Project trust and quarantine rules apply. Toolkit has **no dedicated Hermes manager, migration or MCP installer**. Do not infer activation from an overlapping Codex path; verify in the installed Hermes session.

### DeepSeek Harness

Install/configure Harness separately, then follow the [Harness guide](../integrations/deepseek-harness/README.md). Choose managed shared `.agents/skills` via `--layout codex`, or generate the optional Cordis MCP bundle, review it and explicitly install it into the chosen `dsh` profile. Native `.dsh/skills` management is not provided. Inspect the active profile and actual tools/skills after restart. **DeepSeek Chat does not use this installer.**

### Other chat clients

For [DeepSeek Chat](../integrations/deepseek-chat/README.md), Qwen Chat, Gemini web/mobile and other chat-only interfaces, no Toolkit-native plugin install is established here. Open the chat, provide the Toolkit URL and permitted project material, and ask it to read only relevant public `SKILL.md` files. If URL reading fails, attach those files **with needed references** or paste the necessary text. Use the [no-terminal workflow](BEGINNER_START.md). Report `GUIDANCE_ONLY`, not installed skills; if execution tools are absent, tests remain `NOT_RUN`. Qwen Chat is distinct from Qwen Code; Gemini chat is distinct from Gemini CLI.

## Check, update or remove the selected route

For managed copies, `status`, `update`, `uninstall`, `rollback` and `recover` are described below; use the same `--layout`. For MCP use that installer's `doctor` and removal instructions. For hosted plugins/Skills, use the host's own disable/remove/update controls. Reference-only chat needs no uninstall. See [separate source, skill, MCP and plugin update procedures](UPDATING.md). If a client does not find a skill, check the actual workspace, client version, disabled skills, duplicate names and referenced resources before copying anything again.

## Beginner CLI (Skill Manager v2)

Use the same managed install engine through a smaller entrypoint. Python 3.12+ and an **existing** target project are required. The CLI never downloads or installs an AI client. Run these commands from the Toolkit checkout:

~~~bash
python scripts/adt.py profile list
python scripts/adt.py doctor --target /path/to/repo
python scripts/adt.py profile plan --target /path/to/repo --task qa
python scripts/adt.py init --target /path/to/repo --profile general
~~~

**Inspect the preview first.** Replace `/path/to/repo` with an existing project directory. Only then apply the change and check status in a separate block:

~~~bash
python scripts/adt.py init --target /path/to/repo --profile general --apply
python scripts/adt.py status --target /path/to/repo
~~~

On Windows, replace `python` with `py -3` and use a Windows project path. Select `--layout claude` for a Claude Code skills folder; this does **not** confirm that Claude Code is installed or detects skills. All commands except `init --apply` are read-only. Inspect the per-file plan **before** granting `--apply`. A missing project is never created automatically. `doctor` reports damaged state, drift, linked paths, transactions and unmanaged skills without attempting repair; filesystem permissions and client activation can remain NOT_VERIFIED. For a recoverable interruption, preview `python scripts/skill_manager.py recover --target /path/to/repo`; apply recovery only after explicit review. For managed updates and rollback, continue using `skill_manager.py`. A repeat `init` skips already managed clean skills; unrelated unmanaged folders remain untouched. Existing `AGENTS.md` and `CLAUDE.md` are not rewritten.

For technical documentation use `--task docs` (profile `docs-technical`, source verification), for wording only use `--task docs-edit` (`editorial`); `--task docs-verify` requests factual cross-checks. QA selection is heuristic: Python/JavaScript files do not establish that pytest or Playwright are installed. Wide `qa-all` includes 27 QA skills and should normally be replaced with a focused profile; the number of files does not measure model tokens.

[Русский первый запуск](ru/GETTING_STARTED.md)

Client layouts, pinned source evidence and offline verification: [CLIENT_COMPATIBILITY.md](CLIENT_COMPATIBILITY.md).

**New project? Start with Skill Manager v2.** You need Python 3.12+, a clone of this Toolkit and an existing target project. The Toolkit does not install an AI client. Choose a profile with `python scripts/skill_manager.py catalog`, then:

~~~bash
python scripts/skill_manager.py install --target /path/to/repo --profile qa-core
~~~

**After reviewing the proposed plan**, apply the installation and check its status separately:

~~~bash
python scripts/skill_manager.py install --target /path/to/repo --profile qa-core --apply
python scripts/skill_manager.py status --target /path/to/repo
~~~

The first command previews file-level changes; only `--apply` writes. Review the target project's existing `AGENTS.md`, `CLAUDE.md` and skill folders first; these files are never automatically rewritten. For Claude Code, use `--layout claude` consistently. Manager ownership and backups apply only to its own installations.

**One-time copy without managed updates:** `python scripts/install.py --target /path/to/repo --profile qa-core`, then repeat with `--apply`. This legacy installer is still supported, refuses to overwrite existing skills and allows custom trusted `--skills-dir PATH` destinations. It does **not** create manager ownership or rollback history. Do not assume the Manager can adopt a legacy installation.

**Verify:** use `status` for Manager-owned skills, inspect the copied `SKILL.md`, then separately check whether your installed, configured AI client actually discovers and activates the skill. Copying files, source-format compliance and real client activation are different claims. QA reference roles are documentation, not auto-created agents.

**When moving to a public repository:** run validation and publication checks; review `extensions/qa/SOURCE_MAPPING.md`, licenses and all credential-like strings.


## Local MCP server

[Install project-scoped Toolkit MCP for Codex / Claude Code](MCP_INSTALL.md) on Windows, Linux or macOS. MCP tools are read-only; config writes require explicit `--apply`. It is not an HTTP endpoint for ChatGPT.

## Operating-system guides and updates

[Windows / PowerShell](INSTALL_WINDOWS.md) · [Linux / bash](INSTALL_LINUX.md) · [macOS / zsh or bash](INSTALL_MACOS.md) · [Source vs skill vs plugin vs MCP updates](UPDATING.md).

Use an explicit Python 3.12+ interpreter. On Windows examples use `py -3.12`, on Linux/macOS use `python3.12` if installed. Generic `python` in shared examples must be replaced with the correct verified interpreter where necessary. Hosted macOS portability checks do not prove real-client activation.

## Optional read-only profile recommendation

The toolkit can suggest a profile from an explicit task and limited, well-known
project configuration file names. It **does not** inspect private source text,
contact any service, install a skill or decide release permissions.

```bash
python scripts/recommend_profile.py --target /path/to/repo --task qa
python scripts/recommend_profile.py --target /path/to/repo --task feature
```

Supported tasks: `feature`, `ui`, `qa`, `ci`, `release`, `docs`,
`agent`, `backend`, `frontend`, `research`, `provider`. For QA, a Python configuration selects `qa-python`; Python plus
JavaScript selects `qa-fullstack`; JavaScript plus Playwright selects
`qa-ui`. Unknown stacks fall back to `qa-core`.

The output includes a rationale, `read_only: true`, and separate `optional_skills`
and `optional_profiles` suggestions (never installed). For the five curated
areas and size/overlap metrics, see [Curated Skill Packs](CURATED_SKILL_PACKS.md).
Run `python scripts/profile_metrics.py` for file-byte measurements (not model tokens).

The output includes a rationale and `read_only: true`. Every recommendation
is **heuristic** and must be reviewed against local project rules. Use the
recommended Skill Manager for preview and explicit `--apply` after deciding.

## Skill Manager v2 (recommended for managed installs)

The existing `install.py` remains supported for simple one-time copies. The
new `skill_manager.py` maintains an **ownership lockfile** and local history
only for skills installed with the manager. It never adopts or overwrites an
unmanaged skill or edits `AGENTS.md` / `CLAUDE.md`.

~~~powershell
$project = "D:\Work\example-project"
py -3 scripts/skill_manager.py install --target $project --profile qa-python
py -3 scripts/skill_manager.py update --target $project
py -3 scripts/skill_manager.py uninstall --target $project --skills api-testing
py -3 scripts/skill_manager.py rollback --target $project
py -3 scripts/skill_manager.py recover --target $project
~~~

**These are five alternative previews, not a sequence of required actions.** Pick only the operation you need, inspect its plan, and then run **only the corresponding** `--apply` command. For example, to install a profile:

~~~powershell
py -3 scripts/skill_manager.py install --target $project --profile qa-python --apply
py -3 scripts/skill_manager.py status --target $project
~~~

For other operations use `update --apply`, `uninstall --apply`, `rollback --apply` or `recover --apply` as appropriate. Do not run them in sequence. Review the selected plan, its consequences and recovery options first.

The manager stores the first client's schema-v1 lock in `.adt/skills-lock.json`.
For a second client it uses the independently owned
`.adt/skills-lock-codex.json` or `.adt/skills-lock-claude.json`. Shared
`.adt/manager.lock` and transaction snapshots in `.adt/history/` remain
**inside the target project**.
Backups may include copies of installed skill files: exclude `.adt/` from
commits where appropriate. The manager does not edit `.gitignore` automatically.

**Safety:** lockfile-only ownership, content drift checks, read-only previews,
exclusive process locking, staged replacement, interruption recovery, no
hidden network downloads. Locally modified owned skills block mutation.

Existing skills installed with the original `install.py` are not adopted.
Back up and manually migrate them only after reviewing their contents, then
install through the manager into free destinations. Do not delete user changes
just to make a manager command pass.

### File-level previews

Every modifying preview now reports `file_diffs` with added, modified and
deleted relative file names and before/after SHA256 values. These are local
byte comparisons; they do not reveal file contents or bypass the ownership
lock. Review this list before supplying `--apply`. A clean, unchanged update
reports an empty change set. When a file contains local modifications outside
the recorded lockfile digest, the operation stops rather than overwriting it.

### Discover profiles and copy managed skills between clients

~~~bash
python scripts/skill_manager.py catalog
python scripts/skill_manager.py catalog --profile qa-python
python scripts/skill_manager.py migrate --target /path/to/repo --from-layout codex --layout claude
~~~

Migration also requires review. **Only if the preview matches the intended changes and avoids unmanaged files**, run separately:

~~~bash
python scripts/skill_manager.py migrate --target /path/to/repo --from-layout codex --layout claude --apply
python scripts/skill_manager.py status --target /path/to/repo --layout claude
~~~

Migrate **copies**, never removes, the clean, Manager-owned source skills,
with exact SHA256 match to the current Toolkit source. It refuses collisions,
drift, legacy/unmanaged folders and different source bytes. `status`,
`update`, `uninstall` and `rollback` use `--layout` to select the
independent client; `recover` handles pending transactions across both.

See [full Windows/Linux migration scenarios and limitations](CLIENT_MIGRATION.md).
File installation alone is not proof of client discovery, model activation or
effectiveness. For arbitrary custom `--skills-dir` locations continue to use
legacy `install.py`; Skill Manager does not claim ownership of them.
