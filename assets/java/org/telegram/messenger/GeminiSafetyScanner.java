/*
 * Tiflogram: Gemini API orqali shubhali kanal/guruh/botlarni tekshirish.
 * Model: gemini-3.5-flash-lite (yengil, barqaror, klassifikatsiya uchun)
 */
package org.telegram.messenger;

import android.content.SharedPreferences;
import android.text.TextUtils;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;
import org.telegram.tgnet.TLRPC;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.concurrent.atomic.AtomicBoolean;

public class GeminiSafetyScanner {

    private static final String TAG = "TiflogramGemini";
    // Eng yengil barqaror model (klassifikatsiya / triage uchun)
    public static final String MODEL = "gemini-3.5-flash-lite";
    // Zaxira model - agar asosiy model o'chirilsa/404 qaytarsa shunga o'tiladi
    // (Google xatolik xabarida tavsiya qilgan model)
    public static final String FALLBACK_MODEL = "gemini-3.6-flash";
    private static final String API_URL =
            "https://generativelanguage.googleapis.com/v1beta/models/" + MODEL + ":generateContent?key=";
    private static final String API_URL_FALLBACK =
            "https://generativelanguage.googleapis.com/v1beta/models/" + FALLBACK_MODEL + ":generateContent?key=";

    public static final String PREFS = "tiflogram_gemini";
    public static final String KEY_API = "gemini_api_key";
    public static final String KEY_AUTO_DELETE = "gemini_auto_delete";

    private static final AtomicBoolean running = new AtomicBoolean(false);

    public static SharedPreferences prefs() {
        return ApplicationLoader.applicationContext.getSharedPreferences(PREFS, android.content.Context.MODE_PRIVATE);
    }

    public static String getApiKey() {
        return prefs().getString(KEY_API, "");
    }

    public static void setApiKey(String key) {
        prefs().edit().putString(KEY_API, key != null ? key.trim() : "").apply();
    }

    public static boolean isEnabled() {
        return !TextUtils.isEmpty(getApiKey());
    }

    public static boolean isAutoDelete() {
        return prefs().getBoolean(KEY_AUTO_DELETE, true);
    }

    public static void setAutoDelete(boolean v) {
        prefs().edit().putBoolean(KEY_AUTO_DELETE, v).apply();
    }

    public interface ResultListener {
        void onResult(String text);
    }

    // Tiflogram: endi Sozlamalar -> Maxfiylikda alohida bo'lim yo'q.
    // Skanerlash faqat "3 nuqta -> Gemini" oynasida, savol orqali
    // (masalan "kanallarni tekshir") ishga tushadi - pastga qarang.

    public static void runScan(final int account) {
        runScanInternal(account, isAutoDelete(), null);
    }

    public static void runScan(final int account, final boolean autoDelete, final ResultListener listener) {
        runScanInternal(account, autoDelete, listener);
    }

    private static void runScanInternal(final int account, final boolean autoDelete, final ResultListener listener) {
        if (!isEnabled()) {
            deliver(listener, "⚠️ API kalit kiritilmagan.\nGemini oynasida \"Kalit\" tugmasidan kiriting.");
            return;
        }
        if (!running.compareAndSet(false, true)) {
            deliver(listener, "⏳ Tekshiruv allaqachon davom etmoqda…");
            return;
        }
        Utilities.globalQueue.postRunnable(() -> {
            try {
                String report = doScan(account, autoDelete);
                deliver(listener, report);
            } catch (Exception e) {
                FileLog.e(TAG + " scan error", e);
                deliver(listener, "❌ Xato: " + (e.getMessage() != null ? e.getMessage() : e.toString()));
            } finally {
                running.set(false);
            }
        });
    }

    private static void deliver(ResultListener listener, String text) {
        if (listener == null) return;
        AndroidUtilities.runOnUIThread(() -> listener.onResult(text != null ? text : ""));
    }

