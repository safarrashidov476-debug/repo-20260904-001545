#!/usr/bin/env python3
"""Common helpers for Tiflogram source patches.

The Telegram checkout is intentionally not bundled with this repository.  These
helpers locate it at runtime and make every patch fail closed (no partial writes).
"""
from pathlib import Path
import os, re, tempfile

JAVA_ROOTS = ("TMessagesProj/src/main/java", "app/src/main/java", "src/main/java")
RES_ROOTS = ("TMessagesProj/src/main/res", "app/src/main/res", "src/main/res")

def source_root(start=None):
    start = Path(start or os.environ.get("TELEGRAM_SRC", Path.cwd())).resolve()
    candidates = [start] + list(start.parents)
    for root in candidates:
        if (root / "settings.gradle").exists() or (root / "settings.gradle.kts").exists():
            return root
    # permit invocation from a module directory
    for p in start.rglob("settings.gradle") if start.exists() else ():
        return p.parent
    raise FileNotFoundError("Telegram source root topilmadi; TELEGRAM_SRC ni belgilang")

def find_file(relpaths, root=None):
    root = source_root(root)
    for rel in relpaths:
        p = root / rel
        if p.is_file(): return p
    name = Path(relpaths[0]).name
    matches = list(root.rglob(name))
    if len(matches) == 1: return matches[0]
    if not matches: raise FileNotFoundError(name)
    # Prefer the Telegram app module over generated/build copies.
    matches = [p for p in matches if "/build/" not in p.as_posix()]
    if len(matches) == 1: return matches[0]
    raise RuntimeError(f"{name} uchun bir nechta kandidat topildi: {matches}")

def replace_once(path, old, new):
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise ValueError(f"{path}: kutilgan 1 ta moslik o'rniga {count} ta topildi")
    return text.replace(old, new, 1)

def atomic_write(path, text):
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f: f.write(text)
        os.replace(tmp, path)
    except Exception:
        try: os.unlink(tmp)
        except OSError: pass
        raise

def apply_fixes(fixes, root=None, mode="check"):
    """Validate all fixes first, then atomically write all changed files."""
    prepared = {}
    errors = []
    for fix in fixes:
        try:
            path = find_file(fix["paths"], root)
            text = prepared.get(path, path.read_text(encoding="utf-8"))
            if text.count(fix["old"]) != 1:
                raise ValueError(f"{path}: mosliklar soni {text.count(fix['old'])}, 1 bo'lishi kerak")
            prepared[path] = text.replace(fix["old"], fix["new"], 1)
            print(f"✅ [{fix['id']}] {path}")
        except Exception as e:
            errors.append(f"❌ [{fix['id']}] {e}")
            print(errors[-1])
    if errors: raise SystemExit(1)
    if mode == "apply":
        for path, text in prepared.items(): atomic_write(path, text)
        print(f"✅ {len(prepared)} ta fayl yozildi")
    else: print("✅ check OK; hech narsa yozilmadi")
