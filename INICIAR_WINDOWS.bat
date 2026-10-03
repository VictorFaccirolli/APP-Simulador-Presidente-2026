@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 goto erro
python -m streamlit run app.py
pause
exit /b
:erro
 echo Verifique a instalacao do Python e sua conexao com a internet.
pause
