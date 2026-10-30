@echo off
setlocal

cd /d "\\192.168.2.50\h_hp\Desktop\Youtube API CKG\youtube_corpus_search"
call .venv\Scripts\activate.bat
streamlit run app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true
