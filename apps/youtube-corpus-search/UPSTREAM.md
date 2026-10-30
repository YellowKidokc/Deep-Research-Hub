# YouTube Apologetics Corpus Search — Hub App Wrapper

This folder is a thin launcher wrapper. The actual application lives at:

```
\\192.168.2.50\h_hp\Desktop\Youtube API CKG\youtube_corpus_search\
```

`START.bat` changes into that directory, activates its Python venv, and runs Streamlit on `127.0.0.1:8501`.

The hub's `launch.json` entry `corpus.search` calls this batch file. The hub's web frontend embeds the running Streamlit app in the **Corpus Search** screen.

Do not commit the upstream folder's contents here.