    private static String doScan(int account, boolean autoDelete) throws Exception {
        MessagesController mc = MessagesController.getInstance(account);
        ArrayList<TLRPC.Dialog> dialogs = new ArrayList<>(mc.getAllDialogs());
        ArrayList<Item> candidates = new ArrayList<>();

        for (int i = 0; i < dialogs.size(); i++) {
            TLRPC.Dialog d = dialogs.get(i);
            long did = d.id;
            if (DialogObject.isEncryptedDialog(did)) continue;

            if (DialogObject.isChatDialog(did)) {
                TLRPC.Chat chat = mc.getChat(-did);
                if (chat == null) continue;
                boolean isChannel = ChatObject.isChannel(chat) && !ChatObject.isMegagroup(chat);
                boolean isGroup = ChatObject.isMegagroup(chat) || (!ChatObject.isChannel(chat));
                if (!isChannel && !isGroup) continue;
                String title = chat.title != null ? chat.title : "";
                String uname = chat.username != null ? chat.username : "";
                candidates.add(new Item(did, isChannel ? "channel" : "group", title, uname, ""));
            } else if (DialogObject.isUserDialog(did)) {
                TLRPC.User user = mc.getUser(did);
                if (user == null || !user.bot) continue;
                String name = UserObject.getUserName(user);
                String uname = user.username != null ? user.username : "";
                candidates.add(new Item(did, "bot", name != null ? name : "", uname, ""));
            }
        }

        if (candidates.isEmpty()) {
            return "✅ Kanal/guruh/bot topilmadi.";
        }

        HashMap<Long, Item> byId = new HashMap<>();
        for (int i = 0; i < candidates.size(); i++) {
            byId.put(candidates.get(i).dialogId, candidates.get(i));
        }

        ArrayList<Item> allSuspicious = new ArrayList<>();

        // Batch by 15 to keep prompts small
        for (int start = 0; start < candidates.size(); start += 15) {
            int end = Math.min(start + 15, candidates.size());
            ArrayList<Item> batch = new ArrayList<>(candidates.subList(start, end));
            ArrayList<Long> suspicious = classifyBatch(batch);
            if (suspicious == null || suspicious.isEmpty()) continue;
            for (int j = 0; j < suspicious.size(); j++) {
                Item it = byId.get(suspicious.get(j));
                if (it != null) allSuspicious.add(it);
            }
        }

        int deleted = 0;
        if (autoDelete && !allSuspicious.isEmpty()) {
            for (int j = 0; j < allSuspicious.size(); j++) {
                long dialogId = allSuspicious.get(j).dialogId;
                try {
                    deleteDialog(account, dialogId);
                    deleted++;
                    FileLog.d(TAG + " deleted suspicious dialog " + dialogId);
                } catch (Exception e) {
                    FileLog.e(TAG + " delete failed " + dialogId, e);
                }
            }
        }

        StringBuilder report = new StringBuilder();
        report.append("🛡️ Tekshiruv natijasi\n\n");
        report.append("Tekshirildi: ").append(candidates.size()).append(" ta (kanal/guruh/bot)\n");
        report.append("Shubhali: ").append(allSuspicious.size()).append(" ta\n");
        if (autoDelete) {
            report.append("O'chirildi: ").append(deleted).append(" ta\n");
        }
        report.append("\n");
        if (allSuspicious.isEmpty()) {
            report.append("✅ Shubhali kanal/guruh/bot topilmadi.");
        } else {
            report.append("Shubhali ro'yxat:\n");
            for (int i = 0; i < allSuspicious.size(); i++) {
                Item it = allSuspicious.get(i);
                report.append(i + 1).append(") ");
                if ("channel".equals(it.type)) report.append("📢 ");
                else if ("group".equals(it.type)) report.append("👥 ");
                else report.append("🤖 ");
                report.append(it.title);
                if (!TextUtils.isEmpty(it.username)) {
                    report.append(" (@").append(it.username).append(")");
                }
                report.append("\n");
            }
            if (!autoDelete) {
                report.append("\nO'chirish uchun \"kanallarni tekshir va o'chir\" deb so'rang.");
            }
        }
        return report.toString();
    }

    private static void deleteDialog(int account, long dialogId) {
        // Dialogni o'chirish / chiqish (MessagesController orqali)
        MessagesController.getInstance(account).deleteDialog(dialogId, 1, false);
    }

