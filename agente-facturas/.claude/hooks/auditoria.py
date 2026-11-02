#!/usr/bin/env python3
"""Hook PostToolUse: bitácora de auditoría (append-only) de cada acción del agente.

Registra QUÉ se hizo (herramienta, archivo o comando), nunca el CONTENIDO de facturas,
para no duplicar datos sensibles en el log.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    evento = json.load(sys.stdin)
except Exception:
    sys.exit(0)
entrada = evento.get("tool_input", {}) or {}
detalle = entrada.get("file_path") or entrada.get("command") or entrada.get("skill") or entrada.get("pattern") or ""
registro = {
    "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "usuario": os.environ.get("USER") or os.environ.get("USERNAME") or "",
    "sesion": evento.get("session_id", ""),
    "herramienta": evento.get("tool_name", ""),
    "detalle": str(detalle)[:300],
}
logs = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / "datos" / "logs"
logs.mkdir(parents=True, exist_ok=True)
with (logs / "auditoria.jsonl").open("a", encoding="utf-8") as f:
    f.write(json.dumps(registro, ensure_ascii=False) + "\n")
sys.exit(0)
