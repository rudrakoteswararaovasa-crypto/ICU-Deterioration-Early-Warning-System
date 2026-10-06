@echo off
title ICU Early-Warning System Launcher
echo ============================================================
echo   ICU Patient Deterioration Early-Warning System
echo ============================================================
echo Starting Local Web Dashboard and API Server...
cd /d "%~dp0"
python serve.py
pause
