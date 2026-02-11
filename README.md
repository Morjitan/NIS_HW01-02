#  Expense Tracker

### Установка зависимостей

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

### Запуск API
```bash
uvicorn app.main:app --reload
```

### Тесты
```bash
python3 -m pytest -q
```

### Через Makefile
```bash
make install
make test
make typecheck
make lint
```

## Тестирование

### Запуск pytest c coverage

```bash
python3 -m pytest
```

- Целевой порог: `>= 90%`
- Последний запуск: **31 passed**, общее покрытие: **96.98%**

### Запуск Allure отчёта
1) Сгенерировать результаты:
```bash
python3 -m pytest --alluredir=allure-results
```

2) Построить HTML-отчёт:
```bash
npx -y allure-commandline generate allure-results -o allure-report --clean
```

3) Открыть отчёт:
```bash
make allure-open
```

Ручной запуск:
```bash
python3 -m isort app tests
python3 -m black app tests
python3 -m ruff check app tests --fix
python3 -m mypy app tests
```

## pre-commit

Установка хуков:
```bash
python3 -m pre_commit install
```

Проверка перед коммитом вручную:
```bash
python3 -m pre_commit run --all-files
```

Хуки pre-commit:
- `isort`
- `black`
- `ruff`
- `mypy`

