#!/usr/bin/env python3
"""
Tiflogram: har bir build'da APK versionCode'ini MAJBURIY oshiradi.

MUHIM TUZATISH: avvalgi versiya TMessagesProj/build.gradle dagi
"defaultConfig.versionCode = <raqam>" ni o'zgartirgan edi - bu esa
kutubxona moduli, YAKUNIY APK'ga ta'sir qilmaydi. Haqiqiy manba:

    gradle.properties:  APP_VERSION_CODE=<raqam>
    TMessagesProj_App/build.gradle:
        defaultConfig.versionCode = Integer.parseInt(APP_VERSION_CODE)
        output.versionCodeOverride = defaultConfig.versionCode * 10
                                      + variant.productFlavors.get(0).abiVersionCode

Ya'ni asl manba - "gradle.properties" dagi APP_VERSION_CODE. Shuni
oshiramiz (build har doim bir xil flavor - "Afat" - bilan qurilgani
uchun *10+abiVersionCode qismi barqaror qo'shiladi, tartib buzilmaydi).

Ishlatish: patch_version_code.py <run_number>
"""

import re
import sys
from pathlib import Path

TARGET = "gradle.properties"
MAX_VERSION_CODE = 2_100_000_000


def main():
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print("Ishlatish: patch_version_code.py <run_number>")
        sys.exit(1)
    run_number = int(sys.argv[1])

    try:
        target = Path(TARGET)
        with target.open("r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Fayl topilmadi: {TARGET}")
        sys.exit(1)

    pattern = re.compile(r"^APP_VERSION_CODE\s*=\s*(\d+)\s*$", re.MULTILINE)
    match = pattern.search(content)
    if not match:
        print("❌ 'APP_VERSION_CODE=<raqam>' qatori gradle.properties'da topilmadi")
        sys.exit(1)

    original = int(match.group(1))
    # Ko'paytirish Android versionCode limitidan tez oshib ketadi.
    new_code = max(original + 1, run_number)
    if new_code > MAX_VERSION_CODE:
        print(f"❌ Yangi versionCode Android limitidan oshdi: {new_code}")
        sys.exit(1)

    print(f"Asl APP_VERSION_CODE: {original}")
    print(f"Run number: {run_number}")
    print(f"Yangi APP_VERSION_CODE: {new_code}")

    new_content = pattern.sub(f"APP_VERSION_CODE={new_code}", content, count=1)
    with target.open("w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"✅ Yozildi: {TARGET}")
    print("✅ Endi bu APK har doim eski nusxa ustiga yangilanish sifatida o'rnatiladi.")


if __name__ == "__main__":
    main()
