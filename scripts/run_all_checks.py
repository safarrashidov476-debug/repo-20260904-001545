#!/usr/bin/env python3
"""
Tiflogram: BARCHA fix_*.py skriptlarini bitta joyda "check" rejimida
ishga tushiradi va yig'ma natija (jadval) chiqaradi.

Maqsad: har safar APK qurib, birma-bir xato topib charchash o'rniga —
push qilishdan OLDIN (yoki workflow ichida pre-check bosqichi sifatida)
BARCHA fix'larning holatini bir marta ko'rish.

HECH QANDAY FAYLGA YOZMAYDI — faqat tekshiradi (check rejimi, xavfsiz).

Ishlatish (repo tub papkasidan):
    python3 scripts/run_all_checks.py

Chiqish kodi: 0 - hammasi OK, 1 - kamida bitta fix mos kelmadi.
"""

import importlib.util
import re
import subprocess
import sys
from pathlib import Path
try:
    from patchlib import source_root, find_file
except ImportError:
    from scripts.patchlib import source_root, find_file

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
try:
    SOURCE_ROOT = source_root()
except (FileNotFoundError, RuntimeError):
    SOURCE_ROOT = REPO_ROOT

# check/apply (FIXES-ro'yxat) uslubidagi skriptlar — bular "check" argumenti
# bilan xavfsiz ishga tushadi (fayl yozmaydi).
LIST_STYLE_SCRIPTS = [
    "fix_accessibility.py",
    "fix_accounts.py",
    "fix_ads.py",
    "fix_branding.py",
    "fix_download.py",
    "fix_gemini.py",
    "fix_translate_free.py",  # v2: endi FIXES-ro'yxatli, TranslateController.java'ni nishonlaydi
    "fix_translate_language_settings.py",
]

# OLD/NEW/TARGET uslubidagi skriptlar — bularda haqiqiy "check" rejimi yo'q
# (faqat "apply"), shuning uchun modulni import qilib (fayl yozmasdan)
# o'zimiz tekshiramiz.
SIMPLE_STYLE_SCRIPTS = [
    "fix_chat_sound_scope.py",
    "fix_translate_alternative.py",
    "fix_translate_button.py",
]

RESULT_LINE_RE = re.compile(r"^(✅|❌)\s*\[([^\]]+)\]\s*(.+)$")


def build_flexible_pattern(old_str: str) -> re.Pattern:
    """Bo'sh joy/tab farqiga sezgir bo'lmagan regex quradi (fix_ads.py v2 bilan bir xil mantiq)."""
    lines = old_str.split("\n")
    line_patterns = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            line_patterns.append(r"[ \t]*")
            continue
        tokens = stripped.split()
        escaped = r"\s+".join(re.escape(tok) for tok in tokens)
        line_patterns.append(r"[ \t]*" + escaped + r"[ \t]*")
    return re.compile(r"\r?\n[ \t]*".join(line_patterns))


def find_match(content: str, old_str: str):
    if old_str in content:
        return "aniq"
    if build_flexible_pattern(old_str).search(content):
        return "moslashuvchan"
    return None


def check_list_style_script(script_name: str):
    """Skriptni subprocess orqali 'check' rejimida ishga tushiradi (fayl yozmaydi)."""
    script_path = SCRIPTS_DIR / script_name
    rows = []
    if not script_path.exists():
        return [(script_name, "-", False, "skript topilmadi", "-")]

    try:
        proc = subprocess.run(
            [sys.executable, str(script_path), "check"],
            cwd=str(SOURCE_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception as e:
        return [(script_name, "-", False, f"ishga tushmadi: {e}", "-")]

    for line in proc.stdout.splitlines():
        m = RESULT_LINE_RE.match(line.strip())
        if m:
            mark, fid, label = m.groups()
            rows.append((script_name, fid, mark == "✅", label, "subprocess"))

    if not rows:
        # Skript natijani kutilgan formatda chiqarmadi — xom chiqishini ko'rsatamiz
        ok = proc.returncode == 0
        summary = (proc.stdout.strip().splitlines() or ["(bo'sh chiqish)"])[-1]
        rows.append((script_name, "-", ok, f"natija formati kutilmagan: {summary}", "subprocess"))

    return rows


def check_simple_style_script(script_name: str):
    """OLD/TARGET uslubidagi skript uchun: modulni import qilib (yozmasdan) o'zimiz tekshiramiz."""
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        return [(script_name, "-", False, "skript topilmadi", "-")]

    try:
        spec = importlib.util.spec_from_file_location(script_path.stem, script_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # xavfsiz: apply() faqat __main__ blokida chaqiriladi
    except Exception as e:
        return [(script_name, "-", False, f"import xatosi: {e}", "-")]

    old = getattr(mod, "OLD", None)
    target = getattr(mod, "TARGET", None)
    if old is None or target is None:
        return [(script_name, "-", False, "OLD/TARGET topilmadi", "-")]

    try:
        full_path = find_file((target,), SOURCE_ROOT)
    except Exception as e:
        return [(script_name, "1", False, f"fayl topilmadi: {target} ({e})", "-")]

    content = full_path.read_text(encoding="utf-8")
    how = find_match(content, old)
    doc_lines = [ln.strip() for ln in (mod.__doc__ or "").strip().splitlines() if ln.strip()]
    label = doc_lines[0] if doc_lines else script_name
    return [(script_name, "1", how is not None, f"{label} ({target})", how or "topilmadi")]


def main():
    all_rows = []
    for s in LIST_STYLE_SCRIPTS:
        all_rows.extend(check_list_style_script(s))
    for s in SIMPLE_STYLE_SCRIPTS:
        all_rows.extend(check_simple_style_script(s))

    name_w = max(len(r[0]) for r in all_rows) + 1
    id_w = max(len(str(r[1])) for r in all_rows) + 1

    print("=" * 100)
    print("TIFLOGRAM — BARCHA FIX'LAR UCHUN YIG'MA TEKSHIRUV (hech narsa yozilmadi)")
    print("=" * 100)

    fails = 0
    for script, fid, ok, label, how in all_rows:
        mark = "✅" if ok else "❌"
        if not ok:
            fails += 1
        print(f"{mark} {script:<{name_w}} [{str(fid):<{id_w}}] {label}  ({how})")

    print("-" * 100)
    print(f"Jami: {len(all_rows)}, muvaffaqiyatli: {len(all_rows) - fails}, xato: {fails}")

    if fails:
        print("\n⛔ Quyidagi skriptlarda muammo bor — build qilishdan oldin shularni tuzating:")
        seen = set()
        for script, fid, ok, label, how in all_rows:
            if not ok and script not in seen:
                seen.add(script)
                print(f"   - {script}")
        sys.exit(1)

    print("\n✅ Hammasi OK — xavfsiz build qilishingiz mumkin.")
    sys.exit(0)


if __name__ == "__main__":
    main()
