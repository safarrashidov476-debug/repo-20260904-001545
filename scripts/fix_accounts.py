#!/usr/bin/env python3
"""
Tiflogram: akkaunt sonini 5 taga sozlash (premium bo'lsa ham, bo'lmasa ham).

MUHIM: 5 qiymati ataylab tanlangan — native tgnet/Defines.h dagi
MAX_ACCOUNT_COUNT=5 va ConnectionsManager::getInstance() dagi switch-case
(case 0..4) hech qachon o'zgartirilmagan, standart holicha 5 tagacha
akkauntni qo'llab-quvvatlaydi. Shu sababli bu yerda native tomonga
HECH QANDAY patch kerak emas (avvalgi 10 taga oshirishda mos kelmaslik
va SIGSEGV bo'lgan edi — bu safar bunday xavf yo'q).
"""

import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "check"

MAX_N = "5"

FIXES = [
    {
        "id": 1,
        "label": "UserConfig.MAX_ACCOUNT_DEFAULT_COUNT va MAX_ACCOUNT_COUNT",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/UserConfig.java",
        "old": '''    public final static int MAX_ACCOUNT_DEFAULT_COUNT = 3;
    public final static int MAX_ACCOUNT_COUNT = 4;''',
        "new": f'''    // Tiflogram: 5 ta akkaunt (native tomon bilan mos, patch shart emas)
    public final static int MAX_ACCOUNT_DEFAULT_COUNT = {MAX_N};
    public final static int MAX_ACCOUNT_COUNT = {MAX_N};''',
    },
    {
        "id": 2,
        "label": "UserConfig.getMaxAccountCount() -> premiumdan qat'i nazar 5",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/UserConfig.java",
        "old": '''    public static int getMaxAccountCount() {
        return hasPremiumOnAccounts() ? 5 : 3;
    }''',
        "new": f'''    public static int getMaxAccountCount() {{
        // Tiflogram: premium talab qilinmaydi, doim {MAX_N}
        return {MAX_N};
    }}''',
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

    print(f"=== Rejim: {MODE} (akkaunt cheklovi) ===\n")
    results = []
    file_cache = {}

    for fix in FIXES:
        path = fix["path"]
        if path not in file_cache:
            file_cache[path] = read_file(path)
        content = file_cache[path]
        if content is None:
            print(f"❌ [{fix['id']}] {fix['label']} — fayl topilmadi")
            results.append(False)
            continue
        if fix["old"] not in content:
            if fix["new"] in content:
                print(f"✅ [{fix['id']}] {fix['label']} — topildi (allaqachon qo'llangan)")
                results.append(True)
            else:
                print(f"❌ [{fix['id']}] {fix['label']} — eski matn topilmadi")
                results.append(False)
            continue
        print(f"✅ [{fix['id']}] {fix['label']}")
        results.append(True)

    failed = results.count(False)
    print(f"\nOK: {len(results)-failed}/{len(results)}")
    if MODE == "check":
        sys.exit(1 if failed else 0)
    if failed:
        sys.exit(1)

    modified = dict(file_cache)
    for fix in FIXES:
        if fix["old"] in modified[fix["path"]]:
            modified[fix["path"]] = modified[fix["path"]].replace(fix["old"], fix["new"], 1)
    for path, content in modified.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Yozildi: {path}")
    print(f"\n✅ Akkaunt cheklovi {MAX_N} taga sozlandi (native bilan mos, xavfsiz).")


if __name__ == "__main__":
    main()