    private static ArrayList<Long> classifyBatch(ArrayList<Item> batch) throws Exception {
        String apiKey = getApiKey();
        if (TextUtils.isEmpty(apiKey)) return null;

        StringBuilder list = new StringBuilder();
        for (int i = 0; i < batch.size(); i++) {
            Item it = batch.get(i);
            list.append(i + 1).append(") type=").append(it.type)
                    .append("; title=").append(sanitize(it.title))
                    .append("; username=@").append(sanitize(it.username))
                    .append("; about=").append(sanitize(it.about))
                    .append("\n");
        }

        String prompt = "You are a safety classifier for Telegram chats. "
                + "Mark an item SUSPICIOUS only if it clearly looks like: scam, phishing, malware, fraud, "
                + "fake support, investment scam, adult spam bots, or obvious malware distribution. "
                + "Do NOT mark normal news, communities, or legitimate bots. "
                + "Reply with ONLY a JSON array of 1-based indexes that are suspicious, e.g. [2,5] or [].\n\n"
                + list;

        JSONObject body = new JSONObject();
        JSONArray contents = new JSONArray();
        JSONObject content = new JSONObject();
        JSONArray parts = new JSONArray();
        JSONObject part = new JSONObject();
        part.put("text", prompt);
        parts.put(part);
        content.put("parts", parts);
        contents.put(content);
        body.put("contents", contents);

        JSONObject genConfig = new JSONObject();
        genConfig.put("temperature", 0.1);
        genConfig.put("maxOutputTokens", 256);
        body.put("generationConfig", genConfig);

        String responseText = httpPost(API_URL + apiKey, body.toString());
        if (responseText == null) {
            // Asosiy model ishlamadi (masalan 404 - o'chirilgan) - zaxira modelni sinaymiz
            FileLog.d(TAG + " " + MODEL + " ishlamadi, " + FALLBACK_MODEL + " sinalmoqda");
            responseText = httpPost(API_URL_FALLBACK + apiKey, body.toString());
        }
        if (responseText == null) return null;

        JSONObject resp = new JSONObject(responseText);
        JSONArray candidatesArr = resp.optJSONArray("candidates");
        if (candidatesArr == null || candidatesArr.length() == 0) return null;
        JSONObject c0 = candidatesArr.getJSONObject(0);
        JSONObject contentOut = c0.optJSONObject("content");
        if (contentOut == null) return null;
        JSONArray partsOut = contentOut.optJSONArray("parts");
        if (partsOut == null || partsOut.length() == 0) return null;
        String text = partsOut.getJSONObject(0).optString("text", "");

        ArrayList<Long> result = new ArrayList<>();
        // Extract JSON array from response
        int a = text.indexOf('[');
        int b = text.lastIndexOf(']');
        if (a < 0 || b <= a) return result;
        JSONArray idxs = new JSONArray(text.substring(a, b + 1));
        for (int i = 0; i < idxs.length(); i++) {
            int oneBased = idxs.optInt(i, -1);
            if (oneBased >= 1 && oneBased <= batch.size()) {
                result.add(batch.get(oneBased - 1).dialogId);
            }
        }
        return result;
    }

