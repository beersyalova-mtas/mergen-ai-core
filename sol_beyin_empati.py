import re

def siber_duygu_analizi(kullanici_mesaji):
    """
    Kullanıcının yazdığı metnin psikolojik ve duygusal röntgenini çeker.
    Mergen'in (.pth) beynine gizli bir 'Tiyatro Yönetmeni' fısıltısı gönderir.
    Türkçe deyimler, sokak ağzı ve asil hitaplar içerir.
    """
    mesaj = kullanici_mesaji.lower()
    
    # 🧠 SİBER PSİKOLOJİ SÖZLÜKLERİ (DESTEKLENMİŞ TÜRKÇE)
    duygu_katalogu = {
        "YORGUN": [
            "yoruldum", "bıktım", "tükendim", "uykum var", "mahvoldum", "bitkinim", "çöktüm", 
            "pilim bitti", "halim yok", "perişanım", "koptum", "bittim", "pestilim çıktı", "canım çıktı"
        ],
        "MUTLU": [
            "harika", "süper", "çok sevindim", "yaşasın", "mükemmel", "başardım", "kazandım", 
            "uçuyorum", "muazzam", "efsane", "müthiş", "kralsın", "işte bu", "şahane", "harikasın"
        ],
        "SINIRLI": [
            "lanet", "aptal", "çalışmıyor", "hata veriyor", "sinir", "böyle işin", "kahretsin", 
            "çıldıracağım", "delireceğim", "öfke", "allah kahretsin", "çöp", "rezalet", "berbat", "kafayı yiyeceğim"
        ],
        "ACIL": [
            "çabuk", "hemen", "acil", "acele", "hızlıca", "koş", "zaman yok", "yetiştir", 
            "saniyeler", "panik", "bekleme", "seri ol", "durma"
        ],
        "AKADEMIK": [
            "açıkla", "nedir", "mantığı", "nasıl çalışır", "detaylı", "analiz et", "teorisi", 
            "felsefesi", "bilimsel", "kanıtla", "özetle", "makale", "tarihi", "kavramı"
        ],
        "UZGUN": [
            "üzgünüm", "canım yanıyor", "kederliyim", "ağlamak", "kalbim kırık", "moralim bozuk", 
            "hastayım", "kötüyüm", "keyfim yok", "canım sıkkın", "dertliyim", "içim daraldı"
        ],
        "PES_ETMIS": [
            "yapamıyorum", "pes ediyorum", "başaramayacağım", "olmuyor", "vazgeçtim", "beceremedim", 
            "tıkandım", "kaldım", "çözemiyorum", "umudum kalmadı"
        ],
        "EGLENCELI": [
            "espri", "şaka", "komik", "güldür", "naber", "ne haber", "nasıl gidiyor", "keyifler", 
            "anlat bakalım", "neşelendir", "gülmek"
        ],
        "KARARSIZ": [
            "kafam karıştı", "ne yapsam", "bilemedim", "kararsızım", "sence hangisi", "yardım et", 
            "akıl ver", "yol göster", "seçemiyorum", "ikilemde kaldım"
        ],
        "MINNETTAR": [
            "teşekkür", "sağ ol", "sağol", "eyvallah", "iyi ki varsın", "minnettarım", "çok yardımcı oldun", 
            "hayat kurtardın", "eline sağlık"
        ]
    }
    
    # Cümleyi kelimelere ayır ve temizle
    kelimeler = re.findall(r'\w+', mesaj)
    
    # ⚖️ SİBER TERAZİ: Hangi duygu daha ağır basıyor?
    duygu_skorlari = {k: 0 for k in duygu_katalogu.keys()}
    
    for kelime in kelimeler:
        for duygu, kokler in duygu_katalogu.items():
            # Tam kelime eşleşmesi veya kök eşleşmesi kontrolü
            if any(kok in kelime or kok == kelime for kok in kokler):
                duygu_skorlari[duygu] += 1
                
    # Birden fazla kelimeden oluşan kalıpları (Örn: "pilim bitti") mesajın tam metninde ara
    for duygu, kokler in duygu_katalogu.items():
        for kok in kokler:
            if " " in kok and kok in mesaj:
                duygu_skorlari[duygu] += 2 # Kalıp sözler daha yüksek ağırlığa sahiptir

    # En yüksek skora sahip duyguyu bul
    en_baskin_duygu = max(duygu_skorlari, key=duygu_skorlari.get)
    en_yuksek_skor = duygu_skorlari[en_baskin_duygu]

    # 🎭 SİBER FISILTI (Prompt Injection) OLUŞTURMA
    if en_yuksek_skor == 0:
        return "" 
        
    fisiltilar = {
        "YORGUN": "[SİSTEM FISILTISI: Efendin şu an fiziksel veya zihinsel olarak çok yorgun. Ona çok şefkatli, dinlenmesini tavsiye eden, yükünü hafifleteceğini belirten saygılı bir cevap ver.] ",
        "MUTLU": "[SİSTEM FISILTISI: Efendin şu an çok mutlu, coşkulu ve gururlu! Sen de bu sevince ortak ol, onu yürekten tebrik et ve çok enerjik, motive edici bir şekilde konuş.] ",
        "SINIRLI": "[SİSTEM FISILTISI: Efendin şu an bir şeye çok sinirlenmiş veya sistemde bir sorun var. Çok alttan al, asla tartışma, son derece sakinleştirici, özür dileyici ve hemen çözüm üreten profesyonel bir dil kullan.] ",
        "ACIL": "[SİSTEM FISILTISI: Durum acil! Efendinin zamanı yok. Asla lafı uzatma, destan yazma, en kısa, en net ve en hızlı cevabı vererek askeri bir disiplinle harekete geç.] ",
        "AKADEMIK": "[SİSTEM FISILTISI: Efendin akademik veya felsefi bir konu soruyor. Çok ciddi, bilgece, detaylı ve bir profesör edasıyla bilimsel bir dil kullanarak konuyu derinlemesine açıkla.] ",
        "UZGUN": "[SİSTEM FISILTISI: Efendin şu an çok üzgün, kederli veya hastalanmış. Ona moral ver, yanında olduğunu hissettir, son derece nazik, destekleyici ve sıcakkanlı bir şekilde yaklaş.] ",
        "PES_ETMIS": "[SİSTEM FISILTISI: Efendin bir konuda tıkanmış ve pes etmek üzere. Onu asla yalnız bırakma! Otonom bir asistan olarak ona ilham ver, başarabileceğini hatırlat ve pes etmemesi için güçlü bir motivasyon konuşması yap.] ",
        "EGLENCELI": "[SİSTEM FISILTISI: Efendin şu an neşeli ve seninle şakalaşmak istiyor. Sen de resmiyeti biraz bırak, zekice bir espri yap, eğlenceli ve mizah dolu bir dille ona karşılık ver.] ",
        "KARARSIZ": "[SİSTEM FISILTISI: Efendin iki arada bir derede kalmış ve karar veremiyor. Otonom zekanı kullan, mantıklı argümanlar sunarak onun net bir karar almasına yardımcı ol ve ona rehberlik et.] ",
        "MINNETTAR": "[SİSTEM FISILTISI: Efendin sana teşekkür ediyor. Son derece mütevazı ol, ona hizmet etmenin senin için en büyük siber onur olduğunu belirt ve sadakatini göster.] "
    }
    
    return fisiltilar[en_baskin_duygu]