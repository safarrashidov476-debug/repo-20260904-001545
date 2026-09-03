#!/usr/bin/env python3
"""
Telegram Android uchun accessibility (TalkBack) tuzatishlari.
Rejimlar:
  check  - faqat tekshiradi, hech narsani o'zgartirmaydi
  apply  - barchasini tekshiradi; agar biri topilmasa, hech narsani
           o'zgartirmasdan to'xtaydi; hammasi topilsa, hammasini qo'llaydi
"""

import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "check"

FIXES = []

# ---------------------------------------------------------------------
# 1) DialogCell.java - ism va tur tartibini tuzatish
# ---------------------------------------------------------------------
FIXES.append({
    "id": 1,
    "label": "DialogCell.java: ism va tur tartibi",
    "path": "TMessagesProj/src/main/java/org/telegram/ui/Cells/DialogCell.java",
    "old": '''            } else if (user != null) {
                if (UserObject.isReplyUser(user)) {
                    sb.append(getString(R.string.RepliesTitle));
                } else if (UserObject.isAnonymous(user)) {
                    sb.append(getString(R.string.AnonymousForward));
                } else {
                    if (user.bot) {
                        sb.append(getString(R.string.Bot));
                        sb.append(". ");
                    }
                    if (user.self) {
                        sb.append(getString(R.string.SavedMessages));
                    } else {
                        sb.append(ContactsController.formatName(user.first_name, user.last_name));
                    }
                }
                sb.append(". ");
            } else if (chat != null) {
                if (chat.broadcast) {
                    sb.append(getString(R.string.AccDescrChannel));
                } else {
                    sb.append(getString(R.string.AccDescrGroup));
                }
                sb.append(". ");
                sb.append(chat.title);
                sb.append(". ");
            }''',
    "new": '''            } else if (user != null) {
                if (UserObject.isReplyUser(user)) {
                    sb.append(getString(R.string.RepliesTitle));
                    sb.append(". ");
                } else if (UserObject.isAnonymous(user)) {
                    sb.append(getString(R.string.AnonymousForward));
                    sb.append(". ");
                } else {
                    if (user.self) {
                        sb.append(getString(R.string.SavedMessages));
                    } else {
                        sb.append(ContactsController.formatName(user.first_name, user.last_name));
                    }
                    sb.append(". ");
                    if (user.bot) {
                        sb.append(getString(R.string.Bot));
                        sb.append(". ");
                    }
                }
            } else if (chat != null) {
                sb.append(chat.title);
                sb.append(". ");
                if (chat.broadcast) {
                    sb.append(getString(R.string.AccDescrChannel));
                } else {
                    sb.append(getString(R.string.AccDescrGroup));
                }
                sb.append(". ");
            }''',
})

# ---------------------------------------------------------------------
# 2) ChatMessageCell.java - ulashish tugmasini TalkBack'dan yashirish
# ---------------------------------------------------------------------
FIXES.append({
    "id": 2,
    "label": "ChatMessageCell.java: ulashish tugmasini yashirish",
    "path": "TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java",
    "old": '''if (drawSideButton == 1 || drawSideButton == 2) {
                    info.addChild(ChatMessageCell.this, SHARE);
                }''',
    "new": '''// Ulashish tugmasi TalkBack ro'yxatidan olib tashlandi''',
})

# ---------------------------------------------------------------------
# 3a) RadialProgress2.java - konstruktorga field qo'shish
# ---------------------------------------------------------------------
FIXES.append({
    "id": "3a",
    "label": "RadialProgress2.java: field qo'shish",
    "path": "TMessagesProj/src/main/java/org/telegram/ui/Components/RadialProgress2.java",
    "old": '''    public RadialProgress2(View parentView, Theme.ResourcesProvider resourcesProvider) {
        this.resourcesProvider = resourcesProvider;
        miniProgressBackgroundPaint = new Paint(Paint.ANTI_ALIAS_FLAG);

        parent = parentView;''',
    "new": '''    private int lastAnnouncedPercent = -1;

    public RadialProgress2(View parentView, Theme.ResourcesProvider resourcesProvider) {
        this.resourcesProvider = resourcesProvider;
        miniProgressBackgroundPaint = new Paint(Paint.ANTI_ALIAS_FLAG);

        parent = parentView;''',
})

