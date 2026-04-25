import re
import datetime

def niyet_ve_baglam_analizi(kullanici_mesaji, sohbet_gemisi_listesi):
    mesaj = kullanici_mesaji.lower()
    fisilti = "" # Mergen'in ana çekirdeğine gizlice göndereceğimiz komutlar
    
    # ==========================================
    # 0. CHRONOS MODÜLÜ: ZAMAN VE TAKVİM FARKINDALIĞI ⏱️
    # ==========================================
    zaman_kilitleri = ["saat", "zaman", "bugün", "yarın", "dün", "tarih", "hangi gün", "aydayız", "hava", "gece", "gündüz"]
    if any(k in mesaj for k in zaman_kilitleri):
        anlik = datetime.datetime.now()
        saat_bilgisi = anlik.strftime("%H:%M")
        tarih_bilgisi = anlik.strftime("%d-%m-%Y")
        # Mergen'e zamanı fısılda, o da kendi biliyormuş gibi kullansın!
        fisilti += f"[SİSTEM BİLGİSİ: Şu an Karargah Saati: {saat_bilgisi}, Tarih: {tarih_bilgisi}] "

    # ==========================================
    # 1. KISA SÜRELİ SİBER BELLEK (SON OLAYLAR)
    # ==========================================
    son_mergen_cevabi = ""
    son_kullanici_sorusu = ""
    if len(sohbet_gemisi_listesi) > 0:
        son_diyalog = sohbet_gemisi_listesi[-1]
        if "[MERGEN]" in son_diyalog:
            parcalar = son_diyalog.split("[MERGEN]")
            son_kullanici_sorusu = parcalar[0].replace("[İNSAN]", "").strip()
            son_mergen_cevabi = parcalar[-1].strip()

    # ==========================================
    # 2. CÜMLE PARÇALAYICI: ÇOKLU GÖREV RADARI 🪓
    # ==========================================
    coklu_gorev_ayiricilar = [" ve ", " sonra ", " ardından ", " ayrıca "]
    for ayirici in coklu_gorev_ayiricilar:
        if ayirici in mesaj:
            gorevler = mesaj.split(ayirici)
            fisilti += f"[SİSTEM FISILTISI: DİKKAT! Cümle parçalandı. {len(gorevler)} farklı işlem istendi. Hepsini sırayla, eksiksiz yerine getir!] "
            break # İlk ayırıcıdan bölüp fısıltıyı atar

    # ==========================================
    # 3. ACİLİYET VE DUYGU RADARI 🚨
    # ==========================================
    acil_kilitleri = ["acil", "çabuk", "hemen", "acelem var", "hızlıca", "kısa kes", "kısaca"]
    if any(k in mesaj for k in acil_kilitleri):
        fisilti += "[SİSTEM FISILTISI: Efendin acil cevap bekliyor. Asla lafı uzatma, sadece isteneni ver!] "

    # ==========================================
    # 4. DEVAMLILIK VE ZAMİR ÇÖZÜMLEME
    # ==========================================
    baglam_kilitleri = ["bunu", "bunun", "onu", "onun", "peki", "şimdi", "çıkan", "sonucu", "buna", "ondan"]
    hedef_zamirler = ["bunun", "bunu", "onun", "onu", "sonucu", "buna", "ondan"] 
    
    islem_kilitleri = [r"\b\+\b", r"\b-\b", r"\b\*\b", r"\b/\b", r"\b%\b", r"\bçarp\b", r"\bböl\b", r"\btopla\b", r"\bçıkar\b", r"\byüzde\b", r"\bkaresi\b", r"\bküpü\b", r"\bhesapla\b"]
    
    devam_ediyor_mu = any(k in mesaj for k in baglam_kilitleri)
    islem_var_mi = any(re.search(k, mesaj) for k in islem_kilitleri)

    # ==========================================
    # 5. SİBER HİYERARŞİ VE YÖNLENDİRME
    # ==========================================
    
    # A. URL ve Ağ Okuyucu
    if "http" in mesaj or "www" in mesaj:
        return "URL_OKUYUCU", mesaj, fisilti
        
    # B. Sistem Donanım Komutanı
    sistem_kilitleri = ["bilgisayarı", "sesi", "kapat", "uyku modu", "ekranı"]
    if any(k in mesaj for k in sistem_kilitleri) and any(e in mesaj for e in ["kapat", "kıs", "aç", "al"]):
        return "SISTEM_KOMUTANI", mesaj, fisilti

    # C. Devam Eden Bağlam (Matematik VEYA Çeviri)
    if devam_ediyor_mu and son_mergen_cevabi:
        if islem_var_mi:
            rakamlar = re.findall(r'\b\d+(?:\.\d+)?\b', son_mergen_cevabi)
            if rakamlar:
                hedef_rakam = rakamlar[-1] 
                yeni_hedef_mesaj = mesaj
                for kilit in hedef_zamirler:
                    if re.search(r'\b' + kilit + r'\b', yeni_hedef_mesaj):
                        yeni_hedef_mesaj = re.sub(r'\b' + kilit + r'\b', hedef_rakam, yeni_hedef_mesaj)
                        break 
                return "MATEMATIK", yeni_hedef_mesaj, fisilti
                
        cevirici_sorular = ["çevir", "nedir", "ne demek", "nasıl denir"]
        if any(s in mesaj for s in cevirici_sorular):
            fisilti += f"[SİSTEM FISILTISI: Efendin az önceki '{son_mergen_cevabi[:30]}...' cevabını kastediyor.] "

    # D. Siber Birim Çevirici
    cevirici_birimler = [r"\bdönüm\b", r"\bdekar\b", r"\bhektar\b", r"\bmetrekare\b", r"\bm2\b", r"\bkilo\b", r"\bkilogram\b", r"\bton\b", r"\blitre\b", r"\bmetre\b"]
    cevirici_sorular = [r"\bkaç\b", r"\bkaçtır\b", r"\bne kadar\b", r"\beder\b", r"\bçevir\b"]
    
    if any(re.search(b, mesaj) for b in cevirici_birimler) and any(re.search(s, mesaj) for s in cevirici_sorular):
        return "CEVIRICI", mesaj, fisilti
        
    # E. Saf Matematik
    elif islem_var_mi:
        return "MATEMATIK", mesaj, fisilti

    # F. Sohbet ve Danışmanlık
    danismanlik_kilitleri = ["sence", "ne yapmalıyım", "fikrin ne", "çok büyük", "çok küçük", "nasıl yapalım", "ne dersin"]
    if any(k in mesaj for k in danismanlik_kilitleri):
        fisilti += "[SİSTEM FISILTISI: Efendin konu hakkında senden analitik bir fikir ve danışmanlık istiyor.] "
    elif devam_ediyor_mu:
        fisilti += "[SİSTEM FISILTISI: Efendin önceki konuya devam ediyor, bağlamı koparmadan akıcı cevap ver.] "
        
    return "SOHBET", mesaj, fisilti