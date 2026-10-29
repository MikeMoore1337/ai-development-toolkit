# Harness²: приёмка оригинального upstream на Windows/WSL2

Этот сценарий относится к Toolkit #421 и использует **исключительно** существующие install.sh и cli.sh. Он не устанавливает Harness² в Python 3.14 Windows, не меняет Codex Desktop, YFC, Hermes или Second Brain. Все команды выполняются в Ubuntu WSL2. Никакие модели, judge, Codex CLI и Claude CLI не запускаются.

## Требования

- Windows 11, WSL2 с Ubuntu. По умолчанию скрипт автоматически выбирает установленный `Ubuntu-24.04`, `Ubuntu` или `Ubuntu-22.04` (другие версии `Ubuntu-XX.YY` также распознаются). Для явного выбора используйте `-Distribution Ubuntu-24.04`. Внутренний `docker-desktop` не используется.
- Если Ubuntu не установлена, выполните в PowerShell `wsl --list --verbose`, затем `wsl --list --online` и `wsl --install -d Ubuntu-24.04`. Это отдельная команда установки Linux, **сам сценарий Harness² её не выполняет**. При первой загрузке Ubuntu создайте непривилегированного Linux-пользователя; может потребоваться перезагрузка Windows.
- В Ubuntu: непривилегированный пользователь, Git и Python 3.12. Для полного штатного benchmark setup дополнительно потребуются uv, npm и компоненты из [официального SETUP](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/docs/SETUP.md).
- Checkout Toolkit, доступный с Windows и из WSL2 через wslpath.

В PowerShell из каталога Toolkit:

~~~powershell
.\integrations\harness2\acceptance.ps1 -Action Preflight
.\integrations\harness2\acceptance.ps1 -Action Install
.\integrations\harness2\acceptance.ps1 -Action Status
.\integrations\harness2\acceptance.ps1 -Action SetupPreview -Benchmark lab
.\integrations\harness2\acceptance.ps1 -Action Check -Benchmark lab
.\integrations\harness2\acceptance.ps1 -Action Artifacts
~~~

**Check должен завершиться отказом**, если официальный benchmark ещё не настроен; это не сбой оболочки и не подтверждение выполненного эксперимента. SetupPreview только показывает план оригинального upstream. RunPreview также использует штатный dry-run и не заменяет реальный запуск.

Полный Setup допустим только по явному решению после проверки лицензий, сетевых загрузок и изоляции:

~~~powershell
.\integrations\harness2\acceptance.ps1 -Action Setup -Benchmark lab -ConfirmNetworkDownloads
~~~

Он скачивает и запускает сторонние зависимости **без модельного эксперимента**, но не разрешает последующие расходы API. Не выполняйте эту команду автоматически в Docker/VPS с секретами или личными данными.

Откат также требует отдельного подтверждения:

~~~powershell
.\integrations\harness2\acceptance.ps1 -Action Remove -ConfirmRemove
~~~

Удаляется только исходная проверенная установка, внешние результаты не удаляются. Если Preflight сообщает об отсутствии Python 3.12, Git или Ubuntu, исправьте системные требования отдельно, не меняя глобальный Python 3.14 Windows. Эти проверки не доказывают поддержку Codex Desktop или улучшение качества моделей. Для закрытия #421 нужны результаты настоящей приёмки WSL2 и отдельно статус разрешённого официального benchmark.
