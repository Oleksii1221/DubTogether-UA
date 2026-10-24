<div align="center">

# Dub Together UA

### Грайте українською

Український переклад **Dub Together** для Linux і Steam Proton.
Один портативний файл, покрокове встановлення та готовий параметр запуску.
Автор перекладу та інсталятора: **Kico**.

[Сайт](https://oleksii1221.github.io/DubTogether-UA/) ·
[Linux-збірки](https://github.com/Oleksii1221/DubTogether-UA/actions/workflows/linux-build.yml) ·
[Повідомити про проблему](https://github.com/Oleksii1221/DubTogether-UA/issues)

</div>

![Вітальний екран інсталятора](docs/assets/app-welcome.png)

> **Linux dev 1.0.3:** розробка ведеться в `linux_dev`. `linux_master` зарезервовано для перевірених Linux-релізів.

## Що робить інсталятор

1. Після відкриття **лише показує вікно** — гра продовжує працювати.
2. На кнопці «Почати встановлення» показує попередження про закриття гри.
3. Тільки після підтвердження перевіряє підтримувану збірку, делікатно
   закриває Dub Together і створює український `.pck` у `~/.local/share` або `$XDG_DATA_HOME`.
4. Показує прогрес, стадію помилки, готовий рядок для Steam і кнопки копіювання.

Оригінальний `DubTogether.exe` та файли в каталозі Steam не перезаписуються.
Оскільки гра не має нативної Linux-збірки, інсталятор працює з Windows-версією через Steam Proton.
Інсталятор не завершує гру примусово: якщо вона не закриється упродовж 20 секунд,
зупиниться з повідомленням і попросить закрити її вручну.

## Встановлення для гравця на Linux

1. Відкрий останню успішну [Linux development build](https://github.com/Oleksii1221/DubTogether-UA/actions/workflows/linux-build.yml) і завантаж артефакт `DubTogether-UA-Linux-dev`.
2. Розпакуй його та дозволь запуск: `chmod +x DubTogether-UA-Installer-Linux-x86_64`.
3. Запусти файл, збережи свій прогрес у грі та натисни **«Почати встановлення»**.
4. Прочитай попередження та підтвердь. Дочекайся завершення.
5. Натисни **«Копіювати»** біля повного рядка `--main-pack "Z:\\..."`.
6. У Steam відкрий **Бібліотека → Dub Together → шестерня → Властивості → Загальні → Параметри запуску** й встав увесь рядок.
7. На останньому екрані інсталятора натисни **«Готово»**, щоб закрити його.
8. Запусти гру через Steam Proton. За потреби вибери **Українська** в налаштуваннях мови.

> Підтримується перевірена збірка гри з SHA-256
> `916ea61397884369e0431b8e393b03d1434d3054b56cf719d43664d1e0f3e72d`.
> Після оновлення гри інсталятор може вимагати новий патч.

## Розробка

Код програми та інструментів — **Python 3.12**. Вікно побудоване на **PySide6 / Qt**.
Бінарні зміни гри зберігаються як патчі. Повного PCK чи EXE гри в репозиторії немає.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-build.txt
export PYTHONPATH=src
.venv/bin/python tools/audit_translations.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m dubua
.venv/bin/python tools/build_linux.py
```

Результат збірки: `dist/DubTogether-UA-Installer-Linux-x86_64`. `tools/rebuild_from_game.py`
відтворює бінарні патчі з **власної копії гри** за допомогою зовнішнього
[GDRETools](https://github.com/GDRETools/gdsdecomp); приклад:

```powershell
.\.venv\Scripts\python.exe tools\rebuild_from_game.py --game 'C:\Path\To\DubTogether.exe' --gdre 'C:\Path\To\gdre_tools.exe'
```

Переклади редагуються в [`translations/uk.json`](translations/uk.json).
Інструмент `tools/catalogue_to_gd.py` перетворює JSON на GDScript перед
повторним збиранням патчів. Автоматична перевірка ловить порожні та незмінені
англійські рядки, відсутні кнопки екрана запису та зіпсовані `%s`/`%d`.

### Структура

| Шлях | Призначення |
| --- | --- |
| `src/dubua/ui.py` | Покрокове вікно, прогрес та інструкція |
| `src/dubua/installer.py`, `pck.py`, `game.py` | Пошук гри, створення PCK, делікатне закриття |
| `translations/uk.json` | Український каталог |
| `tools/` | Аудит, відтворення патчів, збірки Linux і Windows |
| `docs/` | Статичний сайт для GitHub Pages |

## Сайт і статистика

Сайт лежить у `docs/` і публікується через GitHub Pages. На ньому одна кнопка
встановлення, яка веде прямо на `DubTogether-UA-Installer.exe` з останнього
GitHub Release, а також посилання на Steam-профіль автора й репозиторій.

Umami підключено через публічні `scriptUrl` і `websiteId` у
[`docs/config.js`](docs/config.js). Приватні токени в репозиторії не зберігаються.
Статистика DubTogether-UA відокремлюється шляхом `/DubTogether-UA/`, а клік по
кнопці встановлення записується як подія `download-windows`. Лічильник файлів
також доступний на сторінці GitHub Release.

## Гілки, участь і ліцензії

- `dev` — розробка Windows-версії.
- `master` — перевірені Windows-релізи.
- `linux_dev` — розробка Linux/Steam Proton версії та Linux-артефакти в Actions.
- `linux_master` — перевірені Linux-релізи; залишається порожнім до окремої команди на реліз.

Пропонуй виправлення перекладу через Pull Request у `dev`, бажано зі знімком
екрана й поясненням контексту. Ніколи не додавай до репозиторію повний PCK,
EXE гри, збереження або особисті дані зі Steam.

**Код** — [MIT](LICENSE). **Авторський переклад** — [CC BY-NC 4.0](CONTENT-LICENSE.md)
у межах прав автора; він призначений для безкоштовного некомерційного
поширення. MIT сама по собі дозволяє комерційне використання коду.
Сторонні компоненти й знімки описані в [THIRD_PARTY.md](THIRD_PARTY.md).

Dub Together UA — неофіційна робота спільноти, не пов'язана з розробниками гри.
