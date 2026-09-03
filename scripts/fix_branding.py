#!/usr/bin/env python3
"""
Ilova nomi va paket nomini o'zgartirish (Tiflogram).
Rejimlar: check / apply (birinchi skript bilan bir xil mantiq).
Bu skript avvalgi fix_accessibility.py dan MUSTAQIL ishlaydi —
biri ishlamasa, ikkinchisiga ta'sir qilmaydi.
"""

import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "check"

FIXES = [
    {
        "id": 1,
        "label": "strings.xml: ilova nomi -> Tiflogram",
        "path": "TMessagesProj/src/main/res/values/strings.xml",
        "old": '''<string name="AppName">Telegram</string>''',
        "new": '''<string name="AppName">Tiflogram</string>''',
    },
    {
        "id": 2,
        "label": "gradle.properties: paket nomi -> uz.tiflogram.messenger",
        "path": "gradle.properties",
        "old": '''APP_PACKAGE=org.telegram.messenger''',
        "new": '''APP_PACKAGE=uz.tiflogram.messenger''',
    },
]


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def main():
    if MODE not in ("check", "apply"):
        print(f"Noma'lum rejim: {MODE}")
        sys.exit(1)

    print(f"=== Rejim: {MODE} (ilova nomi/paket nomi) ===\n")

    results = []
    file_cache = {}

    for fix in FIXES:
        path = fix["path"]
        if path not in file_cache:
            file_cache[path] = read_file(path)
        content = file_cache[path]

        if content is None:
            print(f"❌ [{fix['id']}] {fix['label']} — fayl topilmadi: {path}")
            results.append((fix, False))
            continue

        if fix["old"] not in content:
            print(f"❌ [{fix['id']}] {fix['label']} — eski matn topilmadi")
            results.append((fix, False))
            continue

        print(f"✅ [{fix['id']}] {fix['label']} — topildi")
        results.append((fix, True))

    failed = [r for r in results if not r[1]]

    if MODE == "check":
        sys.exit(1 if failed else 0)

    if failed:
        print("\n⛔ Ba'zi tuzatishlar topilmadi. Hech narsa o'zgartirilmadi.")
        sys.exit(1)

    modified = dict(file_cache)
    for fix in FIXES:
        path = fix["path"]
        modified[path] = modified[path].replace(fix["old"], fix["new"], 1)

    for path, content in modified.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Yozildi: {path}")

    print("\n✅ Ilova nomi va paket nomi muvaffaqiyatli o'zgartirildi.")


if __name__ == "__main__":
    main()
