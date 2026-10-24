# Обновление Toolkit, навыков, MCP и плагина ChatGPT

[English](../UPDATING.md) · [Установка](INSTALLATION.md) · [Миграция](CLIENT_MIGRATION.md)

| Компонент | Как обновляется |
| --- | --- |
| Локальная копия Toolkit | Проверка Git и осознанный переход к выбранной ревизии |
| Управляемые навыки рабочего проекта | Из **текущих локальных исходников Toolkit** через Skill Manager |
| Плагин ChatGPT | Может получать новые проверенные инструкции; **установленная оболочка сама не заменяется** |
| Локальный Toolkit MCP | Есть Python-сервер stdio и установка в проектные настройки Codex/Claude Code; исходники обновляются только отдельной проверенной операцией Git |

## 1. Осознанно обновите исходники Toolkit

~~~bash
git status --short
git rev-parse HEAD
git fetch --tags origin
git log --oneline HEAD..origin/main
~~~

Fetch обновляет данные Git, не рабочие файлы. Проверьте изменения, после чего для чистой локальной ветки main допускается `git pull --ff-only origin main`. Для опубликованного релиза используйте отдельную чистую копию и точный утверждённый тег, например `git switch --detach v5.5.4`; сверяйте состав тега и `MANIFEST.json.version`. Не сбрасывайте чужие изменения ради обновления.

## Проверка и откат выделенной копии Personal MCP

Обновлятор исходников **Personal MCP** работает только с отдельной Git-копией Toolkit, созданной установщиком. Он не устанавливает новую версию Python-сервера MCP, не импортирует ChatGPT-плагин и не меняет рабочие проекты.

~~~bash
# Только локальное чтение: нет сети и изменений
python3 integrations/personal-mcp/adt-personal/updater/update_toolkit.py --preflight
# Последнее известное состояние Git
python3 integrations/personal-mcp/adt-personal/updater/update_toolkit.py --status
# Предпросмотр допустимого отката на сохранённую ревизию
python3 integrations/personal-mcp/adt-personal/updater/update_toolkit.py --rollback
# Применять только после проверки SHA и состава изменений
python3 integrations/personal-mcp/adt-personal/updater/update_toolkit.py --rollback --apply
~~~

При запуске скрипта из репозитория укажите реальные пути **выделенной** копии через `--source` и `--state-dir`: пути по умолчанию относятся к установленному Personal MCP. В Windows можно использовать `py -3`, для остальных инструментов Toolkit требуется проверенный Python 3.12+.

`--preflight` без сетевого доступа проверяет чистоту Git-копии, официальный адрес origin, текущую версию Toolkit, последнюю **известную** версию/SHA и допустимость отката. Неизвестная версия обозначается `NOT_VERIFIED`, а фактическая совместимость подключённого MCP или ChatGPT — `NOT_TESTED`: исходники Toolkit не доказывают обновления этих оболочек. Git origin, коммиты и SHA256 доказывают ограниченные свойства целостности, **но не являются цифровой подписью или гарантией безопасности кода**.

Плановое обновление разрешает только fast-forward и блокирует понижение версии Toolkit. Для отката нужна сохранённая прежняя ревизия, чистая рабочая копия и явное `--apply`. При локальных изменениях, неправильном origin, несовпадающем состоянии или параллельном запуске операция прекращается без принудительного удаления пользовательских файлов. Если нужен длительный откат, сначала отключите планировщик: иначе очередное разрешённое обновление снова подтянет `main`.

## 2. Сначала предпросмотр управляемых навыков

Из проверенной копии Toolkit, для **существующего проекта** и Python 3.12+:

~~~bash
python3.12 scripts/skill_manager.py status --target /path/to/project --layout codex
python3.12 scripts/skill_manager.py update --target /path/to/project --layout codex
# Проверьте file_diffs, владение файлами и SHA256.
python3.12 scripts/skill_manager.py update --target /path/to/project --layout codex --apply
python3.12 scripts/skill_manager.py status --target /path/to/project --layout codex
python3.12 scripts/skill_manager.py rollback --target /path/to/project --layout codex
~~~

В Windows PowerShell используйте `py -3.12` и путь Windows в кавычках. На macOS предварительно проверьте `python3.12 --version`; системный `python3` не обязательно подходит. Для Claude Code используйте `--layout claude`. `rollback` без `--apply` показывает предпросмотр, а с ним откатывает последнюю допустимую операцию менеджера. При прерывании сначала выполните `recover --target PROJECT` без записи; восстановление с `--apply` требует отдельного решения. Чужие навыки и прежний `install.py` автоматически не принимаются под управление. История и резервные копии - в `PROJECT/.adt/`.

## 3. Плагин и MCP - отдельные процедуры

Плагин ChatGPT использует контракт `MANIFEST.json.chatgpt_personal_live`, когда способен проверенно прочитать актуальные инструкции. Изменение его пакета требует отдельного обновления через Plugin Creator. Это функция аккаунта, а не установленная на Windows, Linux или macOS программа Toolkit.

Для Codex и Claude Code реализован [локальный установщик MCP](MCP_INSTALL.md) со ссылкой на доверенную копию Toolkit по абсолютному пути. Обновление копии возможно после проверки Git и переподключения клиента, **не автоматически в фоне**. HTTP MCP для браузерного ChatGPT не реализован. Нельзя выдумывать команды `pip`, `npm`, `docker` и обещать фоновое обновление. Конкретный MCP-сервер проверяется и устанавливается по собственной инструкции, с учётом прав доступа.

## 4. Границы проверки

Linux и Windows проходят общий офлайновый CI. Для macOS Apple Silicon и Intel используется отдельная ограниченная проверка установки, владения файлами и отката на GitHub Actions с Python 3.12. Это **не проверка личного Mac, реального Codex/Claude Code или приложения**. Согласно [документации GitHub](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) стандартные runner для публичных репозиториев бесплатны. Платные runner, AI API и устройства пользователя не используются.
