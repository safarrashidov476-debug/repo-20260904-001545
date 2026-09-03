#!/usr/bin/env python3
"""
Xabar tovushini FAQAT ochiq chat/guruh/bot/kanal ichida chalish.

Muammo: playInChatSound() metodi xabar qaysi chatga tegishli ekanini
tekshirmaydi va foydalanuvchi hech qanday chatni ochmagan bo'lsa ham
(masalan chatlar ro'yxatida turganda) tovushni chaladi.

Yechim: metod boshida openedDialogId == 0 (hech qanday chat ochilmagan)
bo'lsa, funksiyadan darhol chiqib ketish.

Manba: TMessagesProj/src/main/java/org/telegram/messenger/NotificationsController.java
"""
import sys
from pathlib import Path

TARGET = "TMessagesProj/src/main/java/org/telegram/messenger/NotificationsController.java"

OLD = "if (!inChatSoundEnabled || MediaController.getInstance().isRecordingAudio()) {"

NEW = (
    "if (openedDialogId == 0) {\n"
    "            return;\n"
    "        }\n"
    "        if (!inChatSoundEnabled || MediaController.getInstance().isRecordingAudio()) {"
)


def apply(base: Path):
    f = base / TARGET
    if not f.exists():
        print(f"❌ Fayl topilmadi: {f}")
        sys.exit(1)
    text = f.read_text(encoding="utf-8")
    count = text.count(OLD)
    if count == 0:
        print(f"❌ Eski matn topilmadi ({TARGET}). Manba kodi o'zgargan bo'lishi mumkin.")
        sys.exit(1)
    if count > 1:
        print(f"⚠️ Eski matn {count} marta uchradi, faqat birinchisi almashtiriladi.")
    text = text.replace(OLD, NEW, 1)
    f.write_text(text, encoding="utf-8")
    print(f"✅ {TARGET} — xabar tovushi endi faqat ochiq chatda chalinadi")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    base = Path(".")
    if mode == "apply":
        apply(base)
    else:
        print("Foydalanish: fix_chat_sound_scope.py apply")
        sys.exit(1)
