#!/usr/bin/env python3
"""
Tiflogram: chat/kanal yuqorisidagi "Tarjima" tugmasi bosilganda
ishlaydigan Premium tekshiruvini olib tashlaydi.

MUHIM: bu — isFeatureAvailable()/isDialogTranslatable()dan MUTLAQO
ALOHIDA, uchinchi tekshiruv. fix_translate_free.py faqat tugma
KO'RINISHINI boshqaruvchi joylarni tuzatgan edi; bu yerda esa tugma
BOSILGANDA nima bo'lishi hal qilinadi. Shu joy tuzatilmagani uchun
tugma ko'rinsa ham, bosilganda hali ham Premium oynasi chiqib,
haqiqiy tarjima yoqilmagan edi.

Manba: TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java
       (createTranslateButton() -> onButtonClick())
Rejimlar: check / apply
"""

import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "check"

TARGET = "TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java"

OLD = '''                if (getUserConfig().isPremium() || currentChat != null && currentChat.autotranslation) {
                    getMessagesController().getTranslateController().toggleTranslatingDialog(getDialogId());
                } else {
                    MessagesController.getNotificationsSettings(currentAccount).edit().putInt("dialog_show_translate_count" + getDialogId(), 14).commit();
                    showDialog(new PremiumFeatureBottomSheet(ChatActivity.this, PremiumPreviewFragment.PREMIUM_FEATURE_TRANSLATIONS, false));
                }'''

NEW = '''                // Tiflogram: tarjima tugmasi Premium'siz ham ishlaydi
                getMessagesController().getTranslateController().toggleTranslatingDialog(getDialogId());'''


def main():
    if MODE not in ("check", "apply"):
        print(f"Noma'lum rejim: {MODE}")
        sys.exit(1)

    print(f"=== Rejim: {MODE} (tarjima tugmasi -> Premium tekshiruvisiz) ===\n")

    try:
        with open(TARGET, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Fayl topilmadi: {TARGET}")
        sys.exit(1)

    count = content.count(OLD)
    if count == 0:
        print("❌ Kutilgan blok topilmadi. Manba kodi o'zgargan bo'lishi mumkin.")
        sys.exit(1)
    if count > 1:
        print(f"⚠️ Kutilgan blok {count} marta uchradi, faqat birinchisi almashtiriladi.")

    print(f"✅ Topildi: {TARGET} (createTranslateButton -> onButtonClick)")

    if MODE == "check":
        sys.exit(0)

    content = content.replace(OLD, NEW, 1)
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n✅ Yozildi: {TARGET}")
    print("✅ Tarjima tugmasi endi Premium'siz ham to'g'ridan-to'g'ri yoqadi.")


if __name__ == "__main__":
    main()
