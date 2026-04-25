# 🧠 MERGEN AI CORE: Otonom Siber Asistan ve Karargah İşletim Sistemi

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-Deep_Learning-EE4C2C.svg)
![Flask](https://img.shields.io/badge/Flask-Web_Framework-000000.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer_Vision-5C3EE8.svg)

> *"Bir sistemin en zayıf halkası, daima klavyenin başındaki insandır. Mergen, bu halkayı güçlendirmek için yaratıldı."*

**Mergen AI Core**, hazır API'lerin (ChatGPT vb.) arkasına saklanmak yerine **tamamen sıfırdan, kaputun altına girilerek** PyTorch üzerinde inşa edilmiş **512 nöronlu, kelime bazlı otonom bir yapay zeka asistanıdır.** Sadece bir sohbet botu değil; ortamı görebilen, sesleri duyabilen, metinleri okuyabilen ve bilgisayar donanımınızı anlık takip eden bir **Siber Karargahtır.**

---

## 🦅 SİBER YETENEKLER VE SENSÖRLER

Mergen, dış dünya ile iletişim kurmak için farklı "Siber Duyulara" sahiptir:

* 🧠 **512 Nöronlu Ana Çekirdek (PyTorch):** Kendi yazdığımız, yerel olarak eğitilebilen ve RLHF (İnsan Geri Bildirimiyle Pekiştirmeli Öğrenme) mantığıyla doğru/yanlış cevapları siber karantinaya veya kaliteli tecrübelere ayıran LSTM tabanlı dil modeli.
* 🎛️ **Sol Beyin Yönlendiricisi (Otonom Router):** Mergen'in nöral ağı yorulmadan önce devreye giren analitik beyin.
    * **Cümle Parçalayıcı:** *"Bana saati söyle ve sonra 150'yi 3'e böl"* cümlesini böler ve çoklu görev yapar.
    * **Zamir Çözücü:** Önceki cevaptaki verileri aklında tutarak *"Bunu 5 ile çarp"* gibi ardışık komutları anlar.
    * **Duygu & Aciliyet Radarı:** *"Hemen cevap ver"* denildiğinde lafı uzatmaz, kestirip atar.
* 👁️ **Siber Göz (OpenCV & MobileNetV2):** Kamerayı kullanarak ortamdaki insan yüzlerini sayar ve nesneleri (YOLO mantığıyla) % doğruluk payıyla Türkçe olarak tanır.
* 📖 **Optik Karakter Okuyucu (Tesseract OCR):** Kameraya gösterilen görüntülerdeki metinleri (TR+ENG) saniyeler içinde okur ve analiz eder.
* 🎙️ **Siber Kulak (Whisper AI):** Söylenilenleri yüksek doğrulukla anlar ve metne dökerek işler. Sistem aynı zamanda metinleri sesli olarak size geri okur (TTS).
* 🛰️ **Canlı İnternet Ağı:** Wikipedia, Döviz, Kripto (BTC, ETH, SOL, XRP), Uzay İstasyonu (ISS) konumu ve anlık Hava Durumu verilerini siber uydulardan çeker.

---

## 🛠️ DİJİTAL ATÖLYE VE ARAÇLAR
Sistem sadece konuşmakla kalmaz, size bir dijital asistanın vermesi gereken tüm donanımları sağlar:
* **Siber Silgi:** Rembg ile resimlerin arka planını yapay zekayla kusursuz siler.
* **Siber Sansür:** Resimlerdeki yüzleri otomatik tespit edip buzlar.
* **PDF Cerrahı & PDF to Word:** PDF'leri parçalar veya düzenlenebilir Word dosyasına çevirir.
* **WebP Optimize:** Resimleri kaliteden ödün vermeden %80 sıkıştırır.

---

## 📡 SİBER GÖZETLEME KULESİ (Canlı Radar)
Ayrı bir portta (8081) çalışan **Siber Radar** eklentisi sayesinde; Karargahın kapısından giren ziyaretçilerin IP adreslerini, bulundukları şehri, internet servis sağlayıcılarını, cihaz ve işletim sistemlerini *sayfayı yenilemeden* canlı ve asenkron olarak takip edebilirsiniz. Ayrıca Instagram gibi uygulama içi tarayıcılardan (In-App Browser) gelenleri tespit edip, onları özgür tarayıcılara (Chrome/Safari) yönlendiren otonom bir kalkana sahiptir.

---

## ⚙️ KAPUTUN ALTINDAKİ MİMARİ (Kurulum)

Eğer bu siber karargahı kendi bilgisayarınızda ateşlemek istiyorsanız:

**Gereksinimler:**
```bash
pip install flask flask-socketio torch torchvision torchaudio rembg PyPDF2 pdf2docx opencv-python numpy pytesseract openai-whisper wikipedia psutil beautifulsoup4 requests
