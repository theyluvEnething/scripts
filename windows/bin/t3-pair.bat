@echo off
setlocal
rem t3-pair.py lives in windows\ but imports utilkit from shared\
set "PYTHONPATH=%~dp0..\..\shared;%PYTHONPATH%"
python "%~dp0..\t3-pair.py" %*
