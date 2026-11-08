# Research
Наявні скрипти мають жорсткі local/runtime.json і media/scenes paths. Обрано два optional CLI flags і сесійний DUB_WORK_DIR замість junction, AppData або переписування загальних системних змінних. Python/FFmpeg уже доступні; перевстановлення не потрібне. Особливості старого CPU перевіряє наявний inventory; ML не запускається. Критичних невизначеностей для цих двох шляхів немає.
