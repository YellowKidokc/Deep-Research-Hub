from __future__ import annotations

import importlib.util
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "04_config" / "actions.json"
ACTIONS_DIR = ROOT / "08_actions"
LOG_PATH = ROOT / "05_logs" / "actions.log"


@dataclass(frozen=True)
class ActionDefinition:
    id: str
    name: str
    module: str
    description: str = ""


class ActionRegistry:
    def __init__(self, config_path: Path = CONFIG_PATH, actions_dir: Path = ACTIONS_DIR) -> None:
        self.config_path = config_path
        self.actions_dir = actions_dir
        self._actions: dict[str, ActionDefinition] = {}
        self._processors: dict[str, Callable[[dict[str, Any]], str]] = {}
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
        self.reload()

    def reload(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Action config not found: {self.config_path}")
        raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        self._actions = {item["id"]: ActionDefinition(**item) for item in raw}
        self._processors.clear()

    def list_actions(self) -> list[ActionDefinition]:
        return list(self._actions.values())

    def get(self, action_id: str) -> ActionDefinition:
        try:
            return self._actions[action_id]
        except KeyError as exc:
            raise KeyError(f"Unknown action: {action_id}") from exc

    def run(self, action_id: str, data: dict[str, Any]) -> str:
        action = self.get(action_id)
        processor = self._load_processor(action)
        payload = dict(data)
        payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        try:
            result = processor(payload)
        except Exception:
            logging.exception("action_failed id=%s", action_id)
            raise
        logging.info("action_complete id=%s selection_len=%s clipboard_len=%s result_len=%s", action_id, len(payload.get("selection") or ""), len(payload.get("clipboard") or ""), len(result or ""))
        return str(result)

    def _load_processor(self, action: ActionDefinition) -> Callable[[dict[str, Any]], str]:
        if action.id in self._processors:
            return self._processors[action.id]
        module_path = self.actions_dir / f"{action.module}.py"
        if not module_path.exists():
            raise FileNotFoundError(f"Action module not found for {action.id}: {module_path}")
        spec = importlib.util.spec_from_file_location(f"stratum_action_{action.module}", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not import action module: {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        process = getattr(module, "process", None)
        if not callable(process):
            raise AttributeError(f"Action module must expose process(data: dict) -> str: {module_path}")
        self._processors[action.id] = process
        return process
