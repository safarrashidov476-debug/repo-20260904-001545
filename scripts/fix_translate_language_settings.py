#!/usr/bin/env python3
"""
Tiflogram: Sozlamalar -> Til -> "Avtomatik tarjima" tugmasini
Premium'siz ham yoqib bo'ladigan qiladi.

MUHIM: bu joy avval TOPILMAGAN edi. Foydalanuvchi tarjimani
o'chirib-yoqganda "Premium kerak" chiqishining sababi shu bo'lishi
mumkin - LanguageSelectActivity.java dagi shu tugma, YOQILGANDA
(value==true) alohida Premium tekshiruvi qiladi.

Manba: TMessagesProj/src/main/java/org/telegram/ui/LanguageSelectActivity.java
Rejimlar: check / apply
"""

import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "check"

TARGET = "TMessagesProj/src/main/java/org/telegram/ui/LanguageSelectActivity.java"

OLD = '''                    } else if (position == autoTranslationPosition) {'''


def main():
    if MODE not in ("check", "apply"):
        print(f"Noma'lum rejim: {MODE}")
        sys.exit(1)

    print(f"=== Rejim: {MODE} (LanguageSelectActivity - avtomatik tarjima tugmasi) ===\n")

    try:
        with open(TARGET, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Fayl topilmadi: {TARGET}")
        sys.exit(1)

    # Bu skript aniq matn o'rniga MARKER orqali ishlaydi va butun
    # if-blokni emas, faqat "isPremium()" sharti bilan bog'liq
    # ikkita joyni moslashuvchan qidiradi.
    import re

    # 1) "if (value && !getUserConfig().isPremium())" - Premium'ga
    #    bog'liq bo'lgan shartni har doim false qilib qo'yamiz
    pattern1 = re.compile(
        r"if\s*\(\s*value\s*&&\s*!getUserConfig\(\)\.isPremium\(\)\s*\)"
    )
    # 2) qulf ikonkasi: "!getUserConfig().isPremium() ? R.drawable.permission_locked : 0"
    pattern2 = re.compile(
        r"!getUserConfig\(\)\.isPremium\(\)\s*\?\s*R\.drawable\.permission_locked\s*:\s*0"
    )

    count1 = len(pattern1.findall(content))
    count2 = len(pattern2.findall(content))

    if count1 == 0 and count2 == 0:
        print("❌ [1] LanguageSelectActivity: avtomatik tarjima Premium tekshiruvi — topilmadi")
        sys.exit(1)

    print(f"✅ [1] LanguageSelectActivity: avtomatik tarjima Premium tekshiruvi — topildi ({count1} shart, {count2} ikonka)")

    if MODE == "check":
        sys.exit(0)

    if count1 > 0:
        content = pattern1.sub("if (false)", content)
    if count2 > 0:
        content = pattern2.sub("0", content)

    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n✅ Yozildi: {TARGET}")
    print("✅ 'Avtomatik tarjima' tugmasi endi Premium'siz ham yoqiladi (qulf ikonkasi ham olib tashlandi).")


if __name__ == "__main__":
    main()
