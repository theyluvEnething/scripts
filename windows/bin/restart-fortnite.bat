@echo off
setlocal
rem restart-fortnite.py lives in windows\ but imports utilkit from shared\
set "PYTHONPATH=%~dp0..\..\shared;%PYTHONPATH%"
python "%~dp0..\restart-fortnite.py" %*