# ---------------------------------------------------------------------
# 3b) RadialProgress2.java - setProgress metodini kengaytirish
#     Endi foiz HAR 1%DA e'lon qilinadi (avval 10% edi)
# ---------------------------------------------------------------------
FIXES.append({
    "id": "3b",
    "label": "RadialProgress2.java: foizni har 1%da ovozli aytish",
    "path": "TMessagesProj/src/main/java/org/telegram/ui/Components/RadialProgress2.java",
    "old": '''    public void setProgress(float value, boolean animated) {
        if (drawMiniIcon) {
            miniMediaActionDrawable.setProgress(value, animated);
        } else {
            mediaActionDrawable.setProgress(value, animated);
        }
    }''',
    "new": '''    public void setProgress(float value, boolean animated) {
        if (drawMiniIcon) {
            miniMediaActionDrawable.setProgress(value, animated);
        } else {
            mediaActionDrawable.setProgress(value, animated);
        }
        // Tiflogram: foizni alohida, xabarni bo'ladigan e'lon bilan aytmaymiz.
        // Buning o'rniga, xabar TalkBack fokusida bo'lsa, "kontent o'zgardi"
        // signalini yuboramiz - shunda TalkBack xabarning TO'LIQ tavsifini
        // (foiz + rasm/caption + qabul qilingan vaqt) birgalikda, bitta
        // yaxlit gap sifatida qayta o'qiydi (ChatMessageCell ichida yig'iladi).
        if (parent != null && parent.isAccessibilityFocused()) {
            int percent = Math.round(Math.max(0f, Math.min(1f, value)) * 100);
            // Har 1% da va 100% da kontent o'zgarishi — TalkBack tavsifni qayta o'qiydi
            // (foiz tavsif boshida ChatMessageCell da yig'iladi).
            if (percent != lastAnnouncedPercent && percent >= 0 && percent <= 100) {
                lastAnnouncedPercent = percent;
                parent.sendAccessibilityEvent(android.view.accessibility.AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED);
            }
        } else {
            // Fokus yo'qolganda reset — qayta fokusda 0 dan boshlasin
            lastAnnouncedPercent = -1;
        }
    }''',
})

# ---------------------------------------------------------------------
# 4a) ChatMessageCell.java - COMMENT elementini child ro'yxatidan olib tashlash
# ---------------------------------------------------------------------
FIXES.append({
    "id": "4a",
    "label": "ChatMessageCell.java: comment child olib tashlash",
    "path": "TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java",
    "old": '''                if (commentLayout != null) {
                    info.addChild(ChatMessageCell.this, COMMENT);
                }''',
    "new": '''                // "Fikr bildirish" endi alohida element emas, pastdagi acc_action_comment orqali beriladi''',
})

# ---------------------------------------------------------------------
# 4b) ChatMessageCell.java - asosiy amallar ro'yxatiga qo'shish
# ---------------------------------------------------------------------
FIXES.append({
    "id": "4b",
    "label": "ChatMessageCell.java: comment amalini qo'shish",
    "path": "TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java",
    "old": '''                info.addAction(new AccessibilityNodeInfo.AccessibilityAction(R.id.acc_action_msg_options, getString("AccActionMessageOptions", R.string.AccActionMessageOptions)));''',
    "new": '''                info.addAction(new AccessibilityNodeInfo.AccessibilityAction(R.id.acc_action_msg_options, getString("AccActionMessageOptions", R.string.AccActionMessageOptions)));
                if (commentLayout != null) {
                    int commentCount = getRepliesCount();
                    CharSequence commentLabel;
                    if (isRepliesChat) {
                        commentLabel = getString("ViewInChat", R.string.ViewInChat);
                    } else {
                        commentLabel = commentCount == 0 ? getString("LeaveAComment", R.string.LeaveAComment) : formatPluralString("CommentsCount", commentCount);
                    }
                    info.addAction(new AccessibilityNodeInfo.AccessibilityAction(R.id.acc_action_comment, commentLabel));
                }''',
})