    private static String httpPost(String urlStr, String json) {
        HttpURLConnection conn = null;
        try {
            URL url = new URL(urlStr);
            conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json; charset=utf-8");
            conn.setDoOutput(true);
            conn.setConnectTimeout(20000);
            conn.setReadTimeout(45000);
            byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
            conn.setFixedLengthStreamingMode(bytes.length);
            OutputStream os = conn.getOutputStream();
            os.write(bytes);
            os.close();
            int code = conn.getResponseCode();
            BufferedReader reader = new BufferedReader(new InputStreamReader(
                    code >= 200 && code < 300 ? conn.getInputStream() : conn.getErrorStream(),
                    StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) sb.append(line);
            reader.close();
            if (code < 200 || code >= 300) {
                FileLog.e(TAG + " HTTP " + code + " " + sb);
                return null;
            }
            return sb.toString();
        } catch (Exception e) {
            FileLog.e(TAG + " http error", e);
            return null;
        } finally {
            if (conn != null) conn.disconnect();
        }
    }

    private static String sanitize(String s) {
        if (s == null) return "";
        s = s.replace('\n', ' ').replace('\r', ' ');
        if (s.length() > 120) s = s.substring(0, 120);
        return s;
    }

    private static class Item {
        final long dialogId;
        final String type;
        final String title;
        final String username;
        final String about;

        Item(long dialogId, String type, String title, String username, String about) {
            this.dialogId = dialogId;
            this.type = type;
            this.title = title;
            this.username = username;
            this.about = about;
        }
    }

    // =====================================================================
    // Tiflogram: "3 nuqta -> Gemini" suhbat oynasi (faqat savol-javob).
    // MUHIM: bu yerda AI javobidan kelib chiqib biror amalni avtomatik
    // bajarish (masalan xabar yuborish, guruh ochish) YO'Q - bu xavfli
    // bo'lgani uchun ataylab olib tashlangan. Gemini faqat javob beradi.
    // =====================================================================

    // =====================================================================
    // Tiflogram: xavfsiz "niyat" aniqlash - savol matnidagi KALIT SO'ZLARNI
    // BIZNING KOD tekshiradi (Gemini emas). Shuning uchun bu "buyruq
    // bajarish" emas - AI javobi hech qachon qaysi kod ishlashini
    // belgilamaydi, faqat foydalanuvchi savolining o'zi tekshiriladi.
    // Moslik topilmasa (null qaytsa) - oddiy savol sifatida Gemini'ga
    // yuboriladi.
    // =====================================================================
    private static String tryLocalIntent(final int account, String q, final ResultListener listener) {
        String ql = q.toLowerCase(java.util.Locale.ROOT);
        boolean mentionsManage = ql.contains("kanal") || ql.contains("guruh") || ql.contains("bot");
        boolean wantsCheck = ql.contains("tekshir") || ql.contains("skaner") || ql.contains("shubhali");
        if (mentionsManage && wantsCheck) {
            boolean wantsDelete = ql.contains("o'chir") || ql.contains("ochir") || ql.contains("olib tashla");
            runScan(account, wantsDelete, listener);
            return "🔎 Tekshirilmoqda…";
        }
        return null;
    }

    /** Gemini'dan oddiy savol-javob (buyruq bajarish yo'q, faqat matn javob). */
    public static String ask(String userText) throws Exception {
        String apiKey = getApiKey();
        if (TextUtils.isEmpty(apiKey)) {
            return "API kalit kiritilmagan. Pastdagi \"Kalit\" tugmasidan kiriting.";
        }
        String prompt = "Sen Tiflogram ilovasidagi yordamchisan. O'zbek tilida qisqa va aniq javob ber.\n\nSavol: " + userText;

        JSONObject body = new JSONObject();
        JSONArray contents = new JSONArray();
        JSONObject content = new JSONObject();
        JSONArray parts = new JSONArray();
        JSONObject part = new JSONObject();
        part.put("text", prompt);
        parts.put(part);
        content.put("parts", parts);
        contents.put(content);
        body.put("contents", contents);
        JSONObject genConfig = new JSONObject();
        genConfig.put("temperature", 0.4);
        genConfig.put("maxOutputTokens", 1024);
        body.put("generationConfig", genConfig);

        String responseText = httpPost(API_URL + apiKey, body.toString());
        if (responseText == null) {
            // Asosiy model ishlamadi - zaxira modelni sinaymiz
            responseText = httpPost(API_URL_FALLBACK + apiKey, body.toString());
        }
        if (responseText == null) return "Gemini javob bermadi (tarmoq yoki model xatosi).";

        JSONObject resp = new JSONObject(responseText);
        JSONArray candidatesArr = resp.optJSONArray("candidates");
        if (candidatesArr == null || candidatesArr.length() == 0) return "Bo'sh javob.";
        JSONObject contentOut = candidatesArr.getJSONObject(0).optJSONObject("content");
        if (contentOut == null) return "Bo'sh javob.";
        JSONArray partsOut = contentOut.optJSONArray("parts");
        if (partsOut == null || partsOut.length() == 0) return "Bo'sh javob.";
        String text = partsOut.getJSONObject(0).optString("text", "");
        return TextUtils.isEmpty(text) ? "Bo'sh javob." : text;
    }

    /** "3 nuqta -> Gemini" oynasini ochadi. Yengil interfeys: scroll, yuklanish holati, yuborilgach maydon tozalanadi. */
    public static void openAssistant(final org.telegram.ui.ActionBar.BaseFragment fragment, final int account) {
        if (fragment == null || fragment.getParentActivity() == null) return;
        final android.app.Activity act = fragment.getParentActivity();

        android.widget.LinearLayout box = new android.widget.LinearLayout(act);
        box.setOrientation(android.widget.LinearLayout.VERTICAL);
        int pad = AndroidUtilities.dp(16);
        box.setPadding(pad, AndroidUtilities.dp(8), pad, 0);

        // Natija - scroll ichida, balandligi cheklangan (interfeys "og'ir" bo'lib qolmasligi uchun)
        final android.widget.TextView out = new android.widget.TextView(act);
        out.setTextSize(android.util.TypedValue.COMPLEX_UNIT_DIP, 15);
        out.setLineSpacing(AndroidUtilities.dp(2), 1f);
        out.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(org.telegram.ui.ActionBar.Theme.key_dialogTextBlack));
        out.setText("Savolingizni yozing. Masalan: \"kanal va guruhlarni tekshir\".");

        android.widget.ScrollView scroll = new android.widget.ScrollView(act);
        scroll.addView(out, new android.widget.ScrollView.LayoutParams(
                android.widget.ScrollView.LayoutParams.MATCH_PARENT,
                android.widget.ScrollView.LayoutParams.WRAP_CONTENT));
        scroll.setLayoutParams(new android.widget.LinearLayout.LayoutParams(
                android.widget.LinearLayout.LayoutParams.MATCH_PARENT, AndroidUtilities.dp(180)));
        box.addView(scroll);

        // Yuklanmoqda - aylanma belgi (natija o'rniga vaqtincha ko'rinadi)
        final android.widget.ProgressBar spinner = new android.widget.ProgressBar(act);
        spinner.setVisibility(android.view.View.GONE);
        box.addView(spinner, org.telegram.ui.Components.LayoutHelper.createLinear(28, 28, android.view.Gravity.CENTER, 0, 8, 0, 8));

        final org.telegram.ui.Components.EditTextBoldCursor edit = new org.telegram.ui.Components.EditTextBoldCursor(act);
        edit.setTextSize(android.util.TypedValue.COMPLEX_UNIT_DIP, 16);
        edit.setHint("Savol yozing…");
        edit.setMinLines(1);
        edit.setMaxLines(4);
        edit.setPadding(AndroidUtilities.dp(8), AndroidUtilities.dp(8), AndroidUtilities.dp(8), AndroidUtilities.dp(8));
        android.widget.LinearLayout.LayoutParams editParams = new android.widget.LinearLayout.LayoutParams(
                android.widget.LinearLayout.LayoutParams.MATCH_PARENT,
                android.widget.LinearLayout.LayoutParams.WRAP_CONTENT);
        editParams.setMargins(0, AndroidUtilities.dp(8), 0, 0);
        box.addView(edit, editParams);

        org.telegram.ui.ActionBar.AlertDialog.Builder b = new org.telegram.ui.ActionBar.AlertDialog.Builder(act);
        b.setTitle("Gemini");
        b.setView(box);
        b.setPositiveButton("So'rash", null); // listener pastda - avtomatik yopilib ketmasligi uchun
        b.setNeutralButton("Kalit", null);
        b.setNegativeButton(org.telegram.messenger.LocaleController.getString("Close", R.string.Close), null);
        final org.telegram.ui.ActionBar.AlertDialog dlg = b.create();

        dlg.setOnShowListener(d -> {
            final android.widget.Button askBtn = (android.widget.Button) dlg.getButton(android.content.DialogInterface.BUTTON_POSITIVE);
            final android.widget.Button keyBtn = (android.widget.Button) dlg.getButton(android.content.DialogInterface.BUTTON_NEUTRAL);

            if (askBtn != null) askBtn.setOnClickListener(v -> {
                final String q = edit.getText() != null ? edit.getText().toString().trim() : "";
                if (q.isEmpty()) return;

                // Tiflogram: yuborilgan matn darhol maydondan tozalanadi
                edit.setText("");

                askBtn.setEnabled(false);
                spinner.setVisibility(android.view.View.VISIBLE);
                out.setText("");

                // Avval xavfsiz mahalliy niyatni tekshiramiz (masalan
                // "kanallarni tekshir") - AI emas, bizning kod qaror qiladi
                String immediate = tryLocalIntent(account, q, result -> {
                    spinner.setVisibility(android.view.View.GONE);
                    askBtn.setEnabled(true);
                    out.setText(result);
                });
                if (immediate != null) {
                    out.setText(immediate);
                    return; // natija yuqoridagi listener orqali keladi
                }

                Utilities.globalQueue.postRunnable(() -> {
                    String answer;
                    try {
                        answer = ask(q);
                    } catch (Exception e) {
                        answer = "Xato: " + e.getMessage();
                    }
                    final String result = answer;
                    AndroidUtilities.runOnUIThread(() -> {
                        spinner.setVisibility(android.view.View.GONE);
                        askBtn.setEnabled(true);
                        out.setText(result);
                    });
                });
            });

            if (keyBtn != null) keyBtn.setOnClickListener(v -> {
                final org.telegram.ui.Components.EditTextBoldCursor keyEdit = new org.telegram.ui.Components.EditTextBoldCursor(act);
                keyEdit.setHint("AIza…");
                keyEdit.setText(getApiKey());
                keyEdit.setSingleLine(true);
                keyEdit.setPadding(AndroidUtilities.dp(16), AndroidUtilities.dp(12), AndroidUtilities.dp(16), AndroidUtilities.dp(12));
                org.telegram.ui.ActionBar.AlertDialog.Builder kb = new org.telegram.ui.ActionBar.AlertDialog.Builder(act);
                kb.setTitle("Gemini API kalit");
                kb.setView(keyEdit);
                kb.setPositiveButton(org.telegram.messenger.LocaleController.getString("OK", R.string.OK), (dd, w) -> setApiKey(keyEdit.getText() != null ? keyEdit.getText().toString() : ""));
                kb.setNegativeButton(org.telegram.messenger.LocaleController.getString("Cancel", R.string.Cancel), null);
                kb.show();
            });
        });

        fragment.showDialog(dlg);
    }
}
