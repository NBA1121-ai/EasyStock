@echo off
title EasyStock Server
cd /d "%~dp0"
python -c "from app import init_db; init_db()"
echo.
echo ========================================
echo   EasyStock запущен: http://localhost:5000
echo   Нажмите Ctrl+C чтобы остановить
echo ========================================
echo.
start http://localhost:5000
python -m waitress --host=0.0.0.0 --port=5000 app:app
pause