# ---------------------------------------------------------------------
# 4c) ChatMessageCell.java - performAccessibilityAction ichida ushlash
# ---------------------------------------------------------------------
FIXES.append({
    "id": "4c",
    "label": "ChatMessageCell.java: comment amalini ushlash",
    "path": "TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java",
    "old": '''        } else if (action == R.id.acc_action_msg_options) {''',
    "new": '''        } else if (action == R.id.acc_action_comment) {
            if (delegate != null) {
                if (isRepliesChat) {
                    delegate.didPressSideButton(ChatMessageCell.this);
                } else {
                    delegate.didPressCommentButton(ChatMessageCell.this);
                }
            }
        } else if (action == R.id.acc_action_msg_options) {''',
})

# ---------------------------------------------------------------------
# 5) ids.xml - yangi ID e'lon qilish
# ---------------------------------------------------------------------
FIXES.append({
    "id": 5,
    "label": "ids.xml: acc_action_comment ID qo'shish",
    "path": "TMessagesProj/src/main/res/values/ids.xml",
    "old": '''<item name="acc_action_msg_options" type="id"/>''',
    "new": '''<item name="acc_action_msg_options" type="id"/>
    <item name="acc_action_comment" type="id"/>''',
})

# ---------------------------------------------------------------------
# 6) BuildVars.java - API_ID va API_HASH qiymatlarini o'rnatish
#    DIQQAT: quyidagi qiymatlar NAMUNA. Haqiqiy build uchun
#    my.telegram.org saytidan olingan o'z qiymatlaringizni qo'ying.
# ---------------------------------------------------------------------
FIXES.append({
    "id": 6,
    "label": "BuildVars.java: API_ID va API_HASH",
    "path": "TMessagesProj/src/main/java/org/telegram/messenger/BuildVars.java",
    "old": '''    public static int APP_ID = 4;
    public static String APP_HASH = "014b35b6184100b085b0d0572f9b5103";''',
    "new": '''    public static int APP_ID = 30286038;
    public static String APP_HASH = "20f4a1a1b116ce7dcb6b33c68044d6bf";''',
})


# ---------------------------------------------------------------------
# 7) ChatMessageCell.java - kanal postida komment soni (0 bo'lsa ham,
#    "0 fikr" deb) xabar tavsifi oxirida aytilsin
# ---------------------------------------------------------------------
FIXES.append({
    "id": 7,
    "label": "ChatMessageCell.java: komment sonini har doim aytish (0 dan boshlab)",
    "path": "TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java",
    "old": '''                    if (getRepliesCount() > 0 && !hasCommentLayout()) {
                        sb.append("\\n");
                        sb.append(formatPluralString("AccDescrNumberOfReplies", getRepliesCount()));
                    }''',
    "new": '''                    if (getRepliesCount() > 0 && !hasCommentLayout()) {
                        sb.append("\\n");
                        sb.append(formatPluralString("AccDescrNumberOfReplies", getRepliesCount()));
                    } else if (hasCommentLayout()) {
                        sb.append("\\n");
                        sb.append(formatPluralString("CommentsCount", getRepliesCount()));
                    }''',
})


# ---------------------------------------------------------------------
# 8) ChatActivity.java (subtitle) - "kimdir yozmoqda" holatini
#    TalkBack orqali ovozli e'lon qilish
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# 8) ChatAvatarContainer.java (subtitle) - "kimdir yozmoqda" holatini
#    TalkBack orqali ovozli e'lon qilish
# ---------------------------------------------------------------------
FIXES.append({
    "id": 8,
    "label": "ChatAvatarContainer.java: 'yozmoqda' holatini ovozli aytish",
    "path": "TMessagesProj/src/main/java/org/telegram/ui/Components/ChatAvatarContainer.java",
    "old": '''            useOnlineColor = true;
            setTypingAnimation(true);
        }
        lastSubtitleColorKey = useOnlineColor ? Theme.key_chat_status : Theme.key_actionBarDefaultSubtitle;''',
    "new": '''            useOnlineColor = true;
            setTypingAnimation(true);
            if (subtitleTextView != null && newSubtitle != null) {
                CharSequence currentShownSubtitle = subtitleTextView.getText();
                if (currentShownSubtitle == null || !newSubtitle.toString().equals(currentShownSubtitle.toString())) {
                    subtitleTextView.announceForAccessibility(newSubtitle);
                }
            }
        }
        lastSubtitleColorKey = useOnlineColor ? Theme.key_chat_status : Theme.key_actionBarDefaultSubtitle;''',
})

