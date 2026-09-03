#!/usr/bin/env python3
"""
Telegram Android uchun sponsor (reklama) xabarlarini o'chirish.
Kanal va botlardagi sponsored messages + video reklamalarni bloklaydi.
Rejimlar: check / apply

MUHIM (v2, whitespace-tolerant):
Avvalgi versiya "eski matn topilmadi" xatosi berdi, chunki str.replace()
aniq bo'shliq (space/tab) va chekinishga qattiq bog'liq edi.
Grok orqali tekshirilgan haqiqiy DrKLO/Telegram manba kodi bilan
solishtirilganda MANTIQ/MATN O'ZGARMAGAN — faqat indentation/whitespace
farq qilishi mumkin ekan. Shuning uchun bu versiya har bir qatorni
alohida "strip" qilib taqqoslaydi (regex orqali), bo'sh joy farqidan
qat'i nazar haqiqiy kodni topadi. Java bo'shliqqa sezgir emas, shuning
uchun bu 100% xavfsiz - faqat topish ishonchliligini oshiradi, kodning
o'zini emas.
"""

import re
import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "check"

FIXES = [
    {
        "id": 1,
        "label": "MessagesController.isSponsoredDisabled() -> har doim true",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/MessagesController.java",
        "old": '''public boolean isSponsoredDisabled() {
    TLRPC.UserFull userFull = getUserFull(getUserConfig().getClientUserId());
    if (userFull == null) return false;
    return !userFull.sponsored_enabled;
}''',
        "new": '''    public boolean isSponsoredDisabled() {
        // Tiflogram: reklamalarni o'chirish
        return true;
    }''',
    },
    {
        "id": 2,
        "label": "MessagesController.getSponsoredMessages() -> null",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/MessagesController.java",
        "old": '''public SponsoredMessagesInfo getSponsoredMessages(long dialogId) {
    SponsoredMessagesInfo info = sponsoredMessages.get(dialogId);''',
        "new": '''    public SponsoredMessagesInfo getSponsoredMessages(long dialogId) {
        // Tiflogram: reklamalarni o'chirish - hech qachon so'ramaymiz
        boolean tiflogramDisableAds = true;
        if (tiflogramDisableAds) {
            return null;
        }
        SponsoredMessagesInfo info = sponsoredMessages.get(dialogId);''',
    },
    {
        "id": 3,
        "label": "ChatActivity.addSponsoredMessages() -> darhol return",
        "path": "TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java",
        "old": '''private void addSponsoredMessages(boolean animated) {
    if (sponsoredMessagesAdded || chatMode != 0 || !ChatObject.isChannel(currentChat) && !UserObject.isBot(currentUser) || !forwardEndReached[0] || getUserConfig().isPremium() && getMessagesController().isSponsoredDisabled() || isReport()) {
        return;
    }''',
        "new": '''    private void addSponsoredMessages(boolean animated) {
        // Tiflogram: reklamalarni o'chirish
        boolean tiflogramDisableAds = true;
        if (tiflogramDisableAds || sponsoredMessagesAdded || chatMode != 0 || !ChatObject.isChannel(currentChat) && !UserObject.isBot(currentUser) || !forwardEndReached[0] || getUserConfig().isPremium() && getMessagesController().isSponsoredDisabled() || isReport()) {
            return;
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
    """
    old_str dagi har bir qatorni "strip" qilib, orasidagi bo'sh joy/tab
    farqiga sezgir bo'lmagan regex quradi. Qator ICHIDAGI bo'shliqlar
    (masalan operatorlar orasida) aniq bitta yoki ko'p bo'sh joy sifatida
    moslashtiriladi, lekin so'zlar/belgilar ketma-ketligi o'zgarmaydi.
    """
    lines = old_str.split("\n")
    line_patterns = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            line_patterns.append(r"[ \t]*")
            continue
        # ichki bo'sh joylarni \s+ ga almashtirib, qolganini escape qilamiz
        tokens = stripped.split()
        escaped = r"\s+".join(re.escape(tok) for tok in tokens)
        line_patterns.append(r"[ \t]*" + escaped + r"[ \t]*")
    # qatorlar orasida CRLF yoki LF bo'lishi mumkin
    pattern = r"\r?\n[ \t]*".join(line_patterns)
    return re.compile(pattern)


def find_match(content, old_str):
    """Avval aniq (tez) moslikni sinaydi, keyin whitespace-tolerant regexni."""
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

    print(f"=== Rejim: {MODE} (reklama o'chirish, v2 whitespace-tolerant) ===\n")

    results = []
    file_cache = {}
    matched_spans = {}  # fix_id -> (path, real_matched_text)

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

    print("\n✅ Barcha reklama tuzatishlari muvaffaqiyatli qo'llandi.")


if __name__ == "__main__":
    main()
