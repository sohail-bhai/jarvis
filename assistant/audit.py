import json
import threading
import uuid
from pathlib import Path
import re
import datetime

_log_lock = threading.Lock()
_audit_path = None
_max_bytes = 5_000_000
_backup_count = 20

def configure(path: Path, max_bytes: int, backup_count: int) -> None:
    global _audit_path, _max_bytes, _backup_count
    _audit_path = Path(path)
    _max_bytes = max_bytes
    _backup_count = backup_count
    if _audit_path:
        _audit_path.parent.mkdir(parents=True, exist_ok=True)

def _roll_logs():
    if not _audit_path or not _audit_path.exists():
        return
    if _audit_path.stat().st_size < _max_bytes:
        return
        
    for i in range(_backup_count - 1, 0, -1):
        sfn = _audit_path.with_name(f"{_audit_path.name}.{i}")
        dfn = _audit_path.with_name(f"{_audit_path.name}.{i + 1}")
        if sfn.exists():
            if dfn.exists():
                dfn.unlink()
            sfn.rename(dfn)
            
    dfn = _audit_path.with_name(f"{_audit_path.name}.1")
    if dfn.exists():
        dfn.unlink()
    _audit_path.rename(dfn)

def append(record: dict) -> str:
    audit_id = uuid.uuid4().hex[:8]
    record["audit_id"] = audit_id
    record["ts"] = datetime.datetime.now().timestamp()
    record["iso"] = datetime.datetime.now().astimezone().isoformat()
    
    if not _audit_path:
        return audit_id
        
    line = json.dumps(record, ensure_ascii=False) + "\n"
    
    with _log_lock:
        try:
            _roll_logs()
            with open(_audit_path, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
        except Exception as e:
            pass
            
    return audit_id

_redact_pattern = re.compile(r'(?i)pass|password|app_password|token|secret|api_key|credential')

def redact(args: dict, max_len: int = 200) -> str:
    redacted = {}
    for k, v in args.items():
        if _redact_pattern.search(k):
            redacted[k] = "***"
        else:
            redacted[k] = v
            
    s = str(redacted)
    if len(s) > max_len:
        s = s[:max_len] + "..."
    return s
