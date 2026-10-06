@echo off
REM Optional Windows helper. Run manually after editing NAS paths if needed.
mklink /D local_models \\NAS\engines\local_models
mklink /D tts \\NAS\engines\tts
mklink /D stt \\NAS\engines\stt
