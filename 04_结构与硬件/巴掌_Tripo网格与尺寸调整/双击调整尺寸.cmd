@echo off
chcp 65001 >nul
"%~dp0..\cad_runtime\Scripts\python.exe" "%~dp0adjust.py"
