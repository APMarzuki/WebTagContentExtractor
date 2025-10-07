@echo off
echo Starting WebTagContent Extractor GUI...
cd /d %~dp0..
python gui/main_window.py
pause