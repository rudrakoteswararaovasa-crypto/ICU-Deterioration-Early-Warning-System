@echo off
title GitHub Repository Setup & Push
echo ============================================================
echo  ICU Deterioration Early-Warning System - GitHub Deploy
echo ============================================================
echo.
cd /d "%~dp0"
set GIT="C:\Users\rudra\.gemini\antigravity\mingit\cmd\git.exe"
set GH="C:\Users\rudra\.gemini\antigravity\gh\gh.exe"

echo [1/3] Ensuring main branch...
%GIT% branch -M main

echo [2/3] Checking GitHub CLI Authentication...
%GH% auth status
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Please log in to GitHub by following the prompt below:
    %GH% auth login
)

echo [3/3] Creating GitHub Repository 'ICU-Deterioration-Early-Warning-System' & Pushing...
%GH% repo create "ICU-Deterioration-Early-Warning-System" --public --source=. --remote=origin --push

echo.
echo ============================================================
echo  SUCCESS! Your repository is live on GitHub.
echo ============================================================
pause
