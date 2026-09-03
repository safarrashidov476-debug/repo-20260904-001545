package org.telegram.messenger;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import org.json.JSONArray;

/**
 * Tiflogram: Telegram serveriga (va Premium tekshiruviga) bog'liq
 * bo'lmagan holda, to'g'ridan-to'g'ri Google Translate'ning bepul
 * endpoint'i orqali matn tarjima qilish.
 *
 * Ishlatish:
 *   TiflogramTranslate.translate(matn, "uz", (natija, xato) -> { ... });
 *
 * "natija" - tarjima qilingan matn (String), muvaffaqiyatsiz bo'lsa null.
 * "xato" - xato bo'lsa Throwable, bo'lmasa null.
 */
public class TiflogramTranslate {

    public interface Callback {
        void onResult(String translatedText, Throwable error);
    }

    /**
     * @param text     tarjima qilinadigan matn
     * @param toLang   maqsad til kodi (masalan "uz")
     * @param callback natija UI thread'da qaytariladi
     */
    public static void translate(String text, String toLang, Callback callback) {
        translate(text, "auto", toLang, callback);
    }

    public static void translate(String text, String fromLang, String toLang, Callback callback) {
        Utilities.globalQueue.postRunnable(() -> {
            try {
                String urlStr = "https://translate.googleapis.com/translate_a/single"
                        + "?client=gtx"
                        + "&sl=" + (fromLang == null || fromLang.isEmpty() ? "auto" : fromLang)
                        + "&tl=" + toLang
                        + "&dt=t&ie=UTF-8&oe=UTF-8"
                        + "&q=" + URLEncoder.encode(text, "UTF-8");

                URL url = new URL(urlStr);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("GET");
                conn.setRequestProperty("User-Agent", "Mozilla/5.0");
                conn.setConnectTimeout(10000);
                conn.setReadTimeout(10000);

                int code = conn.getResponseCode();
                if (code != 200) {
                    throw new RuntimeException("Google Translate HTTP " + code);
                }

                BufferedReader reader = new BufferedReader(
                        new InputStreamReader(conn.getInputStream(), "UTF-8"));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    sb.append(line);
                }
                reader.close();
                conn.disconnect();

                // Javob formati: [[["tarjima","asl matn",null,null,...],...],...]
                JSONArray json = new JSONArray(sb.toString());
                JSONArray sentences = json.getJSONArray(0);
                StringBuilder translated = new StringBuilder();
                for (int i = 0; i < sentences.length(); i++) {
                    JSONArray sentence = sentences.getJSONArray(i);
                    if (sentence.length() > 0 && !sentence.isNull(0)) {
                        translated.append(sentence.getString(0));
                    }
                }

                final String result = translated.toString();
                AndroidUtilities.runOnUIThread(() -> callback.onResult(result, null));
            } catch (Throwable e) {
                FileLog.e(e);
                AndroidUtilities.runOnUIThread(() -> callback.onResult(null, e));
            }
        });
    }
}
