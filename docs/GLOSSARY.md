# AI Development Toolkit glossary

[Русская версия](ru/GLOSSARY.md) | [Start without a terminal](BEGINNER_START.md) | [Home](../README.md)

You can start using Toolkit without learning these terms. Refer to this page when a guide mentions an unfamiliar concept.

| Term | Plain-language explanation |
| --- | --- |
| **Toolkit** | A collection of reusable instructions and utilities, not an AI client by itself. |
| **Skill / Agent Skill** | Instructions for a particular task, stored in a directory with a `SKILL.md` file. |
| **Profile** | A preselected group of skills, such as `qa-python` or `frontend`. It is not a separate AI model. |
| **AI client / agent** | The application that handles your request, such as ChatGPT, Codex, Claude, or Claude Code. Different clients have different access to files and tools. |
| **MCP (Model Context Protocol)** | A way for a compatible client to communicate with external tools. Connecting an MCP server does not automatically grant write access or install skills. |
| **CLI / terminal** | A command-line interface where you run commands such as `python scripts/adt.py profile list`. You do not need it just to discuss a task. |
| **Repository** | Project files and their change history, often managed by Git. Sharing a GitHub link is not permission to edit the project. |
| **Local project** | Files on your computer. A chat app cannot automatically see them without a supported connection and permissions. |
| **`AGENTS.md` / `CLAUDE.md`** | Instructions local to a project. Installing skills must not silently overwrite them. |
| **Preview** | A list of changes a command proposes, without applying them. |
| **`--apply`** | An explicit option that allows a supported command to make the changes you reviewed. |
| **Managed installation / ownership** | Skill Manager records which files it installed and manages only those files. |
| **`status`** | A command that reports the state of the files managed by Skill Manager. |
| **Rollback** | Reverting an eligible previous managed operation, after reviewing its proposed changes. |
| **CI (Continuous Integration)** | Automated checks that run on code or documentation, for example in GitHub Actions. Passing CI does not prove an application works for every user. |
| **Test** | A specific check of behavior. Writing a test plan is not the same as executing tests. |
| **Regression test** | A check that a change has not broken behavior that worked before. |
| **Pull Request (PR)** | A proposed set of changes for review. An open PR is not a merged change. |
| **Deployment** | Running an application in a target environment. Publishing to production requires appropriate authorization. |
| **API** | An interface through which software systems exchange requests and data. Some external APIs require credentials or payment. |
| **Permission** | Authorization to read, modify, execute, or publish. A skill does not override permissions or project rules. |
| **Skill installed** | Skill files were copied into a project. The AI client may still not detect them. |
| **Skill discovered** | The AI client demonstrably recognized a skill in a real session. This does not prove that it used the skill. |
| **Skill used** | The client demonstrably applied that skill to a task. This does not prove the resulting application works. |
| **Application verified** | Relevant behavior was actually checked, with recorded results. Do not infer this from installed skill files. |
| **`main` branch / release** | `main` is the current development branch. A release is a separately published and tagged version. |
| **`PASS` / `FAIL` / `NOT_RUN` / `NOT_VERIFIED`** | A check succeeded, failed, was not run, or lacked sufficient evidence respectively. These are different outcomes. |

Command names, paths, flags, protocol names, and status codes are shown exactly as you should use them; do not translate them when copying examples.
