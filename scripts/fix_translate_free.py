#!/usr/bin/env python3
"""
Tiflogram: tarjima (Translate) funksiyasini Premium'siz ham ishlaydigan qiladi.

MUHIM (v2 - to'g'ri faylga ko'chirildi):
Eski versiya MessagesController.java dagi
"return UserConfig.getInstance(currentAccount).isPremium() || user.premium;"
qatorini qidirar edi. Bu ENDI NOTO'G'RI edi - Grok orqali tekshirilgan
haqiqiy DrKLO/Telegram manba kodida tarjima huquqi tekshiruvi butunlay
boshqa faylga - TranslateController.java ga ko'chirilgan ekan
(MessagesController.java da faqat "getTranslateController()" getter bor).

Asosiy "eshik" ikkita metod:
  - isFeatureAvailable()
  - isFeatureAvailable(long dialogId)
Ikkalasi ham UserConfig.isPremium() ni tekshiradi. Bu skript ikkalasini
ham Premium tekshiruvisiz ishlaydigan qiladi, lekin isChatTranslateEnabled()
(umumiy feature-flag) tekshiruvini SAQLAB QOLADI - ya'ni funksiya butunlay
o'chirilgan bo'lsa (server/remote config orqali), baribir o'chiq qoladi;
faqat "Premium kerak" cheklovi olib tashlanadi.

Rejimlar: check / apply
"""

import re
import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "check"

TRANSLATE_CONTROLLER_PATH = "TMessagesProj/src/main/java/org/telegram/messenger/TranslateController.java"

FIXES = [
    {
        "id": 1,
        "label": "TranslateController.isFeatureAvailable() -> Premium'siz ham ishlaydi",
        "path": TRANSLATE_CONTROLLER_PATH,
        "old": '''public boolean isFeatureAvailable() {
    return isChatTranslateEnabled() && UserConfig.getInstance(currentAccount).isPremium();
}''',
        "new": '''    public boolean isFeatureAvailable() {
        // Tiflogram: tarjima Premium'siz ham ishlaydi
        return isChatTranslateEnabled();
    }''',
    },
    {
        "id": 2,
        "label": "TranslateController.isFeatureAvailable(dialogId) -> Premium'siz ham ishlaydi",
        "path": TRANSLATE_CONTROLLER_PATH,
        "old": '''public boolean isFeatureAvailable(long dialogId) {
    if (!isChatTranslateEnabled()) {
        return false;
    }
    final TLRPC.Chat chat = getMessagesController().getChat(-dialogId);
    return (
        UserConfig.getInstance(currentAccount).isPremium() ||
        chat != null && chat.autotranslation
    );
}''',
        "new": '''    public boolean isFeatureAvailable(long dialogId) {
        // Tiflogram: tarjima Premium'siz ham ishlaydi
        return isChatTranslateEnabled();
    }''',
    },
    {
        "id": 3,
        "label": "TranslateController.isChatTranslateEnabled() -> remote 'disabled'ga bog'liq emas",
        "path": TRANSLATE_CONTROLLER_PATH,
        "old": '''public boolean isChatTranslateEnabled() {
    if (!getMessagesController().isTranslationsAutoEnabled()) {
        return false;
    }
    if (chatTranslateEnabled == null) {
        chatTranslateEnabled = messagesController.getMainSettings().getBoolean("translate_chat_button", true);
    }
    return chatTranslateEnabled;
}''',
        "new": '''    public boolean isChatTranslateEnabled() {
        // Tiflogram: remote sozlama "disabled" bo'lsa ham e'tiborsiz qoldiramiz
        if (chatTranslateEnabled == null) {
            chatTranslateEnabled = messagesController.getMainSettings().getBoolean("translate_chat_button", true);
        }
        return chatTranslateEnabled;
    }''',
    },
]


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def build_flexible_pattern(old_str):
    """Bo'sh joy/tab farqiga sezgir bo'lmagan regex (fix_ads.py bilan bir xil mantiq)."""
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


def find_match(content, old_str):
    if old_str in content:
        idx = content.index(old_str)
        return content[idx:idx + len(old_str)], "aniq"
    pattern = build_flexible_pattern(old_str)
    m = pattern.search(content)
    if m:
        return m.group(0), "moslashuvchan (whitespace-tolerant)"
    return None, None


def main():
    if MODE not in ("check", "apply"):
        print(f"Noma'lum rejim: {MODE}. 'check' yoki 'apply' bo'lishi kerak.")
        sys.exit(1)

    print(f"=== Rejim: {MODE} (tarjima Premium cheklovini olib tashlash) ===\n")

    results = []
    file_cache = {}
    matched_spans = {}

    for fix in FIXES:
        path = fix["path"]
        if path not in file_cache:
            file_cache[path] = read_file(path)
        content = file_cache[path]

        if content is None:
            print(f"❌ [{fix['id']}] {fix['label']} — fayl topilmadi: {path}")
            results.append((fix, False, "fayl topilmadi"))
            continue

        matched_text, how = find_match(content, fix["old"])
        if matched_text is None:
            print(f"❌ [{fix['id']}] {fix['label']} — eski matn topilmadi (moslashuvchan qidiruvda ham)")
            results.append((fix, False, "eski matn topilmadi"))
            continue

        print(f"✅ [{fix['id']}] {fix['label']} — topildi ({how} moslik)")
        results.append((fix, True, None))
        matched_spans[fix["id"]] = (path, matched_text)

    failed = [r for r in results if not r[1]]

    print("\n=== Xulosa ===")
    print(f"Jami: {len(results)}, muvaffaqiyatli: {len(results) - len(failed)}, xato: {len(failed)}")

    if failed:
        print("\nXato bo'lgan tuzatishlar:")
        for fix, ok, reason in failed:
            print(f"  - [{fix['id']}] {fix['label']}: {reason}")

    if MODE == "check":
        sys.exit(1 if failed else 0)

    if failed:
        print("\n⛔ Ba'zi tuzatishlar topilmadi. Hech narsa o'zgartirilmadi (all-or-nothing).")
        sys.exit(1)

    print("\n=== Qo'llanmoqda ===")
    modified_content = dict(file_cache)

    for fix in FIXES:
        path = fix["path"]
        _, real_old_text = matched_spans[fix["id"]]
        modified_content[path] = modified_content[path].replace(real_old_text, fix["new"], 1)

    for path, content in modified_content.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Yozildi: {path}")

    print("\n✅ Barcha tarjima tuzatishlari muvaffaqiyatli qo'llandi.")


if __name__ == "__main__":
    main()