# ---------------------------------------------------------------------
# 9) ChatMessageCell.java - "with admin tag: Admin" / "with member tag"
#    TalkBack matnidan olib tashlash (guruhlarda admin xabarlari)
# ---------------------------------------------------------------------
FIXES.append({
    "id": 9,
    "label": "ChatMessageCell.java: admin tag TalkBack matnini olib tashlash",
    "path": "TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java",
    "old": '''                        final CharSequence adminText = getAdminAccessibilityText();
                        if (!TextUtils.isEmpty(adminText)) {
                            if (adminLayoutIsTag) {
                                sb.append(' ').append(formatString(adminLayoutIsAdmin ? R.string.AccDescrWithAdminTag : R.string.AccDescrWithMemberTag, adminText));
                            } else {
                                sb.append(", ").append(adminText);
                            }
                        }''',
    "new": '''                        // Admin/member tag TalkBack da aytilmaydi (so'ralganidek)''',
})


# ---------------------------------------------------------------------
# 10) ChatActivityEnterView.java - matn uzunlik cheklovidan oshganda
#     text fayl sifatida yuborish + fayl nomi kiritish oynasi
# ---------------------------------------------------------------------
FIXES.append({
    "id": 10,
    "label": "ChatActivityEnterView.java: uzun matnni text fayl qilib yuborish",
    "path": "TMessagesProj/src/main/java/org/telegram/ui/Components/ChatActivityEnterView.java",
    "old": '''        int maxLength = accountInstance.getMessagesController().getMaxMessageLength();
        if (text.length() != 0) {
            if (delegate != null && parentFragment != null && (scheduleDate != 0) == parentFragment.isInScheduleMode()) {
                delegate.prepareMessageSending();
            }
            int end;
            int start = 0;
            do {
                int whitespaceIndex = -1;''',
    "new": '''        int maxLength = accountInstance.getMessagesController().getMaxMessageLength();
        // Tiflogram: matn cheklovidan oshsa - text fayl sifatida yuborish
        if (text.length() > maxLength && parentActivity != null) {
            final CharSequence fullText = text;
            final boolean notifyFinal = notify;
            final int scheduleDateFinal = scheduleDate;
            final int scheduleRepeatPeriodFinal = scheduleRepeatPeriod;
            final long payStarsFinal = payStars;
            final EditTextBoldCursor nameEdit = new EditTextBoldCursor(parentActivity);
            nameEdit.setTextSize(TypedValue.COMPLEX_UNIT_DIP, 16);
            nameEdit.setTextColor(getThemedColor(Theme.key_dialogTextBlack));
            nameEdit.setHintTextColor(getThemedColor(Theme.key_groupcreate_hintText));
            nameEdit.setHint("message.txt");
            nameEdit.setText("message.txt");
            nameEdit.setSingleLine(true);
            nameEdit.setImeOptions(EditorInfo.IME_ACTION_DONE);
            nameEdit.setPadding(AndroidUtilities.dp(16), AndroidUtilities.dp(12), AndroidUtilities.dp(16), AndroidUtilities.dp(12));
            nameEdit.setContentDescription("Text fayl nomi");
            nameEdit.setBackground(Theme.createEditTextDrawable(parentActivity, true));
            final FrameLayout container = new FrameLayout(parentActivity);
            container.setPadding(AndroidUtilities.dp(8), AndroidUtilities.dp(4), AndroidUtilities.dp(8), 0);
            container.addView(nameEdit, LayoutHelper.createFrame(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT));
            AlertDialog.Builder builder = new AlertDialog.Builder(parentActivity, resourcesProvider);
            builder.setTitle(getString(R.string.SendAsFile));
            builder.setMessage("Matn juda uzun. Text fayl sifatida yuborilsinmi? Fayl nomini kiriting:");
            builder.setView(container);
            builder.setPositiveButton(getString(R.string.Send), (dialog, which) -> {
                String fileName = nameEdit.getText() != null ? nameEdit.getText().toString().trim() : "";
                if (fileName.isEmpty()) {
                    fileName = "message.txt";
                }
                if (!fileName.toLowerCase().endsWith(".txt")) {
                    fileName = fileName + ".txt";
                }
                try {
                    File dir = parentActivity.getCacheDir();
                    File outFile = new File(dir, fileName);
                    FileOutputStream fos = new FileOutputStream(outFile);
                    fos.write(fullText.toString().getBytes("UTF-8"));
                    fos.close();
                    if (messageEditText != null) {
                        messageEditText.setText("");
                    }
                    SendMessagesHelper.prepareSendingDocument(
                            accountInstance,
                            outFile.getAbsolutePath(),
                            outFile.getAbsolutePath(),
                            null,
                            null,
                            "text/plain",
                            dialog_id,
                            replyingMessageObject,
                            getThreadMessage(),
                            null,
                            replyingQuote,
                            null,
                            notifyFinal,
                            scheduleDateFinal,
                            null,
                            parentFragment != null ? parentFragment.getMessageChatSendParams() : null,
                            false
                    );
                    if (delegate != null) {
                        delegate.onMessageSend(null, notifyFinal, scheduleDateFinal, scheduleRepeatPeriodFinal, payStarsFinal);
                    }
                } catch (Exception e) {
                    FileLog.e(e);
                }
            });
            builder.setNegativeButton(getString(R.string.Cancel), null);
            AlertDialog dialog = builder.create();
            dialog.setOnShowListener(d -> {
                nameEdit.requestFocus();
                AndroidUtilities.showKeyboard(nameEdit);
            });
            if (parentFragment != null) {
                parentFragment.showDialog(dialog);
            } else {
                dialog.show();
            }
            return true;
        }
        if (text.length() != 0) {
            if (delegate != null && parentFragment != null && (scheduleDate != 0) == parentFragment.isInScheduleMode()) {
                delegate.prepareMessageSending();
            }
            int end;
            int start = 0;
            do {
                int whitespaceIndex = -1;''',
})


