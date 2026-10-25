@echo off
rem Records the run, then starts the command named like this file: see shared\run.py.
python "%~dp0..\..\shared\run.py" %~n0 %*
