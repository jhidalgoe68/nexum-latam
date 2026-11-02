#!/usr/bin/env python3
"""Hook PreToolUse: barrera dura que se aplica aunque el modelo sea engañado (p. ej. por una factura maliciosa).

Bloquea (exit 2):
- Leer secretos: datos/.secretos, .env, llaves SSH/nube.
- Escribir/editar fuera de datos/salida, datos/maestros o el código del proyecto.
- Modificar los originales: datos/entrada y datos/banco son de solo lectura.
- Comandos de red, borrado o exfiltración desde Bash.
"""
import json
import os
import re
import sys
from pathlib import Path

evento = json.load(sys.stdin)
herramienta = evento.get("tool_name", "")
entrada = evento.get("tool_input", {}) or {}
raiz = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()

SECRETOS = re.compile(r"(\.secretos|\.env\b|token_cache|id_rsa|\.ssh|\.aws|\.azure|credentials)", re.I)
ORIGINALES = ("datos/entrada", "datos/banco")
ESCRITURA_OK = ("datos/salida", "datos/maestros", "scripts", ".claude/skills", "tests")
BASH_PROHIBIDO = re.compile(
    r"(\bcurl\b|\bwget\b|\bnc\b|\bssh\b|\bscp\b|\brsync\b|\bftp\b|Invoke-WebRequest|\brm\s|\bshred\b|"
    r"\bmv\s+[^|;]*datos/(entrada|banco)|>\s*datos/(entrada|banco)|base64\s|\bgit\s+push\b|\bmail\b|\bsendmail\b|Send-MailMessage)", re.I)


def bloquear(motivo: str) -> None:
    print(f"Bloqueado por política de seguridad del agente de facturas: {motivo}", file=sys.stderr)
    sys.exit(2)


def relativa(ruta: str) -> str:
    p = Path(ruta)
    p = (raiz / p if not p.is_absolute() else p).resolve()
    try:
        return p.relative_to(raiz).as_posix()
    except ValueError:
        return "../" + p.as_posix()  # fuera del proyecto


if herramienta == "Read":
    if SECRETOS.search(entrada.get("file_path", "")):
        bloquear("lectura de secretos")

elif herramienta in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
    rel = relativa(entrada.get("file_path") or entrada.get("notebook_path") or "")
    if rel.startswith("../"):
        bloquear(f"escritura fuera del proyecto ({rel})")
    if rel.startswith(ORIGINALES):
        bloquear("los originales (facturas recibidas y extractos) son inmutables")
    if SECRETOS.search(rel):
        bloquear("escritura en archivos de secretos")
    if not rel.startswith(ESCRITURA_OK):
        bloquear(f"solo se permite escribir en {', '.join(ESCRITURA_OK)}")

elif herramienta == "Bash":
    comando = entrada.get("command", "")
    if SECRETOS.search(comando):
        bloquear("el comando toca secretos")
    if BASH_PROHIBIDO.search(comando):
        bloquear("comando de red, borrado o exfiltración no permitido")

sys.exit(0)