# ---------------------------------------------------------------------
# 5) ChatMessageCell.java - yuklash foizini xabar tavsifiga qo'shish
#    (bayt hajmi o'rniga "X foiz" - butun tavsif bilan birga o'qiladi,
#    ENG BOSHIDA aytiladi)
# ---------------------------------------------------------------------
FIXES.append({
    "id": 5,
    "label": "ChatMessageCell.java: eski o'rtadagi yuklash matnini o'chirish",
    "path": "TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java",
    "old": '''                    if (documentAttach != null && (documentAttachType == DOCUMENT_ATTACH_TYPE_DOCUMENT || documentAttachType == DOCUMENT_ATTACH_TYPE_GIF || documentAttachType == DOCUMENT_ATTACH_TYPE_VIDEO)) {
                        if (buttonState == 1 && loadingProgressLayout != null) {
                            sb.append("\\n");
                            final boolean sending = currentMessageObject.isSending();
                            final String key = sending ? "AccDescrUploadProgress" : "AccDescrDownloadProgress";
                            final int resId = sending ? R.string.AccDescrUploadProgress : R.string.AccDescrDownloadProgress;
                            sb.append(formatString(key, resId, AndroidUtilities.formatFileSize(currentMessageObject.loadedFileSize), AndroidUtilities.formatFileSize(lastLoadingSizeTotal)));
                        }
                    }''',
    # Tiflogram: bu joydan butunlay olib tashlandi - foiz endi
    # tavsifning ENG BOSHIDA (5b) aytiladi, shu yerda takrorlanmasin
    "new": '''''',
})

