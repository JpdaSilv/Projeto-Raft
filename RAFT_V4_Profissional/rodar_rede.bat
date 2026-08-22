@echo off
cd /d "%~dp0"
echo ============================================
echo       RAFT V4 - SERVIDOR NA REDE
 echo ============================================
echo.
python -m streamlit run app.py --server.address=0.0.0.0 --server.port=8501
pause
