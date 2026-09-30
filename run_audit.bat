@echo off
chcp 65001 >nul
title Ebook Health Check & Audit Tool
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_audit.ps1"
if %errorlevel% neq 0 pause