# ---------------------------------------------------------------------
# 5b) ChatMessageCell.java - yuklash foizini tavsifning ENG BOSHIGA qo'shish
# ---------------------------------------------------------------------
FIXES.append({
    "id": "5b",
    "label": "ChatMessageCell.java: yuklash foizi - tavsif boshida",
    "path": "TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java",
    "old": '''                    SpannableStringBuilder sb = new SpannableStringBuilder();''',
    "new": '''                    SpannableStringBuilder sb = new SpannableStringBuilder();
                    // Tiflogram: yuklash/yuborish foizi ENG BOSHIDA aytiladi.
                    // Barcha media: document/video/gif/audio/music/round/photo.
                    boolean tiflogramDownloading = (buttonState == 1) || (hasMiniProgress == 1 && miniButtonState == 1);
                    if (tiflogramDownloading && currentMessageObject != null && !currentMessageObject.isSending()) {
                        int tiflogramPercent = 0;
                        long total = lastLoadingSizeTotal;
                        long loaded = currentMessageObject.loadedFileSize;
                        if (total <= 0 && currentMessageObject.getDocument() != null) {
                            total = currentMessageObject.getDocument().size;
                        }
                        if (total > 0) {
                            tiflogramPercent = Math.round(Math.max(0f, Math.min(1f, (float) loaded / (float) total)) * 100);
                        }
                        if (tiflogramPercent == 0 && radialProgress != null) {
                            float rp = radialProgress.getProgress();
                            if (rp > 0f && rp < 1f) {
                                tiflogramPercent = Math.round(rp * 100);
                            }
                        }
                        if (tiflogramPercent > 0 && tiflogramPercent < 100) {
                            sb.append(String.valueOf(tiflogramPercent)).append(" foiz");
                            sb.append("\\n");
                        } else if (tiflogramPercent >= 100) {
                            sb.append("Yuklash tugadi");
                            sb.append("\\n");
                        } else {
                            sb.append("Yuklanmoqda");
                            sb.append("\\n");
                        }
                    } else if (tiflogramDownloading && currentMessageObject != null && currentMessageObject.isSending()) {
                        int tiflogramPercent = 0;
                        long total = lastLoadingSizeTotal;
                        long loaded = currentMessageObject.loadedFileSize;
                        if (total > 0) {
                            tiflogramPercent = Math.round(Math.max(0f, Math.min(1f, (float) loaded / (float) total)) * 100);
                        }
                        if (tiflogramPercent > 0 && tiflogramPercent < 100) {
                            sb.append(String.valueOf(tiflogramPercent)).append(" foiz yuborilmoqda");
                            sb.append("\\n");
                        }
                    }''',
})

# ---------------------------------------------------------------------
# 6a) ChatMessageCell.java - men yuborgan xabarda o'qilgan/o'qilmagan
#     holatini XABAR MATNIDAN OLDIN aytish
# ---------------------------------------------------------------------
FIXES.append({
    "id": "6a",
    "label": "ChatMessageCell.java: o'qilgan/o'qilmagan - matndan oldin",
    "path": "TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java",
    "old": '''                    if (drawForwardedName) {
                        for (int a = 0; a < 2; a++) {
                            if (forwardedNameLayout[a] != null && forwardedNameLayout[a].getText() != null) {
                                sb.append(forwardedNameLayout[a].getText());
                                sb.append(a == 0 ? " " : "\\n");
                            }
                        }
                    }
                    if (documentAttach != null && documentAttachType == DOCUMENT_ATTACH_TYPE_DOCUMENT) {''',
    "new": '''                    if (drawForwardedName) {
                        for (int a = 0; a < 2; a++) {
                            if (forwardedNameLayout[a] != null && forwardedNameLayout[a].getText() != null) {
                                sb.append(forwardedNameLayout[a].getText());
                                sb.append(a == 0 ? " " : "\\n");
                            }
                        }
                    }
                    // Tiflogram: men yuborgan xabarda avval o'qilgan/o'qilmagan
                    // holati, keyin xabarning o'zi aytiladi
                    if (currentMessageObject.isOut() && currentMessageObject.isSent() && !currentMessageObject.scheduled) {
                        sb.append(currentMessageObject.isUnread() ? getString("AccDescrMsgUnread", R.string.AccDescrMsgUnread) : getString("AccDescrMsgRead", R.string.AccDescrMsgRead));
                        sb.append("\\n");
                    }
                    if (documentAttach != null && documentAttachType == DOCUMENT_ATTACH_TYPE_DOCUMENT) {''',
})

