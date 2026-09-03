#!/usr/bin/env python3
"""
Tiflogram: UserConfig.smali ichida akkaunt limitini 5 taga sozlaydi
(APK ichidan baksmali orqali chiqarilgan smali faylga ishlaydi,
GitHub Actions "patch-apk.yml" workflow'i tomonidan chaqiriladi).

Ishlatish:
    python3 patch_account_limit_smali.py <UserConfig.smali yo'li>

Chiqish kodi: 0 - muvaffaqiyatli tuzatildi, 1 - kutilgan matn topilmadi.
"""

import re
import sys

MAX_N = "0x5"


def main():
    if len(sys.argv) != 2:
        print("Ishlatish: patch_account_limit_smali.py <UserConfig.smali>")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    changed = 0

    # 1) MAX_ACCOUNT_DEFAULT_COUNT va MAX_ACCOUNT_COUNT maydonlari
    for field in ("MAX_ACCOUNT_DEFAULT_COUNT", "MAX_ACCOUNT_COUNT"):
        pattern = re.compile(
            rf"(\.field public static final {field}:I = )0x[0-9a-fA-F]+"
        )
        new_content, n = pattern.subn(rf"\g<1>{MAX_N}", content)
        if n == 0:
            print(f"❌ {field} maydoni topilmadi — fayl kutilgan formatda emas")
            sys.exit(1)
        content = new_content
        changed += n
        print(f"✅ {field} -> {MAX_N} ga o'zgartirildi")

    # 2) getMaxAccountCount() metodini butunlay soddalashtiramiz:
    #    premium bor-yo'qligidan qat'i nazar doim 5 qaytaradi.
    method_pattern = re.compile(
        r"\.method public static getMaxAccountCount\(\)I.*?\.end method",
        re.DOTALL,
    )
    new_method = (
        ".method public static getMaxAccountCount()I\n"
        "    .locals 1\n"
        "\n"
        f"    const/4 v0, 0x5\n"
        "\n"
        "    return v0\n"
        ".end method"
    )
    new_content, n = method_pattern.subn(new_method, content)
    if n == 0:
        print("❌ getMaxAccountCount() metodi topilmadi — fayl kutilgan formatda emas")
        sys.exit(1)
    content = new_content
    changed += n
    print("✅ getMaxAccountCount() -> doim 5 qaytaradigan qilib almashtirildi")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n✅ Jami {changed} ta o'zgarish qo'llandi: {path}")


if __name__ == "__main__":
    main()
