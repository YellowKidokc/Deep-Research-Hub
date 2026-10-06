from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from engine.station_runner import legacy_main
if __name__ == "__main__":
    raise SystemExit(legacy_main("06","06_YT_WATCH","legacy_youtube","pipeline-workflows/API/deepseek-home/watch_pipeline.py"))
