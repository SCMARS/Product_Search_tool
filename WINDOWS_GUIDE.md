# Інструмент Пошуку Товарів - Windows Guide

Це керівництво містить інструкції для запуску додатку на Windows.

## Вимоги

- **Python 3.6 або вище** - [Завантажити з python.org](https://www.python.org/downloads/)
- **Node.js та npm** - [Завантажити з nodejs.org](https://nodejs.org/)
- **PowerShell** (вбудований в Windows 10/11)

## Швидкий запуск

1. **Відкрийте PowerShell як адміністратор**
   - Натисніть `Win + X` та виберіть "Windows PowerShell (Admin)" або "Terminal (Admin)"
   - Або знайдіть PowerShell в меню Пуск, клікніть правою кнопкою та виберіть "Запустити як адміністратор"

2. **Перейдіть до директорії проекту**
   ```powershell
   cd "C:\path\to\your\Product_search_tool_e_finder"
   ```

3. **Запустіть скрипт:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\run.ps1
   ```

Це автоматично:
- Налаштує Python віртуальне середовище
- Встановить залежності бекенду
- Встановить браузери Playwright
- Запустить сервер Flask
- Встановить залежності фронтенду
- Запустить розробческий сервер React

## Альтернативний запуск

Якщо у вас налаштована політика виконання PowerShell, ви можете просто запустити:

```powershell
.\run.ps1
```

## Ручне налаштування

### Налаштування бекенду

1. **Відкрийте PowerShell та перейдіть до директорії бекенду:**
   ```powershell
   cd backend
   ```

2. **Створіть віртуальне середовище:**
   ```powershell
   python -m venv venv
   ```

3. **Активуйте віртуальне середовище:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

4. **Встановіть залежності:**
   ```powershell
   pip install -r requirements.txt
   ```

5. **Встановіть браузери Playwright:**
   ```powershell
   playwright install
   ```

6. **Створіть файл `.env` на основі `.env.example` та додайте ваші облікові дані API Allegro:**
   ```
   ALLEGRO_CLIENT_ID=your_client_id_here
   ALLEGRO_CLIENT_SECRET=your_client_secret_here
   ```

7. **Запустіть сервер Flask:**
   ```powershell
   $env:FLASK_APP = "app.py"
   flask run --port=5001
   ```
   API буде доступний за адресою http://localhost:5001

### Налаштування фронтенду

1. **Відкрийте нове вікно PowerShell та перейдіть до директорії фронтенду:**
   ```powershell
   cd frontend
   ```

2. **Встановіть залежності:**
   ```powershell
   npm install
   ```

3. **Запустіть розробческий сервер:**
   ```powershell
   npm start
   ```
   Додаток буде доступний за адресою http://localhost:3000

## Налаштування VPN для доступу до Allegro.pl

Оскільки Allegro.pl може блокувати доступ з певних регіонів, вам може знадобитися VPN. Для Windows рекомендується використовувати будь-який VPN-сервіс, який дозволяє підключатися до серверів у Польщі.

### Рекомендовані VPN сервіси:
- **ExpressVPN** - має сервери в Польщі
- **NordVPN** - має сервери в Польщі
- **CyberGhost** - має сервери в Польщі
- **Proton VPN** - безкоштовний план з обмеженнями

## Використання

1. Відкрийте браузер та перейдіть за адресою http://localhost:3000
2. Введіть назву товару у полі пошуку (наприклад, "iPhone 13")
3. Натисніть кнопку "Пошук"
4. Зачекайте завантаження результатів з усіх трьох платформ
5. Перегляньте результати та натисніть "Переглянути товар", щоб перейти на сторінку товару на оригінальній маркетплейсі
6. Натисніть "Копіювати опис", щоб скопіювати деталі товару у буфер обміну для легкого поширення

## Вирішення проблем

### Помилка "Execution of scripts is disabled on this system"
**Рішення:** Запустіть PowerShell як адміністратор та виконайте одну з команд:
```powershell
Set-ExecutionPolicy RemoteSigned
```
або запустіть скрипт з параметром:
```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

### Помилка активації віртуального середовища
**Рішення:** Переконайтеся, що ви запускаєте PowerShell, а не Command Prompt

### Помилка "flask is not recognized as an internal or external command"
**Рішення:** Переконайтеся, що віртуальне середовище активоване та Flask встановлений

### Помилка "npm is not recognized as an internal or external command"
**Рішення:** Переконайтеся, що Node.js встановлений та доданий до PATH

### Помилка "python is not recognized as an internal or external command"
**Рішення:** 
1. Встановіть Python з [python.org](https://www.python.org/downloads/)
2. Під час встановлення обов'язково поставте галочку "Add Python to PATH"
3. Перезапустіть PowerShell після встановлення

### Порти зайняті
Якщо порти 3000 або 5001 зайняті іншими додатками:

**Для Flask (порт 5001):**
```powershell
flask run --port=5002
```

**Для React (порт 3000):**
Змініть порт в package.json або встановіть змінну середовища:
```powershell
$env:PORT = "3001"
npm start
```

### Проблеми з Playwright
Якщо Playwright не може встановити браузери:
```powershell
playwright install --with-deps
```

## Зупинка додатку

Щоб зупинити додаток, натисніть `Ctrl+C` в вікні PowerShell, де запущений скрипт. Це автоматично зупинить всі фонові процеси.

## Додаткові поради

1. **Використовуйте Windows Terminal** для кращого досвіду роботи з PowerShell
2. **Встановіть Git for Windows** для роботи з репозиторієм
3. **Використовуйте VSCode** як редактор коду з розширеннями для Python та React
4. **Регулярно оновлюйте** Python, Node.js та npm до останніх версій

## Підтримка

Якщо у вас виникли проблеми, які не описані в цьому керівництві:

1. Перевірте, чи встановлені всі необхідні залежності
2. Переконайтеся, що порти 3000 та 5001 не зайняті
3. Спробуйте перезапустити PowerShell як адміністратор
4. Перевірте логи помилок у вікні PowerShell
