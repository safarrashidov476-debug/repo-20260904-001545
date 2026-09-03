#!/usr/bin/env python3
"""
Tiflogram: yuklash tugashi tovushi + TalkBack ogohlantirish.
Rejimlar: check / apply

Muammo tahlili (Telegram DrKLO/Telegram manbasi):
------------------------------------------------
1) downloadingFiles / recentDownloadingFiles ga faqat
   MessageObject.putInDownloadsStore == true VA document != null
   bo'lgan yuklamalar qo'shiladi (FileLoader.loadFileInternal).
   Foto (ImageLocation, document yo'q) hech qachon ro'yxatga tushmaydi.

2) onDownloadComplete fileDidLoaded dan OLDIN chaqiriladi, lekin
   runOnUIThread orqali — shuning uchun fileLoaded handler paytida
   element downloadingFiles yoki recentDownloadingFiles da bo'lishi mumkin.

3) Eski pach faqat getDocument() orqali FileLoader.getAttachFileName
   solishtirardi. Foto, ba'zi audio/web va putInDownloadsStore=false
   (avtomatik) yuklamalarda match bo'lmas edi.

Yechim:
- loadingFileMessagesObservers (handler boshida hali o'chirilmagan)
  orqali putInDownloadsStore tekshirish — eng ishonchli.
- Zaxira: downloadingFiles + recentDownloadingFiles ni document
  fileName VA MessageObject.getFileName() bilan solishtirish.
- Muvaffaqiyatli user-yuklamada tovush + TalkBack "Yuklash tugadi".
"""

import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "check"

FIXES = [
    {
        "id": 10,
        "label": "DownloadController: fileLoaded -> tovush va TalkBack",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/DownloadController.java",
        "old": '''        } else if (id == NotificationCenter.fileLoaded || id == NotificationCenter.httpFileDidLoad) {
            listenerInProgress = true;
            String fileName = (String) args[0];''',
        "new": '''        } else if (id == NotificationCenter.fileLoaded || id == NotificationCenter.httpFileDidLoad) {
            listenerInProgress = true;
            String fileName = (String) args[0];
            // Tiflogram: tovush FAQAT foydalanuvchi o'zi boshlagan yuklamada.
            // 1) loadingFileMessagesObservers — hali remove qilinmagan; putInDownloadsStore
            //    eng ishonchli belgi (didPressButton / didPressMiniButton da o'rnatiladi).
            // 2) Zaxira: downloadingFiles + recentDownloadingFiles (document yoki getFileName).
            boolean tiflogramIsUserDownload = false;
            try {
                ArrayList<MessageObject> tiflogramObs = loadingFileMessagesObservers.get(fileName);
                if (tiflogramObs != null) {
                    for (int _i = 0; _i < tiflogramObs.size() && !tiflogramIsUserDownload; _i++) {
                        MessageObject _mo = tiflogramObs.get(_i);
                        if (_mo != null && _mo.putInDownloadsStore) {
                            tiflogramIsUserDownload = true;
                        }
                    }
                }
                if (!tiflogramIsUserDownload) {
                    for (int _i = 0; _i < downloadingFiles.size() && !tiflogramIsUserDownload; _i++) {
                        MessageObject _mo = downloadingFiles.get(_i);
                        if (_mo == null) continue;
                        if (_mo.putInDownloadsStore) {
                            if (_mo.getDocument() != null &&
                                    fileName.equals(FileLoader.getAttachFileName(_mo.getDocument()))) {
                                tiflogramIsUserDownload = true;
                            } else if (fileName.equals(_mo.getFileName())) {
                                tiflogramIsUserDownload = true;
                            }
                        }
                    }
                }
                if (!tiflogramIsUserDownload) {
                    for (int _i = 0; _i < recentDownloadingFiles.size() && !tiflogramIsUserDownload; _i++) {
                        MessageObject _mo = recentDownloadingFiles.get(_i);
                        if (_mo == null) continue;
                        if (_mo.putInDownloadsStore) {
                            if (_mo.getDocument() != null &&
                                    fileName.equals(FileLoader.getAttachFileName(_mo.getDocument()))) {
                                tiflogramIsUserDownload = true;
                            } else if (fileName.equals(_mo.getFileName())) {
                                tiflogramIsUserDownload = true;
                            }
                        }
                    }
                }
            } catch (Throwable ignore) {
            }
            FileLog.d("TiflogramSound fileName=" + fileName + " match=" + tiflogramIsUserDownload
                    + " downloadingFiles.size=" + downloadingFiles.size()
                    + " recentDownloadingFiles.size=" + recentDownloadingFiles.size());
            if (tiflogramIsUserDownload) {
                try {
                    android.media.MediaPlayer mp = android.media.MediaPlayer.create(
                            ApplicationLoader.applicationContext,
                            org.telegram.messenger.R.raw.tiflogram_dl_done);
                    if (mp != null) {
                        mp.setOnCompletionListener(android.media.MediaPlayer::release);
                        mp.start();
                    }
                } catch (Throwable ignore) {
                }
                try {
                    android.view.accessibility.AccessibilityManager am =
                            (android.view.accessibility.AccessibilityManager)
                                    ApplicationLoader.applicationContext.getSystemService(
                                            android.content.Context.ACCESSIBILITY_SERVICE);
                    if (am != null && am.isEnabled()) {
                        android.view.accessibility.AccessibilityEvent ev =
                                android.view.accessibility.AccessibilityEvent.obtain(
                                        android.view.accessibility.AccessibilityEvent.TYPE_ANNOUNCEMENT);
                        ev.getText().add("Yuklash tugadi");
                        am.sendAccessibilityEvent(ev);
                    }
                } catch (Throwable ignore) {
                }
            }''',
    },
]


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

    print(f"=== Rejim: {MODE} (yuklash tovushi) ===\n")
    results = []
    file_cache = {}

    for fix in FIXES:
        path = fix["path"]
        if path not in file_cache:
            file_cache[path] = read_file(path)
        content = file_cache[path]
        if content is None:
            print(f"❌ [{fix['id']}] {fix['label']} — fayl topilmadi")
            results.append(False)
            continue
        if fix["old"] not in content:
            if "TiflogramSound fileName=" in content or "tiflogramIsUserDownload" in content:
                print(f"✅ [{fix['id']}] {fix['label']} — allaqachon qo'llangan")
                results.append(True)
            else:
                print(f"❌ [{fix['id']}] {fix['label']} — eski matn topilmadi")
                results.append(False)
            continue
        print(f"✅ [{fix['id']}] {fix['label']}")
        results.append(True)

    failed = results.count(False)
    print(f"\nOK: {len(results)-failed}/{len(results)}")
    if MODE == "check":
        sys.exit(1 if failed else 0)
    if failed:
        print("⛔ Hech narsa o'zgartirilmadi")
        sys.exit(1)

    modified = dict(file_cache)
    for fix in FIXES:
        path = fix["path"]
        if fix["old"] in modified[path]:
            if fix.get("replace_all"):
                modified[path] = modified[path].replace(fix["old"], fix["new"])
            else:
                modified[path] = modified[path].replace(fix["old"], fix["new"], 1)

    for path, content in modified.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Yozildi: {path}")
    print("\n✅ Yuklash tovushi patchlari qo'llandi.")


if __name__ == "__main__":
    main()
