@echo off
echo === Установка зависимостей Python ===

echo Очистка старых зависимостей...
pip uninstall googletrans -y 2>nul
pip uninstall httpx -y 2>nul

echo Установка зависимостей...
pip install -r requirements.txt

echo === Установка завершена ===
echo Теперь можно запускать: python app.py
pause 