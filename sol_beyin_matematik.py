import re
import math

import re
import math

def siber_hesapla(kullanici_mesaji):
    mesaj = kullanici_mesaji.lower()
    
    # 🧠 SİBER YAMA: Sözel Matematik Zekası (Cümle içinden rakamları cımbızla)
    rakamlar = [float(r) for r in re.findall(r'\b\d+(?:\.\d+)?\b', mesaj)]
    
    # Eğer cümlede tam 2 tane rakam varsa (Örn: "1453 ile 28'i çarp" veya "Bunun yüzde 10'u")
    if len(rakamlar) == 2:
        sayi1, sayi2 = rakamlar[0], rakamlar[1]
        if any(k in mesaj for k in ["çarp", "*", "çarpımı"]): sonuc = sayi1 * sayi2
        elif any(k in mesaj for k in ["böl", "/"]): 
            if sayi2 == 0: return None, "Sıfıra bölme hatası."
            sonuc = sayi1 / sayi2
        elif any(k in mesaj for k in ["topla", "artı", "+"]): sonuc = sayi1 + sayi2
        elif any(k in mesaj for k in ["çıkar", "eksi", "-", "farkı"]): sonuc = sayi1 - sayi2
        elif any(k in mesaj for k in ["yüzde", "%"]): sonuc = (sayi1 * sayi2) / 100
        else: sonuc = None
        
        if sonuc is not None:
            if sonuc.is_integer(): sonuc = int(sonuc)
            else: sonuc = round(sonuc, 4)
            return sonuc, "Başarılı"

    # Eğer cümlede 1 rakam varsa (Örn: "5'in karesi")
    elif len(rakamlar) == 1:
        sayi = rakamlar[0]
        if "karesi" in mesaj: sonuc = sayi ** 2
        elif "küpü" in mesaj: sonuc = sayi ** 3
        else: return None, "Eksik parametre."
        
        if sonuc.is_integer(): sonuc = int(sonuc)
        else: sonuc = round(sonuc, 4)
        return sonuc, "Başarılı"

    # Klasik Denklem formatıysa (Örn: "5+5") eski usül devam et
    siber_sozluk = {"yüzde": "* 0.01 *", "%": "* 0.01 *", "çarpı": "*", "bölü": "/", "artı": "+", "eksi": "-"}
    for k, s in siber_sozluk.items(): mesaj = mesaj.replace(k, s)
    temiz_islem = re.sub(r'[^0-9\+\-\*\/\.\(\)\s]', '', mesaj).strip()
    
    if re.search(r'\d+\s+\d+', temiz_islem): return None, "Karmaşık Paradoks." # Yan yana 1453 28 kalmasını engeller
    
    try:
        sonuc = eval(temiz_islem, {"__builtins__": None, "math": math}, {})
        if isinstance(sonuc, float):
            if sonuc.is_integer(): sonuc = int(sonuc)
            else: sonuc = round(sonuc, 4)
        return sonuc, "Başarılı"
    except:
        return None, "Karmaşık Paradoks."

def siber_cevirici(kullanici_mesaji):
    mesaj = kullanici_mesaji.lower()
    
    if "zeytinyağı" in mesaj or "yağ" in mesaj:
        sayi_match = re.search(r'([0-9\.]+)\s*(?:litre|lt)', mesaj)
        if sayi_match and ("kilo" in mesaj or "kg" in mesaj):
            litre = float(sayi_match.group(1))
            kilo = round(litre * 0.916, 2)
            return f"{litre} litre zeytinyağı ortalama {kilo} kilogramdır.", "Başarılı"
            
        sayi_match2 = re.search(r'([0-9\.]+)\s*(?:kilo|kg)', mesaj)
        if sayi_match2 and ("litre" in mesaj or "lt" in mesaj):
            kilo = float(sayi_match2.group(1))
            litre = round(kilo / 0.916, 2)
            return f"{kilo} kilo zeytinyağı ortalama {litre} litre hacim kaplar.", "Başarılı"

    birimler = {
        "dönüm": ("alan", 1000), "dekar": ("alan", 1000), "hektar": ("alan", 10000), 
        "metrekare": ("alan", 1), "m2": ("alan", 1),
        "ton": ("agirlik", 1000), "kilo": ("agirlik", 1), "kilogram": ("agirlik", 1), "gram": ("agirlik", 0.001),
        "kilometre": ("uzunluk", 1000), "km": ("uzunluk", 1000), "metre": ("uzunluk", 1), "santimetre": ("uzunluk", 0.01)
    }

    match = re.search(r'([0-9\.]+)\s*([a-zçğıöşü]+).*?(?:kaç|kaçtır|ne kadar|eder)\s+([a-zçğıöşü0-9]+)', mesaj)
    
    if match:
        miktar = float(match.group(1))
        birim1 = match.group(2)
        birim2 = match.group(3)
        
        # 🔥 TÜRKÇE DİLBİLGİSİ KALKANI: Soru eklerini (-dir, -dır, -dur) otomatik siler!
        silinecek_ekler = ["dir", "dır", "tir", "tır", "dur", "dür", "tur", "tür"]
        for ek in silinecek_ekler:
            if birim2.endswith(ek): birim2 = birim2[:-len(ek)]
            if birim1.endswith(ek): birim1 = birim1[:-len(ek)]
                
        if birim1 in birimler and birim2 in birimler:
            tip1, carpan1 = birimler[birim1]
            tip2, carpan2 = birimler[birim2]
            
            if tip1 == tip2:
                sonuc = (miktar * carpan1) / carpan2
                if sonuc.is_integer(): sonuc = int(sonuc)
                else: sonuc = round(sonuc, 2)
                return f"{miktar} {birim1}, tam olarak {sonuc} {birim2} eder.", "Başarılı"
            else:
                return None, f"Mantık Hatası: '{birim1}' ile '{birim2}' birbirine dönüştürülemez."
                
    return None, "Çeviri formatı tam anlaşılamadı. (Örn: '5 dönüm kaç metrekare' şeklinde sorun)"