#!/usr/bin/env python3
"""
Tiflogram: Gemini yordamchisi - FAQAT "3 nuqta" menyusida (Sozlamalar ->
Maxfiylik bo'limida emas). Skanerlash (shubhali kanal/guruh/bot) ham shu
oyna ichida, savol orqali ishga tushadi (masalan "kanallarni tekshir").
Rejimlar: check / apply
"""

import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "check"


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

    print(f"=== Rejim: {MODE} (Gemini - faqat 3 nuqta menyusi) ===\n")

    dlg_path = "TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java"
    dlg = read_file(dlg_path)
    if dlg is None:
        print(f"❌ Fayl topilmadi: {dlg_path}")
        sys.exit(1)

    old_io = '''        io.add(R.drawable.outline_groups_24, getString(R.string.NewGroup), () -> {
            Bundle args = new Bundle();
            presentFragment(new GroupCreateActivity(args));
        });'''
    new_io = '''        io.add(R.drawable.msg_bot, "Gemini", () -> {
            org.telegram.messenger.GeminiSafetyScanner.openAssistant(DialogsActivity.this, currentAccount);
        });
        io.add(R.drawable.outline_groups_24, getString(R.string.NewGroup), () -> {
            Bundle args = new Bundle();
            presentFragment(new GroupCreateActivity(args));
        });'''

    count = dlg.count(old_io)
    if count == 0:
        if 'GeminiSafetyScanner.openAssistant(DialogsActivity.this' in dlg:
            print("✅ [1] DialogsActivity: 3 nuqta Gemini — topildi (allaqachon qo'llangan)")
            sys.exit(0)
        print("❌ [1] DialogsActivity: 3 nuqta Gemini — joyi topilmadi")
        sys.exit(1)

    print("✅ [1] DialogsActivity: 3 nuqta Gemini")
    if MODE == "check":
        sys.exit(0)

    dlg = dlg.replace(old_io, new_io, 1)
    with open(dlg_path, "w", encoding="utf-8") as f:
        f.write(dlg)
    print(f"✅ Yozildi: {dlg_path}")
    print("\n✅ Gemini - faqat 3 nuqta menyusida ulandi (Maxfiylik bo'limiga tegilmadi)")


if __name__ == "__main__":
    main()
