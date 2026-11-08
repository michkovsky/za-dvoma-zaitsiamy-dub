# Формати

UTF-8; CSV за стандартними правилами екранування (кома, подвійні лапки, заголовок). Скрипти читають також UTF-8 BOM. Тексти з комами або переносами зберігати штатним CSV writer.

Час у читабельних таблицях: HH:MM:SS.mmm; кінець інтервалу виключний. Вихідні таймкоди рахуються від початку конкретного зареєстрованого джерела. У локальних машинних параметрах можна використовувати секунди числом. Час виконання пілота відносний до його початку й не підміняє час української репліки.

ID: персонажі `pronya`, `khymka`, `sirko`, `yavdokha`, `parrot`; пілот `P001`, сцени `S001`…; репліки всередині власника `P001-L001`. Не змінювати ID при уточненні часу або тексту; не використовувати ID повторно для іншої репліки.

Спільна репліка батьків має speaker `sirko+yavdokha`; у виконанні допускає два рядки з тим самим source_id й різними speaker. Це навмисний хор, а не випадковий дубль.

| Таблиця | Основні колонки |
|---|---|
| glossary.csv | id, source, meaning, adaptation_requirement, context |
| languages/<код>/glossary.csv | concept_id, rendering, status, note |
| scenes/index.csv | id, title, start, end, status |
| dialogue.uk.csv | id, start, end, speaker, text, status, note |
| мовний dialogue.csv | id, source_id, speaker, text, status, note |
| performed.csv | id, source_id, start, end, speaker, text, status, note |

Примітки можуть бути вільним текстом; не створювати окрему мову команд у клітинках. Фонетичні підказки синтезатору зберігати окремо від читабельного перекладу. Опис файлів не означає, що всі сцени вже мають заповнені таблиці.

Реєстр characters/index.csv містить основне name, aliases, незалежні in_script/in_film/in_credits (yes/no/unknown), script_name, credit_name, credit_id, актора та джерела. Семантика — characters/rules.md. Повний набір акторських титрів — source/cast-credits.csv. Їхні типи: named_role, episode_actor, intermedia_actor; лише named_role прямо встановлює пару роль/виконавець. Розгорнуті джерела й розбіжності — source/character-sources.md.
