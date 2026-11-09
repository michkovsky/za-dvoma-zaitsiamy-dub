# Рев’ю PR #11: суми входів і перевірка diff

- Рецензент: GitHub Copilot pull-request reviewer; точну модель сервіс не повідомив.
- Дата: 2026-11-09. Review ID: 5826442860; переглянутий head: `01b46499b5beab2a33e027700fe2369b7c8ff436`.
- Джерело: [рев’ю](https://github.com/michkovsky/za-dvoma-zaitsiamy-dub/pull/11#pullrequestreview-5826442860).
- Обсяг: відповідність опублікованих входів контрольним сумам та достатність quickstart-перевірок. Це окреме рев’ю GitHub, не попередні CLI-сесії генерації перекладів і не прослуховування медіа. Виправлення та перевірки нижче виконав автор; нової модельної перевірки виправлень цим записом не заявлено.

| ID | Зауваження / доказ | Блокувальне? | Рішення | Виправлення |
|---|---|---|---|---|
| R-02 | [4513178172](https://github.com/michkovsky/za-dvoma-zaitsiamy-dub/pull/11#discussion_r4513178172): суми CRLF не збігаються з опублікованими LF-входами | Для перевірки входів | accepted | У translation-ab/metadata.json збережено історичні поля, позначено UTF-8/CRLF, додано published_inputs_utf8_lf_sha256 для A/B. У quickstart наведено точний алгоритм і виконуваний приклад перевірки п’яти записів входів. Переклади та prompts не змінено. |
| R-03 | [4513178230](https://github.com/michkovsky/za-dvoma-zaitsiamy-dub/pull/11#discussion_r4513178230): git diff без бази пропускає закомічені зміни | Для доказу незмінності P001 | accepted | Quickstart використовує git fetch origin main, whitespace-перевірку та exit-code порівняння P001 за origin/main...HEAD; окремо перевіряє unstaged/staged зміни. |

## Фактичні перевірки виправлення

- Відтворено всі п’ять історичних SHA заміною LF → CRLF у Git blobs попереднього head; жодне історичне значення не змінено.
- Приклад Python із quickstart виконано: `OK: 5 published UTF-8/LF input hashes`. Додані суми також зіставлено з LF-байтами Git blobs.
- `python pipeline/validate.py`: OK, 17 CSV-таблиць; це не перевірка звуку або нових SHA. SHA перевірено окремою операцією вище.
- `git diff --check origin/main...HEAD`: exit=0; P001 порівняно з тією самою базою через --exit-code, diff порожній. Окремі staged/unstaged перевірки P001 та whitespace також пройдено.
- Базу PR оновлено й звірено: main `96e085f9e8ec35720bb5830165701006d6e4c8bb`.

Слухова перевірка, мовці та точні межі P002 лишаються відкритими; ці два виправлення їх не завершують. PR не зливався.