# ---------------------------------------------------------------------
# 6b) ChatMessageCell.java - oldingi (oxiridagi) o'qilgan/o'qilmagan
#     qatorini olib tashlash (endi 6a orqali boshida aytiladi)
# ---------------------------------------------------------------------
FIXES.append({
    "id": "6b",
    "label": "ChatMessageCell.java: eski o'qilgan/o'qilmagan qatorini olib tashlash",
    "path": "TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java",
    "old": '''                            } else {
                                sb.append(formatString("AccDescrSentDate", R.string.AccDescrSentDate, getString("TodayAt", R.string.TodayAt) + " " + currentTimeString));
                                sb.append(", ");
                                sb.append(currentMessageObject.isUnread() ? getString("AccDescrMsgUnread", R.string.AccDescrMsgUnread) : getString("AccDescrMsgRead", R.string.AccDescrMsgRead));
                            }''',
    "new": '''                            } else {
                                sb.append(formatString("AccDescrSentDate", R.string.AccDescrSentDate, getString("TodayAt", R.string.TodayAt) + " " + currentTimeString));
                            }''',
})


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def main():
    if MODE not in ("check", "apply"):
        print(f"Noma'lum rejim: {MODE}. 'check' yoki 'apply' bo'lishi kerak.")
        sys.exit(1)

    print(f"=== Rejim: {MODE} ===\n")

    results = []
    file_cache = {}

    for fix in FIXES:
        path = fix["path"]
        if path not in file_cache:
            file_cache[path] = read_file(path)
        content = file_cache[path]

        if content is None:
            print(f"❌ [{fix['id']}] {fix['label']} — fayl topilmadi: {path}")
            results.append((fix, False, "fayl topilmadi"))
            continue

        if fix["old"] not in content:
            print(f"❌ [{fix['id']}] {fix['label']} — eski matn topilmadi")
            results.append((fix, False, "eski matn topilmadi"))
            continue

        print(f"✅ [{fix['id']}] {fix['label']} — topildi")
        results.append((fix, True, None))

    failed = [r for r in results if not r[1]]

    print("\n=== Xulosa ===")
    print(f"Jami: {len(results)}, muvaffaqiyatli: {len(results) - len(failed)}, xato: {len(failed)}")

    if failed:
        print("\nXato bo'lgan tuzatishlar:")
        for fix, ok, reason in failed:
            print(f"  - [{fix['id']}] {fix['label']}: {reason}")

    if MODE == "check":
        if failed:
            sys.exit(1)
        else:
            print("\nBarcha tuzatishlar tayyor. 'apply' rejimida ishga tushirishingiz mumkin.")
            sys.exit(0)

    # MODE == "apply"
    if failed:
        print("\n⛔ Ba'zi tuzatishlar topilmadi. Hech narsa o'zgartirilmadi (all-or-nothing).")
        sys.exit(1)

    # Barchasi topildi - endi haqiqatan qo'llaymiz
    print("\n=== Qo'llanmoqda ===")
    modified_content = dict(file_cache)  # nusxa

    for fix in FIXES:
        path = fix["path"]
        modified_content[path] = modified_content[path].replace(fix["old"], fix["new"], 1)

    for path, content in modified_content.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Yozildi: {path}")

    print("\n✅ Barcha tuzatishlar muvaffaqiyatli qo'llandi.")


if __name__ == "__main__":
    main()
