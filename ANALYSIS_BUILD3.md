# build-3 tahlili

Repository: `safarrashidov476-debug/repo-20260902-174130`.

Tekshirilgan commit: `17306f8` (`build-3`). APK release asseti `tiflogram-signed.apk`, hajmi 77.5 MB. APK SHA-256: `af67a050feba83ea7f1c37b5cbedd7c8ddfdea6df7a76f0ae5b36b439f9ac885`.

## Asosiy muammo

Workflow `assets/java/org/telegram/messenger/GeminiSafetyScanner.java` va `TiflogramTranslate.java` fayllarini talab qiladi. Avvalgi repository snapshotida Java assetlar to‘liq bo‘lmagani uchun workflow ularni `telegram-src` ichiga ko‘chirish bosqichida to‘xtashi mumkin edi. Repository APK source commitini o‘z ichida saqlamaydi; shuning uchun release APK bilan source bir xil ekanini tekshirish qiyin.

## Qilingan tuzatishlar

- Yetishmayotgan Java assetlar repository’ga qo‘shildi.
- Patch resolver va source-root aniqlash mexanizmi qo‘shildi.
- `run_all_checks.py` endi haqiqiy Telegram checkout ichida ishlaydi.
- Build workflow patchlardan oldin source/preflight check bajaradi.
- Java va resource kataloglari qattiq `TMessagesProj` yo‘liga bog‘lanmaydi.
- `versionCode` oshirish Android limitidan oshmaydigan monotonic algoritmga o‘tkazildi.

Rasmiy Telegram source’ining commiti `62b56a07ca7e30e39f7fd00a6728d6bbd716ca1c`, versiyasi Telegram 12.10.1 (7038). Shu source’da 33/33 patch check muvaffaqiyatli o‘tdi.

Lokal build muhitida faqat JDK 21 bo‘lgani uchun Gradle JDK 17 toolchain talabida to‘xtadi. GitHub Actions workflow JDK 17 o‘rnatadi.
