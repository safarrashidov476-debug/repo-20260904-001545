#!/usr/bin/env python3
"""
Tiflogram: tarjimani Telegram serveriga (va u yerdagi Premium
tekshiruviga) umuman bog'liq bo'lmagan qilish.

MUHIM KASHFIYOT (Grok orqali, real manba kodidan tasdiqlangan):
TranslateController.pushToTranslate() metodida Telegram'ning o'zida
serverga bog'liq bo'lmagan ichki tarjima yo'li bor:

    final String method = getMessagesController().translationsAutoEnabled;
    if ("alternative".equals(method) || "system".equals(method)) {
        ... TranslateAlert2.alternativeTranslate(...) orqali tarjima ...
        return;
    }
    // shu yerdan pastda TL_messages_translateText server so'rovi boradi

Bu "alternative" yo'l - server so'rovidan OLDIN tekshiriladigan
shart, va agar shart to'g'ri kelsa, funksiya serverga umuman
so'rov yubormasdan qaytadi (return). Shuning uchun "method"
qiymatini doim "alternative" qilib qo'ysak, tarjima HECH QACHON
Telegram serveriga bormaydi - demak, Premium tekshiruvi ham
(qayerda bo'lishidan qat'i nazar) hech qachon ishga tushmaydi.

Manba: TMessagesProj/src/main/java/org/telegram/messenger/TranslateController.java
Rejimlar: check / apply
"""

import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "check"

TARGET = "TMessagesProj/src/main/java/org/telegram/messenger/TranslateController.java"

OLD = "                final String method = getMessagesController().translationsAutoEnabled;"

NEW = (
    "                // Tiflogram: serverga (va Premium tekshiruviga) umuman\n"
    "                // bog'liq bo'lmagan, ichki (on-device) tarjima majburiy\n"
    "                final String method = \"alternative\";"
)


def main():
    if MODE not in ("check", "apply"):
        print(f"Noma'lum rejim: {MODE}")
        sys.exit(1)

    print("=== Rejim: {} (tarjima -> majburiy 'alternative' yo'l) ===\n".format(MODE))

    try:
        with open(TARGET, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Fayl topilmadi: {TARGET}")
        sys.exit(1)

    count = content.count(OLD)
    if count == 0:
        print("❌ Kutilgan qator topilmadi. Manba kodi o'zgargan bo'lishi mumkin:")
        print(f"   {OLD.strip()}")
        sys.exit(1)
    if count > 1:
        print(f"⚠️ Kutilgan qator {count} marta uchradi, faqat birinchisi almashtiriladi.")

    print("✅ Topildi:")
    print(f"   {OLD.strip()}")

    if MODE == "check":
        sys.exit(0)

    content = content.replace(OLD, NEW, 1)
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n✅ Yozildi: {TARGET}")
    print("✅ Tarjima endi doim ichki ('alternative') yo'l orqali ishlaydi.")


if __name__ == "__main__":
    main()
