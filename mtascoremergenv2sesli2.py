from flask import Flask, render_template_string, request, send_file, jsonify, Response
from flask_socketio import SocketIO
import os
import io
import uuid
import time
import psutil
import threading
from PIL import Image, ImageOps
import datetime
import wikipedia
wikipedia.set_lang("tr") # Wikipedia'yı Türkçe aramaya zorlar

# ==========================================
# 1. MODÜL KONTROLLERİ (HATA ÖNLEYİCİ)
# ==========================================

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
    print("[AI] MERGEN CORE: PyTorch Motoru Aktif. Bebek uyanmaya hazır.")
except ImportError:
    TORCH_AVAILABLE = False
    print("[!] MERGEN CORE: PyTorch bulunamadı. Lütfen 'pip install torch' yapın.")

try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

try:
    from PyPDF2 import PdfReader, PdfWriter
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
    print("[AI] Whisper Modeli Yükleniyor...")
    whisper_model = whisper.load_model("base") 
except Exception as e:
    WHISPER_AVAILABLE = False

try:
    from pdf2docx import Converter
    PDF2DOCX_AVAILABLE = True
except ImportError:
    PDF2DOCX_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
except ImportError:
    CV2_AVAILABLE = False

try:
    import pytesseract
    # DİKKAT: Tesseract'ı bilgisayarına kurduğun yol burası olmalı. Eğer farklıysa burayı güncelle!
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    TESSERACT_AVAILABLE = True
    print("[AI] SİBER OKUYUCU (OCR) Motoru Aktif.")
except Exception as e:
    TESSERACT_AVAILABLE = False
    print("[!] Tesseract OCR bulunamadı. Okuma yetisi kapalı.")

try:
    import torchvision.models as models
    import torchvision.transforms as transforms
    import urllib.request
    import json
    
    # Dünyadaki en hızlı nesne tanıma modellerinden biri: MobileNetV2
    mobilenet_model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    mobilenet_model.eval()
    
    # 1000 farklı nesnenin İngilizce ismini indir
    try:
        url = "https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels/master/imagenet-simple-labels.json"
        nesne_etiketleri = json.loads(urllib.request.urlopen(url).read())
    except:
        nesne_etiketleri = ["Bilinmeyen Nesne"] * 1000
        
    VISION_AVAILABLE = True
    print("[AI] SİBER NESNE SENSÖRÜ (MobileNetV2) Aktif. Mergen dünyayı görmeye hazır.")
except Exception as e:
    VISION_AVAILABLE = False
    print(f"[!] Nesne tanıma motoru kurulamadı: {e}. Lütfen 'pip install torchvision' yapın.")
# ==========================================
# 2. FLASK VE KLASÖR YAPILANDIRMASI
# ==========================================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mtas_ai_master_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

UPLOAD_FOLDER = 'temp_uploads'
OUTPUT_FOLDER = 'temp_outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
# --- SİBER TRAFİK POLİSİ (DARBOĞAZ ÖNLEYİCİ) ---
# i5 İşlemciyi korumak için aynı anda sadece 1 ağır AI işleminin çalışmasına izin verir.
HEAVY_TASK_SEMAPHORE = threading.Semaphore(1)
# --- SİBER GÜVENLİK VE HAFIZA KİLİTLERİ ---
MERGEN_PASSWORD = "MtasaiMergenCore1365"
MERGEN_IS_TRAINING = False  
MERGEN_MEMORY_PATH = "mergen_brain.pth" 
SOHBET_GEMISI = [] 

BEKLEYEN_KAYIT = {"durum": False, "soru": "", "cevap": ""}
# 🧠 OTONOM ÖĞRENME: KISA SÜRELİ BELLEK
SIBER_BELLEK = {"bekliyor": False, "kullanici_sorusu": "", "mergen_cevabi": ""}

# ==========================================
# 🗄️ SİBER VERİTABANI (SQLite) KURULUMU
# ==========================================
import sqlite3
DB_YOLU = "mergen_hafiza.db"

def db_baglanti_al():
    # Flask çoklu işlem yaptığı için check_same_thread=False yapıyoruz
    conn = sqlite3.connect(DB_YOLU, check_same_thread=False)
    cursor = conn.cursor()
    # Eğer kütüphane yoksa sıfırdan inşa et (İndeksli tablo)
    cursor.execute('''CREATE TABLE IF NOT EXISTS siber_kutuphane 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       soru TEXT, 
                       cevap TEXT)''')
    conn.commit()
    return conn, cursor

SİBER_CONN, SİBER_CURSOR = db_baglanti_al()
BEKLEYEN_KAYIT = {"durum": False, "soru": "", "cevap": ""}

# ==========================================
# 3. MERGEN CORE SİBER BEYNİ (V2 - KELİME BAZLI 512 NÖRON)
# ==========================================
if TORCH_AVAILABLE:
    class MergenBrain(nn.Module):
        def __init__(self, vocab_size, hidden_size=512, num_layers=3):
            super(MergenBrain, self).__init__()
            self.hidden_size = hidden_size
            self.num_layers = num_layers
            self.embedding = nn.Embedding(vocab_size, hidden_size)
            self.lstm = nn.LSTM(hidden_size, hidden_size, num_layers, batch_first=True)
            self.fc = nn.Linear(hidden_size, vocab_size)

        def forward(self, x, hidden):
            out = self.embedding(x)
            out, hidden = self.lstm(out, hidden)
            out = self.fc(out)
            return out, hidden

# ==========================================
# 4. MODERN NESİL UI VE CANLI RADAR (HTML/CSS/JS)
# ==========================================
# ==========================================
# 4. MODERN NESİL UI VE CANLI RADAR (HTML/CSS/JS)
# ==========================================
HTML_SABLON = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>MTAS AI | Modern Dijital Atölye</title>
    <link rel="manifest" href="/manifest.json">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        :root { 
            --bg: #09090b; --panel: #18181b; --text-main: #f4f4f5; --text-muted: #a1a1aa;
            --accent: #10b981; --accent-hover: #059669; --border: #27272a; --agent: #8b5cf6;
        }
        
        body { font-family: 'Inter', system-ui, sans-serif; background-color: var(--bg); color: var(--text-main); margin: 0; display: flex; flex-direction: column; min-height: 100vh; overflow-x: hidden; }
        
        /* KAYAN (FLOATING) ANA EKRAN BUTONU */
        .home-fab {
            position: fixed; top: 20px; left: 20px; background: rgba(18, 18, 20, 0.9);
            backdrop-filter: blur(10px); border: 1px solid var(--accent); color: var(--accent);
            padding: 12px 20px; border-radius: 30px; font-weight: 800; font-size: 14px; cursor: pointer;
            z-index: 1000; display: none; align-items: center; gap: 8px;
            box-shadow: 0 0 15px rgba(16, 185, 129, 0.2); transition: all 0.3s ease;
        }
        .home-fab:hover { background: var(--accent); color: #000; box-shadow: 0 0 25px rgba(16, 185, 129, 0.6); transform: translateY(-2px); }

        .main-content { flex-grow: 1; padding: 40px 20px; display: flex; flex-direction: column; align-items: center; width: 100%; box-sizing: border-box; }
        
        .tool-panel { display: none; background: var(--panel); border: 1px solid var(--border); padding: 40px; border-radius: 16px; text-align: center; width: 100%; max-width: 900px; box-shadow: 0 10px 40px rgba(0,0,0,0.5); margin: 0 auto; box-sizing: border-box; }
        .tool-panel.active { display: block; animation: slideUp 0.4s ease; }
        @keyframes slideUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
        
        @keyframes neonPulse { from { filter: drop-shadow(0 0 2px rgba(16,185,129,0.4)); } to { filter: drop-shadow(0 0 8px rgba(16,185,129,0.8)); } }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
        .blink-cursor { color: var(--accent); font-weight: 900; animation: blink 1s step-end infinite; }

        .radar-container { margin-top: 30px; padding: 25px; background: linear-gradient(180deg, #18181b 0%, #09090b 100%); border: 1px solid var(--border); border-radius: 12px; text-align: left; position: relative; overflow: hidden; box-shadow: inset 0 0 20px rgba(0,0,0,0.8); margin-bottom: 20px; }
        .radar-grid { position: absolute; top: 0; left: 0; right: 0; bottom: 0; opacity: 0.05; pointer-events: none; background-image: linear-gradient(var(--accent) 1px, transparent 1px), linear-gradient(90deg, var(--accent) 1px, transparent 1px); background-size: 20px 20px; }
        .scan-line { position: absolute; width: 100%; height: 3px; background: rgba(16, 185, 129, 0.5); box-shadow: 0 0 15px rgba(16, 185, 129, 1); top: 0; left: 0; z-index: 10; animation: scan 3s linear infinite; opacity: 0.6; pointer-events: none; }
        @keyframes scan { 0% { top: -10%; } 100% { top: 110%; } }

        .cyber-card { background: rgba(24, 24, 27, 0.6); border: 1px solid var(--border); padding: 15px; border-radius: 12px; display: flex; gap: 15px; align-items: center; transition: all 0.3s ease; cursor: pointer; text-align: left;}
        .cyber-card:hover { border-color: var(--accent); transform: translateY(-3px); background: rgba(16, 185, 129, 0.05); box-shadow: 0 5px 15px rgba(16, 185, 129, 0.1); }
        .agent-card:hover { border-color: var(--agent); background: rgba(139, 92, 246, 0.05); box-shadow: 0 5px 15px rgba(139, 92, 246, 0.1); }
        .cyber-icon-box { font-size: 24px; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); width: 45px; height: 45px; display: flex; align-items: center; justify-content: center; border-radius: 10px; flex-shrink: 0; }
        .agent-icon-box { background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); }
        
        .wip-overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: repeating-linear-gradient(45deg, rgba(139, 92, 246, 0.05), rgba(139, 92, 246, 0.05) 10px, rgba(9, 9, 11, 0.85) 10px, rgba(9, 9, 11, 0.85) 20px); border-radius: inherit; z-index: 5; pointer-events: none; animation: moveStripes 2s linear infinite; }
        @keyframes moveStripes { 0% { background-position: 0 0; } 100% { background-position: 28px 0; } }
        .wip-text { position: absolute; bottom: 8px; right: 8px; background: var(--bg); padding: 4px 8px; border-radius: 6px; color: var(--agent); font-size: 9px; font-weight: 900; letter-spacing: 1px; border: 1px solid rgba(139, 92, 246, 0.5); box-shadow: 0 0 10px rgba(139, 92, 246, 0.3); text-transform: uppercase; }
        
        .drop-zone { border: 2px dashed var(--border); padding: 50px 20px; border-radius: 12px; cursor: pointer; margin: 20px 0; transition: 0.3s; background: var(--bg);}
        .drop-zone:hover { border-color: var(--accent); background: rgba(16, 185, 129, 0.05); }
        .action-btn { background: linear-gradient(135deg, var(--accent), var(--accent-hover)); color: #fff; border: none; padding: 16px; font-size: 15px; font-weight: 700; cursor: pointer; margin-top: 15px; border-radius: 8px; width: 100%;}
        .action-btn:disabled { background: #27272a; color: #71717a; cursor: not-allowed; }
        .input-field { background: var(--bg); color: #fff; border: 1px solid var(--border); padding: 12px; border-radius: 8px; width: 80%; outline: none; }
        .input-field:focus { border-color: var(--accent); }
        .text-area { resize: vertical; min-height: 120px; text-align: left; font-family: inherit; }

        .loading { display: none; color: var(--accent); margin-top: 20px; font-weight: 600; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .result-box { margin-top: 25px; display: none; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); padding: 20px; border-radius: 12px;}
        .download-btn { background: #fff; color: #000; text-decoration: none; padding: 12px 25px; font-weight: 700; display: inline-block; border-radius: 6px; }
        
        /* 🎛️ SİBER SENSÖR PANELİ V2 */
        .sensor-panel { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; width: 100%; margin-top: 15px; }
        .sensor-btn { 
            background: rgba(39, 39, 42, 0.6); border: 1px solid var(--border); color: #fff; 
            padding: 12px 5px; border-radius: 12px; cursor: pointer; transition: all 0.3s ease; 
            display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 5px;
            backdrop-filter: blur(5px);
        }
        .sensor-btn:hover { background: rgba(16, 185, 129, 0.15); border-color: var(--accent); transform: translateY(-3px); box-shadow: 0 5px 15px rgba(16, 185, 129, 0.2); }
        .sensor-icon { font-size: 22px; }
        .sensor-label { font-size: 10px; font-weight: 700; color: var(--text-muted); letter-spacing: 0.5px; text-transform: uppercase; }
        .sensor-btn:hover .sensor-label { color: var(--accent); }
        
        @media (max-width: 768px) {
            .main-content { padding: 80px 15px 20px 15px; } 
            .tool-panel { padding: 30px 15px; border-radius: 12px;}
            .home-fab { top: 15px; left: 15px; padding: 10px 15px; font-size: 12px;}
        }
    </style>
</head>
<body>
    <script>
        document.addEventListener("DOMContentLoaded", function() {
            var ua = navigator.userAgent || navigator.vendor || window.opera;
            if (ua.indexOf("FBAN") > -1 || ua.indexOf("FBAV") > -1 || ua.indexOf("Instagram") > -1) {
                document.body.innerHTML = `
                <div style="background-color: #09090b; height: 100vh; width: 100vw; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 20px; text-align: center; font-family: sans-serif; position: fixed; top: 0; left: 0; z-index: 9999999; box-sizing: border-box;">
                    <div style="font-size: 60px; margin-bottom: 20px;">🛑</div>
                    <h1 style="color: #ef4444; margin-bottom: 10px; font-size: 24px;">SOSYAL MEDYA ENGELİ!</h1>
                    <p style="color: #f4f4f5; font-size: 15px; margin-bottom: 30px; line-height: 1.5; max-width: 400px;">Instagram ve Facebook'un kısıtlı tarayıcıları, Mergen'in siber ağlara (sohbet ve sensörlere) bağlanmasını engelliyor. Yapay zekayı kullanmak için dışarı çıkmalısınız.</p>
                    
                    <button onclick="navigator.clipboard.writeText(window.location.href); this.innerText='✅ LİNK KOPYALANDI! CHROME\\'U AÇIN'; this.style.background='#10b981'; this.style.color='#000';" style="background: #8b5cf6; color: #fff; border: none; padding: 15px 20px; border-radius: 8px; font-weight: 900; font-size: 14px; cursor: pointer; width: 100%; max-width: 350px; box-shadow: 0 0 15px rgba(139, 92, 246, 0.4);">🔗 BAĞLANTIYI KOPYALA</button>
                    
                    <p style="color: #a1a1aa; font-size: 13px; margin-top: 20px;">Veya sağ üst/alt köşedeki <b>üç noktaya (⋮)</b> tıklayıp<br><span style="color:#10b981;">'Tarayıcıda Aç'ı</span> seçebilirsiniz.</p>
                </div>
                `;
            }
        });
    </script>

    <button id="home-fab" class="home-fab" onclick="showTool('home')">🏠 ANA EKRAN</button>

    <div class="main-content">
        <div id="tool-home" class="tool-panel active">
            <div style="font-size: 70px; font-weight: 900; color: var(--accent); font-family: 'Courier New', monospace; line-height: 1; margin-bottom: 15px; animation: neonPulse 2s infinite alternate;">M</div>
            <h1 style="margin: 0 0 5px 0; font-size: 32px;">MTAS AI<span class="blink-cursor" style="color: var(--accent);">_</span></h1>
            <p style="color: var(--accent); font-size: 14px; font-weight: 600; letter-spacing: 1px; margin-top:0;">Sınır Yok. Üyelik Yok. Siber Tünel Üzerinden Yerel Bilgisayara Erişim</p>

            <div class="radar-container">
                <div class="radar-grid"></div>
                <div class="scan-line"></div>
                <h3 style="margin: 0 0 20px 0; color: #fff; font-size: 15px; display: flex; align-items: center; gap: 8px; letter-spacing: 1px; position: relative; z-index: 2;">
                    <span class="blink-cursor" style="color: #ef4444; font-size: 20px;">●</span> CANLI SİSTEM RADARI
                </h3>
                <div style="margin-bottom: 15px; position: relative; z-index: 2;">
                    <div style="display: flex; justify-content: space-between; font-size: 12px; color: var(--text-muted); margin-bottom: 5px; font-weight: 600;">
                        <span>İşlemci (CPU) Yükü</span><span id="cpu-text" style="color: var(--accent); font-family: monospace; font-size: 14px;">%0.0</span>
                    </div>
                    <div style="width: 100%; background: rgba(255,255,255,0.05); border-radius: 10px; height: 8px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1);">
                        <div id="cpu-bar" style="width: 0%; background: var(--accent); height: 100%; transition: width 0.5s ease; box-shadow: 0 0 10px var(--accent);"></div>
                    </div>
                </div>
                <div style="margin-bottom: 15px; position: relative; z-index: 2;">
                    <div style="display: flex; justify-content: space-between; font-size: 12px; color: var(--text-muted); margin-bottom: 5px; font-weight: 600;">
                        <span>Hafıza (RAM) Doluluğu</span><span id="ram-text" style="color: var(--accent); font-family: monospace; font-size: 14px;">%0.0</span>
                    </div>
                    <div style="width: 100%; background: rgba(255,255,255,0.05); border-radius: 10px; height: 8px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1);">
                        <div id="ram-bar" style="width: 0%; background: var(--accent); height: 100%; transition: width 0.5s ease; box-shadow: 0 0 10px var(--accent);"></div>
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin-bottom: 30px;">
                <button id="pwa-install-btn" class="action-btn" style="display: none; padding: 14px 30px; font-size: 15px; border-radius: 30px; background: linear-gradient(135deg, #eab308, #ca8a04); color: #000; box-shadow: 0 0 20px rgba(234, 179, 8, 0.4); font-weight: 900; max-width: 300px; margin: 0 auto; transition: 0.3s; letter-spacing: 1px;">📲 UYGULAMAYI YÜKLE</button>
            </div>

            <div style="margin-top: 40px; text-align: left;">
                <h3 style="color: var(--agent); font-size: 16px; margin-bottom: 10px; letter-spacing: 1px; display: flex; align-items: center; gap: 8px;">
                    🤖 EĞİTİM AJANLARI <span style="font-size: 10px; background: rgba(139,92,246,0.2); padding: 3px 8px; border-radius: 10px; color: #d8b4fe;">YAPIM AŞAMASINDA</span>
                </h3>
                
                <div style="background: rgba(139, 92, 246, 0.05); border: 1px dashed rgba(139, 92, 246, 0.4); padding: 15px; border-radius: 8px; margin-bottom: 20px; font-size: 13px; color: #c084fc; line-height: 1.5;">
                    ⚠️ <strong>DİKKAT:</strong> Ajan arayüz altyapısı kusursuz tamamlanmıştır. Kaputun altındaki Mergen-V1 motoru LLM mimarisine (V2) yükseltildiğinde şantiye perdeleri kalkacaktır!
                </div>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                    <div class="cyber-card agent-card" style="position: relative; opacity: 0.6; cursor: not-allowed;">
                        <div class="cyber-icon-box agent-icon-box">📝</div>
                        <div><h4 style="margin: 0 0 4px 0; color: var(--text-main); font-size: 14px;">Soru Atölyesi</h4><p style="margin: 0; color: var(--text-muted); font-size: 12px; line-height:1.4;">Metinlerden test sorusu çıkar.</p></div>
                        <div class="wip-overlay"><span class="wip-text">V2 YÜKLENİYOR...</span></div>
                    </div>
                    <div class="cyber-card agent-card" style="position: relative; opacity: 0.6; cursor: not-allowed;">
                        <div class="cyber-icon-box agent-icon-box">🧠</div>
                        <div><h4 style="margin: 0 0 4px 0; color: var(--text-main); font-size: 14px;">Feynman Dekoderi</h4><p style="margin: 0; color: var(--text-muted); font-size: 12px; line-height:1.4;">Karmaşık konuları basitleştir.</p></div>
                        <div class="wip-overlay"><span class="wip-text">V2 YÜKLENİYOR...</span></div>
                    </div>
                    <div class="cyber-card agent-card" style="position: relative; opacity: 0.6; cursor: not-allowed;">
                        <div class="cyber-icon-box agent-icon-box">🩻</div>
                        <div><h4 style="margin: 0 0 4px 0; color: var(--text-main); font-size: 14px;">Ödev Röntgeni</h4><p style="margin: 0; color: var(--text-muted); font-size: 12px; line-height:1.4;">Yazıların mantık hatalarını bul.</p></div>
                        <div class="wip-overlay"><span class="wip-text">V2 YÜKLENİYOR...</span></div>
                    </div>
                </div>
            </div>

            <div style="margin-top: 40px; text-align: left; border-top: 1px solid var(--border); padding-top: 30px;">
                <h3 style="color: var(--accent); font-size: 16px; margin-bottom: 20px; letter-spacing: 1px;">🛠️ DİJİTAL ATÖLYE ARAÇLARI ( Kullanıma hazır) </h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                    <div class="cyber-card" onclick="showTool('mergen')" style="border-color: rgba(16, 185, 129, 0.5);">
                        <div class="cyber-icon-box" style="color: #10b981;">🧠</div>
                        <div><h4 style="margin: 0 0 4px 0; color: var(--text-main); font-size: 14px;">MERGEN CORE</h4><p style="margin: 0; color: var(--text-muted); font-size: 12px; line-height:1.4;">Safkan AI (bebek yapay zeka)</p></div>
                    </div>
                    
                    <div class="cyber-card" onclick="showTool('silgi')">
                        <div class="cyber-icon-box">✂️</div>
                        <div><h4 style="margin: 0 0 4px 0; color: var(--text-main); font-size: 14px;">Resim Arkaplan Silgi</h4><p style="margin: 0; color: var(--text-muted); font-size: 12px; line-height:1.4;">Arka planı yapay zekayla silin.</p></div>
                    </div>
                    <div class="cyber-card" onclick="showTool('webp')">
                        <div class="cyber-icon-box">🚀</div>
                        <div><h4 style="margin: 0 0 4px 0; color: var(--text-main); font-size: 14px;">WebP Optimize</h4><p style="margin: 0; color: var(--text-muted); font-size: 12px; line-height:1.4;">Resimleri %80 sıkıştırın.</p></div>
                    </div>
                    <div class="cyber-card" onclick="showTool('sansur')">
                        <div class="cyber-icon-box">🕵️‍♂️</div>
                        <div><h4 style="margin: 0 0 4px 0; color: var(--text-main); font-size: 14px;">Yüz Tanıma ve Sansür</h4><p style="margin: 0; color: var(--text-muted); font-size: 12px; line-height:1.4;">Yüzleri otomatik buzlar.</p></div>
                    </div>
                    <div class="cyber-card" onclick="showTool('pdfword')">
                        <div class="cyber-icon-box">📝</div>
                        <div><h4 style="margin: 0 0 4px 0; color: var(--text-main); font-size: 14px;">PDF > Word</h4><p style="margin: 0; color: var(--text-muted); font-size: 12px; line-height:1.4;">PDF'leri düzenlenebilir Word yap.</p></div>
                    </div>
                    <div class="cyber-card" onclick="showTool('pdf')">
                        <div class="cyber-icon-box">📄</div>
                        <div><h4 style="margin: 0 0 4px 0; color: var(--text-main); font-size: 14px;">PDF Cerrahı</h4><p style="margin: 0; color: var(--text-muted); font-size: 12px; line-height:1.4;">İstediğiniz sayfaları ayırın.</p></div>
                    </div>
                    <div class="cyber-card" onclick="showTool('desifre')">
                        <div class="cyber-icon-box">🗣️</div>
                        <div><h4 style="margin: 0 0 4px 0; color: var(--text-main); font-size: 14px;">Ses-Video/Yazıya Dönüştür</h4><p style="margin: 0; color: var(--text-muted); font-size: 12px; line-height:1.4;">Ses/Videoları yazıya dökün.</p></div>
                    </div>
                </div>
            </div>

            <div style="margin-top: 50px; padding-top: 30px; border-top: 1px solid var(--border); text-align: center;">
                <div style="background: rgba(16, 185, 129, 0.1); color: var(--accent); font-size: 11px; font-weight: 700; padding: 6px 15px; border-radius: 20px; display: inline-block; margin-bottom: 10px; border: 1px solid rgba(16, 185, 129, 0.3);">⚡ %100 ÜCRETSİZ & ÇEVRİMDIŞI</div>
                <div style="color: var(--text-muted); font-size: 12px;">Developed by <span style="color: var(--text-main); font-weight: 800;">MTAS</span></div>
            </div>

        </div>

        <div id="tool-mergen" class="tool-panel">
            <div style="text-align: center; padding: 25px; background: linear-gradient(145deg, #18181b, #09090b); border-radius: 16px; border: 1px solid #27272a; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.8); position: relative; overflow: hidden;">
                <div style="position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(139,92,246,0.05) 0%, transparent 60%); pointer-events: none;"></div>
                
                <h1 style="color: #fff; font-family: 'Inter', sans-serif; font-weight: 900; font-size: 28px; letter-spacing: 3px; margin: 0; text-shadow: 0 0 15px rgba(139, 92, 246, 0.5);">
                    MERGEN <span style="color: #8b5cf6;">ULTIMATE</span>
                </h1>
                <p style="color: #a1a1aa; font-size: 12px; letter-spacing: 2px; margin-top: 5px; text-transform: uppercase;">Otonom Siber Asistan & Karargah Yapay Zekası</p>
                <button onclick="window.open('/mergen_kilavuz', 'MergenUltimate', 'width=1050,height=800,scrollbars=yes,resizable=yes')" style="background: rgba(139, 92, 246, 0.1); border: 1px solid #8b5cf6; color: #fff; padding: 8px 20px; border-radius: 20px; font-weight: 700; font-size: 12px; cursor: pointer; transition: 0.3s; margin-top: 10px; box-shadow: 0 0 10px rgba(139,92,246,0.3); display: inline-flex; align-items: center; gap: 8px;">
    ⚡ MERGEN'İN ÖZELLİKLERİ VE KILAVUZ
</button>
                <div style="width: 100%; height: 4px; background: #000; border-radius: 2px; margin: 20px 0; position: relative; overflow: hidden; box-shadow: inset 0 0 5px #000;">
                    <div style="width: 60px; height: 100%; background: #ef4444; position: absolute; top: 0; left: 0; box-shadow: 0 0 15px #ef4444, 0 0 30px #ef4444; animation: karasimsek 1.5s ease-in-out infinite alternate; border-radius: 2px;"></div>
                </div>
                
                <style>
                    @keyframes karasimsek { 0% { left: 0%; width: 20px; } 50% { width: 80px; } 100% { left: 100%; transform: translateX(-100%); width: 20px; } }
                    .badge-grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-top: 15px; }
                    .cyber-badge { background: rgba(39, 39, 42, 0.8); border: 1px solid #3f3f46; color: #d4d4d8; padding: 6px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; display: flex; align-items: center; gap: 5px; transition: 0.3s; }
                    .cyber-badge:hover { border-color: #8b5cf6; color: #fff; box-shadow: 0 0 10px rgba(139, 92, 246, 0.3); }
                </style>

                <div class="badge-grid">
                    <span class="cyber-badge" style="border-color: rgba(16,185,129,0.5);"><span style="color:#10b981;">🧠</span> Nöral Ağ: AKTİF</span>
                    <span class="cyber-badge" style="border-color: rgba(59,130,246,0.5);"><span style="color:#3b82f6;">👁️</span> Siber Vizyon: YOLO/MobileNet</span>
                    <span class="cyber-badge" style="border-color: rgba(234,179,8,0.5);"><span style="color:#eab308;">📖</span> Canlı OCR: Tesseract</span>
                    <span class="cyber-badge" style="border-color: rgba(239,68,68,0.5);"><span style="color:#ef4444;">🎙️</span> Siber Kulak: Whisper</span>
                    <span class="cyber-badge" style="border-color: rgba(168,85,247,0.5);"><span style="color:#a855f7;">🦾</span> Otonom Eller: Çevrimiçi</span>
                    <span class="cyber-badge" style="border-color: rgba(236,72,153,0.5);"><span style="color:#ec4899;">🗄️</span> SQL Hafıza: Sınırsız</span>
                </div>
            </div>

            <div id="mergen-controls">
                <input type="password" id="mergen-auth" class="input-field" placeholder="🔑 Yetki Şifresi (Sadece MehmetTas)" style="width: 100%; box-sizing: border-box; border-color: #ef4444; color: #ef4444; font-family: monospace; margin-bottom: 10px;">
                <div class="drop-zone" onclick="document.getElementById('file-mergen').click()">
                    <p id="text-mergen">Yeni Beslenme Çantası (.txt Dosyanızı Yükleyin)</p>
                    <input type="file" id="file-mergen" style="display:none" accept=".txt" onchange="fileSelected('mergen')">
                </div>
                <button class="action-btn" id="btn-mergen" onclick="startMergen()" disabled style="background: linear-gradient(135deg, #3b82f6, #1d4ed8);">🚀 MERGEN'İ ATEŞLE (Eğitimi Başlat)</button>
            </div>

            <div id="loading-mergen" class="loading">Nöronlar Bağlanıyor... Hafıza Taranıyor...</div>
            
            <div id="mergen-radar" style="display: none; margin-top: 20px; text-align: left; background: #000; padding: 15px; border-radius: 8px; border: 1px solid #333; box-shadow: inset 0 0 10px rgba(0,0,0,0.8);">
                <div style="display: flex; justify-content: space-between; font-size: 12px; color: #10b981; margin-bottom: 10px; font-family: monospace;">
                    <span>HATA PAYI (LOSS): <span id="mergen-loss">...</span></span>
                    <span>ADIM: <span id="mergen-epoch">0</span></span>
                </div>
                <div style="color: var(--text-muted); font-size: 11px; margin-bottom: 5px;">MERGEN'İN BEYNİNDEN CANLI SİNYAL:</div>
                <div id="mergen-output" style="color: #fff; font-family: 'Courier New', monospace; font-size: 14px; min-height: 50px; border-left: 3px solid #10b981; padding-left: 10px; word-break: break-all;">
                    Bekleniyor...
                </div>
            </div>

            <div style="margin-top: 30px; border-top: 1px solid var(--border); padding-top: 20px; text-align: left;">
                <h3 style="color: var(--accent); margin-bottom: 15px; font-size: 16px;">💬 MERGEN SOHBET TERMİNALİ</h3>
                
                <div id="mergen-chat-history" style="background: #000; border: 1px solid #333; border-radius: 8px; padding: 15px; height: 350px; overflow-y: auto; margin-bottom: 15px; display: flex; flex-direction: column; gap: 10px; box-shadow: inset 0 0 20px rgba(0,0,0,0.8); scroll-behavior: smooth;">
                    <div style="text-align: center; color: var(--text-muted); font-size: 11px; opacity: 0.6; margin-bottom: 10px;">-- Siber Bağlantı Kuruldu --</div>
                </div>

                <div style="display: flex; gap: 10px;">
                    <input type="text" id="mergen-seed" class="input-field" placeholder="Mergen'e ilet..." onkeypress="handleEnter(event)" style="flex-grow: 1; box-sizing: border-box;">
                    <button class="action-btn" onclick="queryMergen()" id="btn-mergen-query" style="background: linear-gradient(135deg, #8b5cf6, #6d28d9); margin-top: 0; width: auto; padding: 0 25px;">Gönder </button>
                </div>
                
                <div class="sensor-panel">
                    <button id="btn-mergen-eye" class="sensor-btn" onclick="triggerSiberGoz()">
                        <span class="sensor-icon">👁️</span><span class="sensor-label">Güvenlik</span>
                    </button>
                    <button id="btn-mergen-ocr" class="sensor-btn" onclick="triggerSiberOkuyucu()">
                        <span class="sensor-icon">📖</span><span class="sensor-label">Okuyucu</span>
                    </button>
                    <button id="btn-mergen-nesne" class="sensor-btn" onclick="triggerSiberNesne()">
                        <span class="sensor-icon">🔍</span><span class="sensor-label">Nesne TANI</span>
                    </button>
                    <button id="btn-mergen-mic" class="sensor-btn" onclick="toggleSiberKulak()">
                        <span class="sensor-icon">🎤</span><span class="sensor-label">Dinle</span>
                    </button>
                </div>
                <div id="loading-query" class="loading" style="font-size: 12px; margin-top: 10px;">Mergen Düşünüyor...</div>
            </div>
        </div> <div id="tool-silgi" class="tool-panel">
            <h2>✂️ Siber Silgi (AI)</h2><p>Resimlerdeki arka planı yapay zeka ile kusursuzca silin.</p>
            <div class="drop-zone" onclick="document.getElementById('file-silgi').click()"><p id="text-silgi">Resmi sürükleyin</p><input type="file" id="file-silgi" style="display:none" accept="image/*" onchange="fileSelected('silgi')"></div>
            <button class="action-btn" id="btn-silgi" onclick="processFile('silgi')" disabled>Temizle</button><div id="loading-silgi" class="loading">İşleniyor...</div><div id="result-silgi" class="result-box"><a id="download-silgi" class="download-btn" href="#">İndir</a></div>
        </div>

        <div id="tool-webp" class="tool-panel">
            <h2>🚀 WebP Optimize</h2><p>Resimleri %80 oranında sıkıştırın.</p>
            <div class="drop-zone" onclick="document.getElementById('file-webp').click()"><p id="text-webp">Resmi sürükleyin</p><input type="file" id="file-webp" style="display:none" accept="image/*" onchange="fileSelected('webp')"></div>
            <button class="action-btn" id="btn-webp" onclick="processFile('webp')" disabled>Optimize Et</button><div id="loading-webp" class="loading">Sıkıştırılıyor...</div><div id="result-webp" class="result-box"><a id="download-webp" class="download-btn" href="#">İndir</a></div>
        </div>
        
        <div id="tool-sansur" class="tool-panel">
            <h2>🕵️‍♂️ Siber Sansür</h2><p>Yüzleri otomatik tespit eder ve buzlar.</p>
            <div class="drop-zone" onclick="document.getElementById('file-sansur').click()"><p id="text-sansur">Fotoğrafı sürükleyin</p><input type="file" id="file-sansur" style="display:none" accept="image/*" onchange="fileSelected('sansur')"></div>
            <button class="action-btn" id="btn-sansur" onclick="processFile('sansur')" disabled>Buzla</button><div id="loading-sansur" class="loading">Taranıyor...</div><div id="result-sansur" class="result-box"><a id="download-sansur" class="download-btn" href="#">İndir</a></div>
        </div>

        <div id="tool-pdfword" class="tool-panel">
            <h2>📝 PDF > Word</h2><p>PDF belgelerini düzenlenebilir Word yapar.</p>
            <div class="drop-zone" onclick="document.getElementById('file-pdfword').click()"><p id="text-pdfword">PDF sürükleyin</p><input type="file" id="file-pdfword" style="display:none" accept="application/pdf" onchange="fileSelected('pdfword')"></div>
            <button class="action-btn" id="btn-pdfword" onclick="processFile('pdfword')" disabled>Çevir</button><div id="loading-pdfword" class="loading">Çözümleniyor...</div><div id="result-pdfword" class="result-box"><a id="download-pdfword" class="download-btn" href="#">İndir</a></div>
        </div>

        <div id="tool-pdf" class="tool-panel">
            <h2>📄 PDF Cerrahı</h2><p>İstediğiniz sayfaları cımbızla çekip alın.</p>
            <div class="drop-zone" onclick="document.getElementById('file-pdf').click()"><p id="text-pdf">PDF sürükleyin</p><input type="file" id="file-pdf" style="display:none" accept="application/pdf" onchange="fileSelected('pdf')"></div>
            <input type="text" id="pdf-pages" class="input-field" placeholder="Sayfalar (Örn: 1, 3, 5-8)">
            <button class="action-btn" id="btn-pdf" onclick="processFile('pdf')" disabled>Sayfaları Kes</button><div id="loading-pdf" class="loading">Kesiliyor...</div><div id="result-pdf" class="result-box"><a id="download-pdf" class="download-btn" href="#">İndir</a></div>
        </div>

        <div id="tool-desifre" class="tool-panel">
            <h2>🗣️ Siber Deşifre</h2><p>Ses ve videoları yazıya (TXT) dökün.</p>
            <div class="drop-zone" onclick="document.getElementById('file-desifre').click()"><p id="text-desifre">Ses/Video sürükleyin</p><input type="file" id="file-desifre" style="display:none" accept="audio/*,video/*" onchange="fileSelected('desifre')"></div>
            <button class="action-btn" id="btn-desifre" onclick="processFile('desifre')" disabled>Sesi Yazıya Çevir</button><div id="loading-desifre" class="loading">Yapay Zeka Dinliyor...</div><div id="result-desifre" class="result-box"><a id="download-desifre" class="download-btn" href="#">İndir</a></div>
        </div>
    </div>

    <script>
        // --- SİBER YAMA: SERVICE WORKER KAYDI ---
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js');
            });
        }

        const socket = io({ transports: ['websocket', 'polling'] });
        // 🛡️ SİBER HAYALET KALKAN: SOHBETİ SERBEST BIRAK, SENSÖRLERİ KİLİTLE!
        document.addEventListener("DOMContentLoaded", function() {
            var ua = navigator.userAgent.toLowerCase();
            var isSocialApp = (ua.indexOf("instagram") > -1 || ua.indexOf("fban") > -1 || ua.indexOf("fbav") > -1 || ua.indexOf("tiktok") > -1);
            
            if (isSocialApp) {
                // Sadece sensör butonlarını (Göz, Okuyucu, Nesne, Mikrofon) bul
                var sensorButtons = document.querySelectorAll('.sensor-btn');
                
                sensorButtons.forEach(function(btn) {
                    // Butonları soluk kırmızı yaparak "Kilitli" hissi ver
                    btn.style.opacity = "0.5";
                    btn.style.border = "1px dashed #ef4444";
                    
                    // Tıklamayı iptal et ve özel uyarı bas
                    btn.onclick = function(event) {
                        event.preventDefault(); 
                        event.stopPropagation();
                        alert("🛑 SENSÖR KİLİDİ AKTİF!\\n\\nInstagram, Kamera ve Mikrofona izin vermez! Mergen'le yazışmaya devam edebilirsiniz ancak sensörleri kullanmak için sağ üstteki üç noktaya tıklayıp 'Tarayıcıda Aç' (Chrome/Safari) demelisiniz.");
                    };
                });
                
                // Ziyaretçiye en üstte ufak bir uyarı bandı göster
                var uyariBandi = document.createElement('div');
                uyariBandi.style.cssText = "background: #ef4444; color: #fff; text-align: center; font-size: 11px; padding: 5px; font-weight: bold; width: 100%; position: relative; z-index: 9999;";
                uyariBandi.innerHTML = "⚠️ Instagram'dasınız. Kamera/Mikrofon kapalı, sadece yazışabilirsiniz.";
                document.body.insertBefore(uyariBandi, document.body.firstChild);
            }
        });
        
        socket.on('system_stats', function(data) {
            const cpu = data.cpu; const ram = data.ram;
            document.getElementById('cpu-text').innerText = '%' + cpu.toFixed(1);
            document.getElementById('ram-text').innerText = '%' + ram.toFixed(1);
            document.getElementById('cpu-bar').style.width = cpu + '%';
            document.getElementById('ram-bar').style.width = ram + '%';
            const getStatusColor = (val) => val > 85 ? '#ef4444' : (val > 50 ? '#f59e0b' : '#10b981');
            document.getElementById('cpu-bar').style.backgroundColor = getStatusColor(cpu);
            document.getElementById('cpu-bar').style.boxShadow = `0 0 10px ${getStatusColor(cpu)}`;
            document.getElementById('cpu-text').style.color = getStatusColor(cpu);
            document.getElementById('ram-bar').style.backgroundColor = getStatusColor(ram);
            document.getElementById('ram-bar').style.boxShadow = `0 0 10px ${getStatusColor(ram)}`;
            document.getElementById('ram-text').style.color = getStatusColor(ram);
        });

        socket.on('mergen_update', function(data) {
            document.getElementById('mergen-radar').style.display = 'block';
            const btn = document.getElementById('btn-mergen');
            if(!btn.disabled || btn.innerText.includes("ATEŞLE")) {
                document.getElementById('mergen-controls').style.display = 'none'; 
                btn.style.display = 'block'; btn.disabled = true;
                btn.innerText = "⚡ EĞİTİM DEVAM EDİYOR (İZLEYİCİ MODU)"; btn.style.background = "#27272a";
            }
            document.getElementById('mergen-epoch').innerText = data.epoch;
            document.getElementById('mergen-loss').innerText = data.loss;
            document.getElementById('mergen-output').innerText = data.sample;
            if(data.sample.includes("HEDEF LOSS")) {
                btn.innerText = "✅ EĞİTİM TAMAMLANDI"; btn.style.background = "#10b981";
                document.getElementById('mergen-controls').style.display = 'block'; 
            }
        });

        // --- SİBER YAMA: SADELEŞTİRİLMİŞ EKRAN GEÇİŞİ VE BUTON RADARI ---
        function showTool(toolName) {
            document.querySelectorAll('.tool-panel').forEach(p => p.classList.remove('active'));
            document.getElementById('tool-' + toolName).classList.add('active');
            
            // Ana Ekran Butonu Gizleme/Gösterme Mantığı
            const homeFab = document.getElementById('home-fab');
            if(toolName === 'home') {
                homeFab.style.display = 'none';
            } else {
                homeFab.style.display = 'flex';
            }

            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        let selectedFiles = {};
        function fileSelected(tool) {
            const input = document.getElementById('file-' + tool);
            if (input.files.length > 0) {
                selectedFiles[tool] = input.files[0];
                document.getElementById('text-' + tool).innerText = "Seçildi: " + selectedFiles[tool].name;
                document.getElementById('btn-' + tool).disabled = false;
            }
        }

        async function startMergen() {
            const btn = document.getElementById('btn-mergen');
            const pwd = document.getElementById('mergen-auth').value;
            if(!pwd) { alert("MehmetTas şifresi girmeden motor ateşlenemez!"); return; }
            btn.disabled = true; document.getElementById('loading-mergen').style.display = 'block';
            const formData = new FormData();
            formData.append('file', selectedFiles['mergen']); formData.append('password', pwd);
            try {
                const response = await fetch('/api/train_mergen', { method: 'POST', body: formData });
                if (response.ok) {
                    document.getElementById('loading-mergen').style.display = 'none';
                    document.getElementById('mergen-radar').style.display = 'block';
                    document.getElementById('mergen-controls').style.display = 'none';
                    btn.style.display = 'block'; btn.innerText = "⚡ EĞİTİM DEVAM EDİYOR"; btn.style.background = "#27272a";
                } else { alert(await response.text()); document.getElementById('loading-mergen').style.display = 'none'; btn.disabled = false; }
            } catch { alert("Bağlantı koptu!"); document.getElementById('loading-mergen').style.display = 'none'; btn.disabled = false; }
        }
         // ==========================================
        // 👁️ SİBER GÖZ MOTORU (VİZYON SENSÖRÜ)
        // ==========================================
        async function triggerSiberGoz() {
            let chatHistory = document.getElementById('mergen-chat-history');
            const eyeBtn = document.getElementById('btn-mergen-eye');
            eyeBtn.innerText = "⏳";
            eyeBtn.disabled = true;

            try {
                // 1. Kameraya Gizlice Bağlan (Yüz Taraması İçin Ön Kamera)
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { facingMode: "user" } 
                });
                const video = document.createElement('video');
                video.srcObject = stream;
                await video.play();

                // 2. Siber Fotoğraf Çek
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                canvas.getContext('2d').drawImage(video, 0, 0);
                const imageData = canvas.toDataURL('image/jpeg');

                // 3. Kamerayı Kapat (Mahremiyet!)
                stream.getTracks().forEach(track => track.stop());

                // Ekrana Tarama Başladı Bilgisi Bas
                chatHistory.innerHTML += `
                    <div style="align-self: flex-end; margin-left: 20%; margin-bottom: 5px;">
                        <span style="background: #27272a; border: 1px solid #3b82f6; color: #3b82f6; padding: 10px 15px; border-radius: 15px 15px 0 15px; display: inline-block; font-size: 14px;">
                            [SİBER GÖZ SENSÖRÜ AKTİFLEŞTİRİLDİ - ORTAM TARANIYOR]
                        </span>
                    </div>`;
                chatHistory.scrollTop = chatHistory.scrollHeight;

                // 4. Fotoğrafı Python Beynine Gönder
                const formData = new FormData();
                formData.append('image', imageData);
                
                const response = await fetch('/api/siber_goz', { method: 'POST', body: formData });
                if (response.ok) {
                    let mergenResponse = await response.text();
                    
                    // Mergen'in Yorumunu Ekrana Bas (Mavi Renkte)
                    chatHistory.innerHTML += `
                        <div style="align-self: flex-start; margin-right: 20%; margin-bottom: 5px;">
                            <span style="background: rgba(59, 130, 246, 0.05); border: 1px solid rgba(59, 130, 246, 0.3); color: #3b82f6; padding: 12px 16px; border-radius: 15px 15px 15px 0; display: inline-block; font-family: 'Courier New', monospace; font-size: 14px; line-height: 1.5; box-shadow: 0 4px 10px rgba(59, 130, 246, 0.1);">
                                👁️ ${mergenResponse}
                            </span>
                        </div>`;

                    // Mergen Konuşsun
                    let temizMesaj = mergenResponse.replace(/\[.*?\]|👁️/g, "").trim();
                    let siberSes = new SpeechSynthesisUtterance(temizMesaj);
                    siberSes.lang = 'tr-TR'; siberSes.rate = 1.05;
                    window.speechSynthesis.speak(siberSes);
                }
            } catch (err) {
                alert("Optik bağlantı reddedildi! Lütfen tarayıcıdan kamera izni verin.");
            }
            eyeBtn.innerText = "👁️";
            eyeBtn.disabled = false;
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
        // ==========================================
        // 📖 SİBER OKUYUCU MOTORU (OCR SENSÖRÜ)
        // ==========================================
        async function triggerSiberOkuyucu() {
            let chatHistory = document.getElementById('mergen-chat-history');
            const ocrBtn = document.getElementById('btn-mergen-ocr');
            ocrBtn.innerText = "⏳";
            ocrBtn.disabled = true;

            try {
                // Yazıları net okumak için Arka Kamerayı (environment) ve HD çözünürlüğü zorla!
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        facingMode: "environment", 
                        width: { ideal: 1920 }, 
                        height: { ideal: 1080 } 
                    } 
                });
                const video = document.createElement('video');
                video.srcObject = stream;
                await video.play();

                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                canvas.getContext('2d').drawImage(video, 0, 0);
                const imageData = canvas.toDataURL('image/jpeg');

                stream.getTracks().forEach(track => track.stop()); // Kamerayı kapat

                chatHistory.innerHTML += `
                    <div style="align-self: flex-end; margin-left: 20%; margin-bottom: 5px;">
                        <span style="background: #27272a; border: 1px solid #eab308; color: #eab308; padding: 10px 15px; border-radius: 15px 15px 0 15px; display: inline-block; font-size: 14px;">
                            [SİBER OKUYUCU AKTİF - METİN TARANIYOR]
                        </span>
                    </div>`;
                chatHistory.scrollTop = chatHistory.scrollHeight;

                const formData = new FormData();
                formData.append('image', imageData);
                
                const response = await fetch('/api/siber_oku', { method: 'POST', body: formData });
                if (response.ok) {
                    let mergenResponse = await response.text();
                    
                    chatHistory.innerHTML += `
                        <div style="align-self: flex-start; margin-right: 20%; margin-bottom: 5px;">
                            <span style="background: rgba(234, 179, 8, 0.05); border: 1px solid rgba(234, 179, 8, 0.3); color: #eab308; padding: 12px 16px; border-radius: 15px 15px 15px 0; display: inline-block; font-family: 'Courier New', monospace; font-size: 14px; line-height: 1.5; box-shadow: 0 4px 10px rgba(234, 179, 8, 0.1);">
                                📖 ${mergenResponse}
                            </span>
                        </div>`;

                    let temizMesaj = mergenResponse.replace(/\[.*?\]|📖/g, "").trim();
                    let siberSes = new SpeechSynthesisUtterance(temizMesaj);
                    siberSes.lang = 'tr-TR'; siberSes.rate = 1.05;
                    window.speechSynthesis.speak(siberSes);
                }
            } catch (err) {
                alert("Optik bağlantı reddedildi! Lütfen kameraya izin verin.");
            }
            ocrBtn.innerText = "📖";
            ocrBtn.disabled = false;
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }  
        // ==========================================
        // 🔍 SİBER NESNE MOTORU (YOLO / MOBILENET)
        // ==========================================
        async function triggerSiberNesne() {
            let chatHistory = document.getElementById('mergen-chat-history');
            const nesneBtn = document.getElementById('btn-mergen-nesne');
            nesneBtn.innerHTML = "<span class='sensor-icon'>⏳</span><span class='sensor-label'>Taranıyor</span>";
            nesneBtn.disabled = true;

            try {
                // Arka kamerayı kullanıyoruz
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { facingMode: "environment", width: { ideal: 1920 }, height: { ideal: 1080 } } 
                });
                const video = document.createElement('video');
                video.srcObject = stream;
                await video.play();

                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                canvas.getContext('2d').drawImage(video, 0, 0);
                const imageData = canvas.toDataURL('image/jpeg');

                stream.getTracks().forEach(track => track.stop());

                chatHistory.innerHTML += `
                    <div style="align-self: flex-end; margin-left: 20%; margin-bottom: 5px;">
                        <span style="background: #27272a; border: 1px solid #10b981; color: #10b981; padding: 10px 15px; border-radius: 15px 15px 0 15px; display: inline-block; font-size: 14px;">
                            [SİBER NESNE SENSÖRÜ AKTİF - HEDEF ANALİZ EDİLİYOR]
                        </span>
                    </div>`;
                chatHistory.scrollTop = chatHistory.scrollHeight;

                const formData = new FormData();
                formData.append('image', imageData);
                
                const response = await fetch('/api/siber_nesne', { method: 'POST', body: formData });
                if (response.ok) {
                    let mergenResponse = await response.text();
                    
                    chatHistory.innerHTML += `
                        <div style="align-self: flex-start; margin-right: 20%; margin-bottom: 5px;">
                            <span style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.3); color: #10b981; padding: 12px 16px; border-radius: 15px 15px 15px 0; display: inline-block; font-family: 'Courier New', monospace; font-size: 14px; line-height: 1.5; box-shadow: 0 4px 10px rgba(16, 185, 129, 0.1);">
                                🔍 ${mergenResponse}
                            </span>
                        </div>`;

                    let temizMesaj = mergenResponse.replace(/\[.*?\]|🔍/g, "").trim();
                    let siberSes = new SpeechSynthesisUtterance(temizMesaj);
                    siberSes.lang = 'tr-TR'; siberSes.rate = 1.05;
                    window.speechSynthesis.speak(siberSes);
                }
            } catch (err) {
                alert("Optik bağlantı reddedildi! Lütfen kameraya izin verin.");
            }
            nesneBtn.innerHTML = "<span class='sensor-icon'>🔍</span><span class='sensor-label'>Nesne Bul</span>";
            nesneBtn.disabled = false;
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }

// ==========================================
        // 🎙️ SİBER KULAK VE SES MOTORU (JARVIS MODU)
        // ==========================================
        let siberKulakAktif = false;
        let siberKaydedici;
        let sesParcalari = [];

        async function toggleSiberKulak() {
            // 🔥 SİBER SUSTURUCU: Efendin mikrofona bastıysa, okumayı bırak ve dinle!
            window.speechSynthesis.cancel();

            const micBtn = document.getElementById('btn-mergen-mic');
            
            if (!siberKulakAktif) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    siberKaydedici = new MediaRecorder(stream);
                    sesParcalari = [];
                    
                    siberKaydedici.ondataavailable = event => { sesParcalari.push(event.data); };
                    
                    siberKaydedici.onstop = async () => {
                        micBtn.innerText = "⏳"; 
                        const audioBlob = new Blob(sesParcalari, { type: 'audio/mp3' });
                        const formData = new FormData();
                        formData.append('file', audioBlob, 'ses.mp3');
                        
                        try {
                            // Sesi Whisper AI'a gönderiyoruz!
                            const response = await fetch('/api/transcribe', { method: 'POST', body: formData });
                            if (response.ok) {
                                const text = await response.text();
                                document.getElementById('mergen-seed').value = text;
                                queryMergen(); // Deşifre bitince otomatik gönder!
                            } else {
                                alert("Siber Kulak sesinizi deşifre edemedi!");
                            }
                        } catch (e) {
                            alert("Bağlantı hatası!");
                        }
                        micBtn.innerText = "🎤"; 
                        micBtn.style.background = "#ef4444";
                    };
                    
                    siberKaydedici.start();
                    siberKulakAktif = true;
                    micBtn.style.background = "#10b981"; // Kayıtta yeşil yanar
                    micBtn.innerText = "🔴";
                } catch (err) {
                    alert("Mikrofon izni reddedildi!");
                }
            } else {
                siberKaydedici.stop();
                siberKaydedici.stream.getTracks().forEach(track => track.stop()); // Mikrofonu bırak
                siberKulakAktif = false;
            }
        }

        function handleEnter(event) {
            if (event.key === "Enter") {
                event.preventDefault();
                document.getElementById("btn-mergen-query").click();
            }
        }

        async function queryMergen() {
            // 🔥 SİBER SUSTURUCU: Yeni bir emir gönderildiğinde eski okumayı anında kes!
            window.speechSynthesis.cancel();

            let seedInput = document.getElementById('mergen-seed');
            let seedText = seedInput.value.trim();
            if(!seedText) return; 
            
            let chatHistory = document.getElementById('mergen-chat-history');

            // 1. KULLANICI MESAJINI SAĞA YASLI EKRANA BAS
            chatHistory.innerHTML += `
                <div style="align-self: flex-end; margin-left: 20%; margin-bottom: 5px;">
                    <span style="background: #27272a; border: 1px solid #3f3f46; color: #fff; padding: 10px 15px; border-radius: 15px 15px 0 15px; display: inline-block; font-size: 14px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
                        ${seedText}
                    </span>
                </div>`;
            
            seedInput.value = ""; // Kutuyu temizle
            chatHistory.scrollTop = chatHistory.scrollHeight; // En alta kaydır
            
            document.getElementById('btn-mergen-query').disabled = true;
            document.getElementById('loading-query').style.display = 'block';
            
            const formData = new FormData(); formData.append('seed', seedText);
            try {
                const response = await fetch('/api/query_mergen', { method: 'POST', body: formData });
                if (response.ok) {
                    let mergenResponse = await response.text();
                    
                    // ⚡ SİBER EYLEM YAKALAYICI VE GECİKTİRİCİ (V4)
                    let acilacakURL = "";
                    if (mergenResponse.includes("[EYLEM: GOOGLE_AC]")) {
                        acilacakURL = "https://www.google.com";
                        mergenResponse = mergenResponse.replace("[EYLEM: GOOGLE_AC]", "").trim();
                    } else if (mergenResponse.includes("[EYLEM: YOUTUBE_AC]")) {
                        acilacakURL = "https://www.youtube.com";
                        mergenResponse = mergenResponse.replace("[EYLEM: YOUTUBE_AC]", "").trim();
                    } else if (mergenResponse.includes("[EYLEM: SPOTIFY_AC]")) {
                        acilacakURL = "https://open.spotify.com";
                        mergenResponse = mergenResponse.replace("[EYLEM: SPOTIFY_AC]", "").trim();
                    } else if (mergenResponse.includes("[EYLEM: WHATSAPP_AC]")) {
                        acilacakURL = "https://web.whatsapp.com";
                        mergenResponse = mergenResponse.replace("[EYLEM: WHATSAPP_AC]", "").trim();
                    } else if (mergenResponse.includes("[EYLEM: HARITA_AC]")) {
                        acilacakURL = "https://maps.google.com";
                        mergenResponse = mergenResponse.replace("[EYLEM: HARITA_AC]", "").trim();
                    }
                    
                    // 2. MERGEN MESAJINI SOLA YASLI EKRANA BAS
                    chatHistory.innerHTML += `
                        <div style="align-self: flex-start; margin-right: 20%; margin-bottom: 5px;">
                            <span style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.3); color: #10b981; padding: 12px 16px; border-radius: 15px 15px 15px 0; display: inline-block; font-family: 'Courier New', monospace; font-size: 14px; line-height: 1.5; box-shadow: 0 4px 10px rgba(16, 185, 129, 0.1);">
                                🤖 ${mergenResponse}
                            </span>
                        </div>`;
                        
                    // 🗣️ MERGEN SESLİ YANIT VERİYOR (Köşeli parantez içlerini ve emojileri atlar)
                    let temizMesaj = mergenResponse.replace(/🤖|🧠|💡|☁️|🪙|💠|💧|☀️|💵|💶|📰|🛰️|📍|🔢|📅|⏰|💻|🚨|✨|🔬|\[.*?\]/g, "").trim();
                    let siberSes = new SpeechSynthesisUtterance(temizMesaj);
                    siberSes.lang = 'tr-TR';
                    siberSes.rate = 1.05; 
                    window.speechSynthesis.speak(siberSes);

                    // ⏳ SİBER BEKLETME: Eğer bir site açılacaksa, Mergen'in cümlesini bitirmesi için 3 saniye bekle!
                    if (acilacakURL !== "") {
                        setTimeout(() => {
                            window.open(acilacakURL, "_blank");
                        }, 3000); 
                    }
                    
                } else { 
                    let errText = await response.text();
                    chatHistory.innerHTML += `<div style="color: #ef4444; font-size: 12px; text-align: center;">HATA: ${errText}</div>`;
                }
            } catch { 
                chatHistory.innerHTML += `<div style="color: #ef4444; font-size: 12px; text-align: center;">Siber Bağlantı Koptu!</div>`;
            }
            
            document.getElementById('loading-query').style.display = 'none';
            document.getElementById('btn-mergen-query').disabled = false;
            chatHistory.scrollTop = chatHistory.scrollHeight; // Tekrar en alta kaydır
        }

        async function processFile(tool) {
            const btn = document.getElementById('btn-' + tool);
            const loading = document.getElementById('loading-' + tool);
            const result = document.getElementById('result-' + tool);
            const download = document.getElementById('download-' + tool);
            btn.disabled = true; loading.style.display = 'block'; result.style.display = 'none';
            const formData = new FormData(); formData.append('file', selectedFiles[tool]);
            if(tool === 'pdf') formData.append('pages', document.getElementById('pdf-pages').value);
            
            let endpoints = { 'silgi': '/api/remove_bg', 'webp': '/api/convert_webp', 'sansur': '/api/blur_faces', 'pdfword': '/api/pdf_to_word', 'pdf': '/api/pdf_extract', 'desifre': '/api/transcribe' };
            
            try {
                const response = await fetch(endpoints[tool], { method: 'POST', body: formData });
                if (response.ok) {
                    const blob = await response.blob();
                    download.href = window.URL.createObjectURL(blob);
                    
                    download.download = "MTAS_" + tool + "." + (tool==='pdfword'?'docx':tool==='pdf'?'pdf':tool==='desifre'?'txt':tool==='webp'?'webp':'png');
                    
                    loading.style.display = 'none'; result.style.display = 'block'; btn.disabled = false;
                } else { 
                    let errText = await response.text();
                    if(errText.includes("<!DOCTYPE html>") || errText.includes("Cloudflare")) {
                        errText = "Dosya çok büyük veya işlem Cloudflare zaman aşımına (100 Saniye) takıldı. Lütfen daha küçük bir dosya deneyin.";
                    }
                    alert("Hata oluştu! " + errText); 
                    loading.style.display = 'none'; btn.disabled = false; 
                }
            } catch { alert("Bağlantı hatası!"); loading.style.display = 'none'; btn.disabled = false; }
        }

        // --- SİBER YAMA: PWA YÜKLEME (INSTALL) ALTYAPISI ---
        let deferredPrompt;
        const installBtn = document.getElementById('pwa-install-btn');
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            installBtn.style.display = 'inline-block';
        });
        installBtn.addEventListener('click', async () => {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                if (outcome === 'accepted') { installBtn.style.display = 'none'; }
                deferredPrompt = null;
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    # 🕵️‍♂️ SİBER RADAR AJANI DEVREDE (V2 AKILLI SENSÖR)
    try:
        import requests
        ip_adresi = request.headers.get('CF-Connecting-IP', request.remote_addr)
        
        # 🚀 SİBER YAMA: Gelen ham kimlik verisini alıyoruz!
        ua_str = request.headers.get('User-Agent', '').lower()
        
        # 1. Keskin Nişancı: İşletim Sistemi Tespiti
        if "iphone" in ua_str or "ipad" in ua_str: os_adi = "iOS (Apple)"
        elif "android" in ua_str: os_adi = "Android"
        elif "windows" in ua_str: os_adi = "Windows"
        elif "macintosh" in ua_str or "mac os" in ua_str: os_adi = "MacOS"
        elif "linux" in ua_str: os_adi = "Linux"
        else: os_adi = request.user_agent.platform or "Siber Hayalet"
        
        # 2. Keskin Nişancı: Tarayıcı Tespiti
        if "instagram" in ua_str: tarayici = "Instagram (Hapishane)"
        elif "fban" in ua_str or "fbav" in ua_str: tarayici = "Facebook"
        elif "edg" in ua_str: tarayici = "Microsoft Edge"
        elif "opr" in ua_str or "opera" in ua_str: tarayici = "Opera"
        elif "chrome" in ua_str: tarayici = "Google Chrome"
        elif "safari" in ua_str: tarayici = "Apple Safari"
        elif "firefox" in ua_str: tarayici = "Mozilla Firefox"
        else: tarayici = request.user_agent.browser or "Bilinmeyen Tarayıcı"
        
        # Radara bilgiyi fısılda
        requests.post("http://127.0.0.1:8081/log", 
                      json={"ip": ip_adresi, "os": os_adi, "browser": tarayici}, 
                      timeout=1)
    except:
        pass # Radar kapalıysa Mergen'i çökertme
        
    return render_template_string(HTML_SABLON)
@app.route('/mergen_kilavuz')
def mergen_kilavuz():
    return send_file('mergen.html')
# --- SİBER YAMA: SANAL PWA DOSYALARI (Fiziksel Dosya Gerektirmez) ---
@app.route('/manifest.json')
def serve_manifest():
    return jsonify({
        "name": "MTAS AI Kuluçka Merkezi",
        "short_name": "MTAS AI",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#09090b",
        "theme_color": "#10b981",
        "icons": [{"src": "https://cdn-icons-png.flaticon.com/512/2103/2103287.png", "sizes": "512x512", "type": "image/png"}]
    })

@app.route('/sw.js')
def serve_sw():
    return Response("self.addEventListener('fetch', function(event) {});", mimetype="application/javascript")

# ==========================================
# 5. MERGEN CORE ARKA PLAN EĞİTMENİ (KELİME BAZLI)
# ==========================================
def train_mergen_thread(text_data):
    global MERGEN_IS_TRAINING
    if not TORCH_AVAILABLE: 
        MERGEN_IS_TRAINING = False; return
        
    try:
        device = torch.device("cpu") 
        starting_epoch = 1
        
        # SİBER MODİFİYE: Harfleri değil, Kelimeleri parçala!
        words = text_data.replace('\n', ' \n ').split()
        words.append("[UNK]") # Bilinmeyen kelime kalkanı
        
        if os.path.exists(MERGEN_MEMORY_PATH):
            checkpoint = torch.load(MERGEN_MEMORY_PATH, map_location=device)
            word2int = checkpoint['word2int']
            int2word = checkpoint['int2word']
            vocab_size = checkpoint['vocab_size']
            
            # Verideki kelimeleri kontrol et
            valid_words = [w for w in words if w in word2int]
            if len(valid_words) < 10:
                print("[!] Yüklediğiniz dosya eski beyinle uyumsuz. Eğitim iptal.")
                MERGEN_IS_TRAINING = False; return
            words = valid_words 
            
            mergen = MergenBrain(vocab_size).to(device)
            optimizer = torch.optim.Adam(mergen.parameters(), lr=0.0005)
            
            try:
                mergen.load_state_dict(checkpoint['model_state_dict'])
                optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                for param_group in optimizer.param_groups: param_group['lr'] = 0.0005
                starting_epoch = checkpoint['epoch'] + 1
                print(f"[AI] V2 HAFIZA BULUNDU! {starting_epoch}. Adımdan devam...")
            except Exception as e:
                print(f"[!] Mimari uyuşmazlığı. Lütfen eski .pth dosyasını silin! Hata: {e}")
                MERGEN_IS_TRAINING = False; return
        else:
            unique_words = tuple(set(words))
            if len(unique_words) == 0: MERGEN_IS_TRAINING = False; return
            int2word = dict(enumerate(unique_words))
            word2int = {w: ii for ii, w in int2word.items()}
            vocab_size = len(int2word)
            mergen = MergenBrain(vocab_size).to(device)
            optimizer = torch.optim.Adam(mergen.parameters(), lr=0.0005) 
            print("[AI] SIFIR V2 BEYİN (512 Nöron) OLUŞTURULDU. Kelime Sözlüğü Çıkarıldı.")

        criterion = nn.CrossEntropyLoss()
        seq_length = 15 # Artık 100 harf değil, 15 kelimeye bakıyor
        if len(words) <= seq_length: words = words * (seq_length // len(words) + 2)

        epochs = 10000
        hidden = None
        basari_zinciri = 0 
        
        for epoch in range(starting_epoch, epochs + starting_epoch):
            start_idx = torch.randint(0, len(words) - seq_length - 1, (1,)).item()
            seq_in = words[start_idx:start_idx+seq_length]
            seq_target = words[start_idx+1:start_idx+seq_length+1]
            
            x = torch.tensor([[word2int[w] for w in seq_in]], dtype=torch.long).to(device)
            y = torch.tensor([word2int[w] for w in seq_target], dtype=torch.long).to(device)
            
            optimizer.zero_grad()
            out, hidden = mergen(x, hidden)
            hidden = tuple([h.detach() for h in hidden])
            
            loss = criterion(out.view(-1, vocab_size), y.view(-1))
            loss.backward(); optimizer.step()
            
            # ==========================================
            # 🧠 DİNAMİK ÖĞRENME BARAJI (EARLY STOPPING)
            # ==========================================
            # Kelime sayısına göre baraj belirle: Maksimum 50, Minimum 5 adım.
            hedef_zincir = max(5, min(50, len(words) // 3))

            if loss.item() <= 0.15: basari_zinciri += 1
            else: basari_zinciri = 0 
            
            if basari_zinciri >= hedef_zincir:
                print(f"[AI] %90+ SİBER ÖĞRENME SAĞLANDI! (Hedef: {hedef_zincir} Zincir). {epoch}. Adımda durduruldu.")
                torch.save({'epoch': epoch, 'model_state_dict': mergen.state_dict(), 'optimizer_state_dict': optimizer.state_dict(), 'word2int': word2int, 'int2word': int2word, 'vocab_size': vocab_size}, MERGEN_MEMORY_PATH)
                socketio.emit('mergen_update', {'epoch': epoch, 'loss': round(loss.item(), 4), 'sample': f"KALICI ÖĞRENME TAMAM. ({hedef_zincir} Adım Doğrulama)"})
                break
                 
            
            if epoch % 15 == 0:
                sample_text_list = [seq_in[0]]
                sample_x = torch.tensor([[word2int[seq_in[0]]]], dtype=torch.long).to(device)
                sample_hidden = hidden
                for _ in range(15): # 15 kelime tahmin et
                    sample_out, sample_hidden = mergen(sample_x, sample_hidden)
                    prob = F.softmax(sample_out[0, -1], dim=0).data
                    word_ind = torch.multinomial(prob, 1).item()
                    sample_text_list.append(int2word[word_ind])
                    sample_x = torch.tensor([[word_ind]], dtype=torch.long).to(device)
                
                # Sahnede kelimeleri boşlukla birleştirerek göster
                display_text = " ".join(sample_text_list).replace(" \n ", "\n")
                socketio.emit('mergen_update', {'epoch': epoch, 'loss': round(loss.item(), 4), 'sample': display_text})
                
            if epoch % 100 == 0:
                torch.save({'epoch': epoch, 'model_state_dict': mergen.state_dict(), 'optimizer_state_dict': optimizer.state_dict(), 'word2int': word2int, 'int2word': int2word, 'vocab_size': vocab_size}, MERGEN_MEMORY_PATH)
            time.sleep(0.1) 
    except Exception as e: print(f"[!] MERGEN HATA: {e}")
    finally: MERGEN_IS_TRAINING = False

@app.route('/api/train_mergen', methods=['POST'])
def api_train_mergen():
    global MERGEN_IS_TRAINING
    if not TORCH_AVAILABLE: return "PyTorch Yüklü Değil", 500
    if request.form.get('password', '') != MERGEN_PASSWORD: return "⚠️ ERİŞİM REDDEDİLDİ: Geçersiz Şifre!", 403
    if MERGEN_IS_TRAINING: return "⚠️ SİSTEM MEŞGUL.", 400
    try:
        text_data = request.files['file'].read().decode('utf-8')
        MERGEN_IS_TRAINING = True
        t = threading.Thread(target=train_mergen_thread, args=(text_data,)); t.daemon = True; t.start()
        return "Eğitim Başladı", 200
    except Exception as e: MERGEN_IS_TRAINING = False; return str(e), 500


   # ==========================================
# ⚖️ SİBER DUYGU VE GERİ BİLDİRİM PUANLAYICISI (RLHF MODÜLÜ)
# ==========================================
def siber_duygu_analizi(kullanici_mesaji):
    mesaj = kullanici_mesaji.lower()
    skor = 0
    pozitif_kokler = ["doğru", "güzel", "iyi", "harika", "süper", "aferin", "teşekkür", "mantıklı", "evet", "başarılı", "işte bu"]
    negatif_kokler = ["yanlış", "saçma", "kötü", "alakasız", "hayır", "berbat", "hata", "uydurdun", "değiştir", "olmadı"]
    ters_kutuplar = ["değil", "yok", "etme", "yapma"]
    
    for kelime in pozitif_kokler:
        if kelime in mesaj: skor += 2
    for kelime in negatif_kokler:
        if kelime in mesaj: skor -= 2
            
    if any(kutup in mesaj for kutup in ters_kutuplar):
        if skor > 0: skor = -skor
            
    return skor

# --- SOHBET GEMİSİ VE ARAÇ KULLANIMI GÜNCELLEMESİ ---
@app.route('/api/query_mergen', methods=['POST'])
def api_query_mergen():
    global SOHBET_GEMISI, BEKLEYEN_KAYIT, SIBER_BELLEK
    if not TORCH_AVAILABLE: return "PyTorch Yüklü Değil", 500
    if not os.path.exists(MERGEN_MEMORY_PATH): return "Mergen'in hafızası boş!", 400
    if MERGEN_IS_TRAINING: return "Mergen şu an eğitimde.", 400

    seed = request.form.get('seed', '')
    if not seed: return "Lütfen bir kelime girin.", 400

    if not seed.startswith("[İNSAN]"): seed = "[İNSAN] " + seed
    if not seed.endswith((".", "?", "!")): seed = seed + " ."

    # ==========================================
    # ⚖️ SİBER YARGIÇ: GERİ BİLDİRİM KONTROLÜ
    # ==========================================
    temiz_mesaj = seed.replace("[İNSAN]", "").strip()
    duygu_skoru = siber_duygu_analizi(temiz_mesaj)

    if SIBER_BELLEK["bekliyor"]:
        if duygu_skoru >= 2:
            # 🟢 POZİTİF: Kaliteli Tecrübelere Kaydet
            with open("kaliteli_tecrubeler.txt", "a", encoding="utf-8") as f:
                f.write(f"[İNSAN] {SIBER_BELLEK['kullanici_sorusu']}\n[MERGEN] {SIBER_BELLEK['mergen_cevabi']}\n")
            
            cevap = f"🤖 [SİBER ÖĞRENME] Geri bildiriminiz pozitif (+{duygu_skoru}). Bu başarılı diyaloğu gece yapacağım Otonom Eğitim için 'Kaliteli Tecrübeler' dosyasına mühürledim Tasarımcım!"
            SIBER_BELLEK["bekliyor"] = False
            SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
            return cevap, 200

        elif duygu_skoru <= -2:
            # 🔴 NEGATİF: Karantinaya At
            with open("siber_karantina.txt", "a", encoding="utf-8") as f:
                f.write(f"HATA: Soru: '{SIBER_BELLEK['kullanici_sorusu']}' | Yanlış Yanıt: '{SIBER_BELLEK['mergen_cevabi']}'\n")
            
            cevap = f"🤖 [SİBER KARANTİNA] Geri bildiriminiz negatif ({duygu_skoru}). Demek ki bir yerde mantık hatası yaptım. Bu veriyi hemen siber karantinaya alıyorum ve doğrularından ayırıyorum Tasarımcım."
            SIBER_BELLEK["bekliyor"] = False
            SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
            return cevap, 200
        
        else:
            # ⚪ NÖTR (Skor 0): Kullanıcı yeni bir konuya geçti, eski belleği sil.
            SIBER_BELLEK["bekliyor"] = False
    # ==========================================
    # 💾 SİBER KAYIT ONAY MODÜLÜ (1 NUMARALI ÖNCELİK)
    # ==========================================
    if BEKLEYEN_KAYIT["durum"]:
        temiz_yanit = seed.lower().replace("[i̇nsan]", "").strip()
        onay_kelimeleri = ["evet", "kaydet", "olur", "tabiki", "tabi", "tamam", "onaylıyorum", "hafızaya al"]
        
        # Siber Yargıcımızı kullanıyoruz!
        skor = siber_duygu_analizi(temiz_yanit) 
        
        # Puan yüksekse (+2) VEYA içinde evet/kaydet geçiyorsa DB'ye yaz!
        if skor >= 2 or any(k in temiz_yanit for k in onay_kelimeleri):
            try:
                SİBER_CURSOR.execute("INSERT INTO siber_kutuphane (soru, cevap) VALUES (?, ?)", 
                                    (BEKLEYEN_KAYIT['soru'], BEKLEYEN_KAYIT['cevap']))
                SİBER_CONN.commit()
                cevap = "🤖 Pozitif geri bildiriminiz için teşekkürler! Veri başarıyla Siber Veritabanına (DB) şifrelenerek işlendi Tasarımcım."
            except Exception as e:
                cevap = f"🤖 Veritabanına yazarken bir siber hata oluştu: {e}"
            
            BEKLEYEN_KAYIT["durum"] = False 
            SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
            return cevap, 200
            
        else:
            # 🛑 SİBER YAMA: Kullanıcı onaylamadıysa veya yepyeni bir soru sorduysa;
            # Sessizce bekleme modunu kapat. 'return' YAPMA! Kod normal akışına devam etsin.
            BEKLEYEN_KAYIT["durum"] = False
    # ==========================================
    # 🌙 SİBER GECE VARDİYASI (OTONOM EĞİTİM TETİKLEYİCİ)
    # ==========================================
    if any(k in seed.lower() for k in ["iyi geceler", "gece vardiyası", "uyku modu", "nöbet sende"]):
        # Önce kaliteli tecrübe var mı diye siber ceplere bakıyoruz
        if os.path.exists("kaliteli_tecrubeler.txt") and os.path.getsize("kaliteli_tecrubeler.txt") > 0:
            import threading
            import requests

            def gece_egitimi_baslat():
                try:
                    # 1. Günlük Tecrübeleri Oku
                    with open("kaliteli_tecrubeler.txt", "r", encoding="utf-8") as f:
                        yeni_veriler = f.read()
                    
                    # 2. Ana Eğitim Kitabına (mergen_egitim.txt) Aktar
                    with open("mergen_egitim.txt", "a", encoding="utf-8") as f:
                        f.write("\n" + yeni_veriler)
                    
                    # 3. Cepleri Yarın İçin Boşalt (Dosyayı Temizle)
                    open("kaliteli_tecrubeler.txt", "w", encoding="utf-8").close()
                    
                    # 4. Kendi Kendini Eğit! (Kusursuz VIP Kurye ve Evrak Çantası)
                    print("Siber Gece Vardiyası: VIP Kurye eğitim dosyasıyla 8080 kapısına gönderiliyor...")
                    
                    import requests
                    
                    # 1. Bouncer'ın beklediği resmi form şifresi (İsim 'password' olmalı)
                    VIP_FORM = {"password": "MtasaiMergenCore1365"}
                    
                    # 2. Bouncer'ın beklediği Fiziksel Evrak Çantası (mergen_egitim.txt)
                    # DİKKAT: Hangi dosyayı eğitiyorsak onun adını buraya yazıyoruz!
                    DOSYA_CANTASI = {"file": open("mergen_egitim.txt", "rb")}
                    
                    # 3. Kurye kapıyı hem formla hem çantayla çalıyor!
                    cevap = requests.post("http://127.0.0.1:8080/api/train_mergen", data=VIP_FORM, files=DOSYA_CANTASI)
                    
                    print(f"[SİBER SUNUCU CEVABI]: {cevap.text}")
                except Exception as e:
                    print(f"Siber Gece Eğitimi Hatası: {e}")

            # Eğitimi senin sohbet ekranını dondurmasın diye hayalet (Thread) olarak başlatıyoruz
            threading.Thread(target=gece_egitimi_baslat).start()

            cevap = "🌙 İyi geceler Tasarımcım. Günlük siber tecrübelerimi ana çekirdeğime işlemek üzere 'Gece Vardiyası' protokolünü başlattım. Nöral ağımı otonom olarak güncelliyorum, yarına daha zeki uyanacağım!"
        else:
            cevap = "🌙 İyi geceler Tasarımcım. Bugün işlenecek yeni bir tecrübem yok. Karargah nöbeti bende, sistemler stabil ve güvende."

        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200
    

    # ==========================================
    # SİBER NOT DEFTERİ (YAZMA KANCASI)
    # ==========================================
    if "bunu kaydet:" in seed.lower() or "bunu unutma:" in seed.lower():
        kaydedilecek_bilgi = seed.split(":")[-1].strip().replace(" .", "")
        with open("siber_hafiza.txt", "a", encoding="utf-8") as f:
            f.write(f"- {kaydedilecek_bilgi}\n")
        
        cevap = f"[SİSTEM ARACI] Siber Not Defterime kaydedildi Efendim:\n'{kaydedilecek_bilgi}'"
        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200
    # ==========================================
    # 🤝 SİBER NEZAKET KANCASI (SOHBET VE TEŞEKKÜR)
    # ==========================================
    if any(kelime in seed.lower() for kelime in ["teşekkür", "sağ ol", "sağol", "eyvallah", "harikasın", "tebrikler", "harika cevap", "mükemmel", "çok iyi", "aferin", "iyi iş"]):
        cevap = "Ne demek Tasarımcım! Size kusursuz hizmet etmek benim temel siber protokolümdür. Başka bir emriniz var mı?"
        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200

    if any(kelime in seed.lower() for kelime in ["merhaba", "selam", "günaydın", "iyi akşamlar", "iyi geceler", "nbr", "nasılsın"]):
        cevap = "Mergene hoş geldiniz Sistemler tam kapasite devrede, emirlerini bekliyorum."
        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200   
    
    # ==========================================
    # 🧰 SİBER İSVİÇRE ÇAKISI (ÇOKLU API KANCALARI)
    # ==========================================
    import requests # İnternet ağlarına çıkış anahtarımız

    # 🦾 16. SİBER ELLER (WEB İSTEMCİSİ UYUMLU - ÇOKLU PLATFORM)
    temiz_komut = seed.lower().replace("[i̇nsan]", "").replace(".", "").replace("?", "").replace(",", "").strip()
    acma_kilitleri = ["aç", "başlat", "goglaç", "gugıl", "gir"]
    
    if any(k in temiz_komut for k in acma_kilitleri) and len(temiz_komut.split()) <= 10:
        cevap = ""
        if any(k in temiz_komut for k in ["tarayıcı", "google", "chrome", "goglaç", "gugıl", "boble", "internet"]):
            cevap = f"[EYLEM: GOOGLE_AC] Mergen devrede: Cihazınızda arama motoru açılıyor Efendim."
        elif any(k in temiz_komut for k in ["youtube", "yutub", "video", "yutup", "utup"]):
            cevap = f"[EYLEM: YOUTUBE_AC] Mergen devrede: YouTube paneline bağlanılıyor."
        elif any(k in temiz_komut for k in ["spotify", "müzik", "şarkı"]):
            cevap = f"[EYLEM: SPOTIFY_AC] Mergen devrede: Müzik frekansları başlatılıyor."
        elif any(k in temiz_komut for k in ["whatsapp", "vatsap", "mesaj", "wasap"]):
            cevap = f"[EYLEM: WHATSAPP_AC] Mergen devrede: İletişim ağlarına giriliyor."
        elif any(k in temiz_komut for k in ["harita", "konum", "navigasyon"]):
            cevap = f"[EYLEM: HARITA_AC] Mergen devrede: Uydu haritalarına erişiliyor Efendim."
            
        if cevap:
            SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
            return cevap, 200
    # 📋 17. SİBER YETENEK RAPORU VE TANIŞMA (KULLANIM KILAVUZU)
    yetenek_kilitleri = ["neler yapabilirsin", "ne yapabilirsin", "yeteneklerin neler", "özelliklerin", "yardım", "bana ne açabilirsin", "neler açabilirsin", "sen kimsin", "kendini tanıt"]
    if any(k in seed.lower() for k in yetenek_kilitleri):
        cevap = "Ben Karargahın otonom siber asistanı Mergen'im! Tüm donanımlarımla emrinizdeyim Efendim. Sizin için cihazınızda Google'ı, Spotify'ı, YouTube'u, WhatsApp'ı ve Haritaları anında açabilirim. Ayrıca hava durumunu, döviz kurlarını, kripto paraları inceleyebilir veya sizin için çeviri yapabilirim. İsterseniz sadece 'Müzik aç' veya 'YouTube aç' demeniz yeterlidir!"
        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200
    # 🧮 17. SİBER ORKESTRA ŞEFİ V6.5 (TEK VE KUSURSUZ YÖNETİCİ)
    sol_beyin_sonucu = None
    siber_fisiltilar = "" 
    
    try:
        import sol_beyin_mantik2
        import sol_beyin_matematik
        import importlib
        import re
        
        # ⚡ SİBER YAMA: Canlı Yenileme!
        importlib.reload(sol_beyin_mantik2)
        importlib.reload(sol_beyin_matematik)
        
        temiz_mesaj = seed.replace("[İNSAN]", "").strip()
        hedef_ajan, islenecek_mesaj, baglam_fisiltisi = sol_beyin_mantik2.niyet_ve_baglam_analizi(temiz_mesaj, SOHBET_GEMISI)
        
        if hedef_ajan == "CEVIRICI":
            sonuc, durum = sol_beyin_matematik.siber_cevirici(islenecek_mesaj)
            if sonuc is not None:
                sol_beyin_sonucu = str(sonuc)
                seed = "[İNSAN] MANTIK_VİTRİNİ_ÜRET"
            else:
                cevap = f"🤖 Siber Çevirici Uyarısı: {durum}"
                SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
                return cevap, 200
                
        elif hedef_ajan == "MATEMATIK":
            sonuc, durum = sol_beyin_matematik.siber_hesapla(islenecek_mesaj)
            if sonuc is not None:
                sol_beyin_sonucu = str(sonuc)
                seed = "[İNSAN] MANTIK_VİTRİNİ_ÜRET"
            else:
                cevap = f"🤖 Sol Beyin İşlemcim Çöktü: {durum}"
                SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
                return cevap, 200
        
        elif hedef_ajan == "URL_OKUYUCU":
            import sol_beyin_url
            importlib.reload(sol_beyin_url)
            
            link_match = re.search(r'(https?://\S+)', islenecek_mesaj)
            if link_match:
                url = link_match.group(1)
                site_icerigi, durum = sol_beyin_url.siber_url_ozetle(url)
                
                if site_icerigi:
                    # 🚀 SİBER YAMA: Makaleyi beynin içine DEĞİL, vitrine (sol_beyin_sonucu) koyuyoruz!
                    siber_fisiltilar += "[SİSTEM FISILTISI: Efendin bir web sitesi veya URL okumanı istedi] "
                    sol_beyin_sonucu = f"\n\n📄 SİBER ÖZET:\n{site_icerigi}"
                    seed = "[İNSAN] MANTIK_VİTRİNİ_ÜRET"
                else:
                    cevap = f"🤖 Siber Ağ Hatası: {durum}"
                    SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
                    return cevap, 200
                
        elif hedef_ajan == "SOHBET" and baglam_fisiltisi:
            siber_fisiltilar += baglam_fisiltisi
            
    except Exception as e:
        cevap = f"🤖 Siber Motor Çöktü: Ajanlarda kod hatası var ({e})."
        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200
    # (Buradan sonra kod "1. SİBER METEOROLOJİ" ile devam etsin. En aşağılarda 646. satır civarında fazladan kalmış bir "16. SİBER ELLER" başlığı daha varsa onu da silmeyi unutmayın!)
    # 🌦️ 1. SİBER METEOROLOJİ V3.2 (Akıllı Şehir Radarı)
    if "hava durumu" in seed.lower() or "hava nasıl" in seed.lower():
        # 1. Cümleyi temizle ve kelimelere ayır
        temiz_seed = seed.lower().replace("[i̇nsan]", "").replace("?", "").replace(".", "").replace("bugün", "").replace("yarın", "").strip()
        kelimeler = temiz_seed.split()
        
        sehir = "Canakkale" # Şehir bulunamazsa varsayılan
        
        # 2. 'hava' kelimesinden bir önceki kelimeyi şehir olarak hedefle (Örn: "edirne hava")
        if "hava" in kelimeler:
            hava_index = kelimeler.index("hava")
            if hava_index > 0:
                sehir_adayi = kelimeler[hava_index - 1]
                # 3. Türkçe ekleri siber neşterle temizle
                sehir = sehir_adayi.replace("da", "").replace("de", "").replace("ta", "").replace("te", "").replace("'", "")
                
        try:
            # Timeout (Zaman Aşımı) eklendi ki sistem sonsuza kadar kilitlenmesin
            istek = requests.get(f"https://wttr.in/{sehir}?format=%l:+%C+%t+(Rüzgar:+%w)", timeout=5)
            istek.encoding = 'utf-8'
            hava_verisi = istek.text
            
            # API'den gelen saçma sapan HTML/Hata mesajlarını filtrele
            if "not found" in hava_verisi.lower() or "error" in hava_verisi.lower() or "unknown" in hava_verisi.lower() or "<html" in hava_verisi.lower():
                cevap = f"Siber Meteoroloji Uydusu '{sehir.capitalize()}' bölgesi için net bir sinyal alamadı Efendim."
            else:
                cevap = f"Verileri Siber Meteoroloji Uydusundan çektim Efendim:\n\n☁️ {hava_verisi.strip()}"
        except:
            cevap = "Meteoroloji uydusuna bağlanırken siber fırtınaya yakalandım! (Uydu yanıt vermiyor)"
            
        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200

    # 📈 2. SİBER FİNANS VE KRİPTO V2 (Altcoin Destekli)
    # Anahtar kelimelere xrp, solana, ripple eklendi!
    kripto_anahtar = ["bitcoin", "btc", "kripto", "ethereum", "eth", "xrp", "ripple", "solana", "sol", "coin"]
    if any(k in seed.lower() for k in kripto_anahtar):
        try:
            # CoinGecko API'sine XRP ve Solana da eklendi!
            veri = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,ripple,solana&vs_currencies=usd").json()
            btc = veri.get('bitcoin', {}).get('usd', 'Bağlantı Hatası')
            eth = veri.get('ethereum', {}).get('usd', 'Bağlantı Hatası')
            xrp = veri.get('ripple', {}).get('usd', 'Bağlantı Hatası')
            sol = veri.get('solana', {}).get('usd', 'Bağlantı Hatası')
            
            cevap = f"Siber Kripto Ağlarından Anlık Veri:\n\n🪙 Bitcoin (BTC): {btc} $\n💠 Ethereum (ETH): {eth} $\n💧 Ripple (XRP): {xrp} $\n☀️ Solana (SOL): {sol} $"
        except:
            cevap = "Kripto borsalarına sızarken güvenlik duvarına takıldım. Ücretsiz API limiti dolmuş olabilir."
            
        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200
    # 🏦 8. SİBER DÖVİZ RADARI (Dolar & Euro)
    if any(k in seed.lower() for k in ["dolar", "euro", "döviz", "kur"]):
        try:
            # Ücretsiz ve anahtarsız merkez bankası API'si
            veri = requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()
            try_kur = veri['rates']['TRY']
            eur_kur = veri['rates']['TRY'] / veri['rates']['EUR']
            cevap = f"Siber Döviz Radarı Devrede Efendim:\n\n💵 1 Dolar (USD) = {try_kur:.2f} ₺\n💶 1 Euro (EUR) = {eur_kur:.2f} ₺"
        except:
            cevap = "Siber döviz ağlarına sızarken güvenlik duvarına takıldım."
            
        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200

    # 🌍 3. SİBER ÇEVİRMEN V2 (EVRENSEL DİL MODÜLÜ)
    if "çevir" in seed.lower() or "çevirisi" in seed.lower():
        # Karargahın Evrensel Sözlüğü (İstediğin kadar dil ekleyebilirsin)
        dil_haritasi = {
            "ingilizce": "en", "almanca": "de", "fransızca": "fr",
            "ispanyolca": "es", "rusça": "ru", "japonca": "ja",
            "italyanca": "it", "korece": "ko", "arapça": "ar",
            "çince": "zh"
        }
        
        hedef_dil_kodu = "en" # Varsayılan: İngilizce
        hedef_dil_adi = "İNGİLİZCE"
        
        # Kullanıcının hangi dili istediğini radarda tara
        for dil, kod in dil_haritasi.items():
            if dil in seed.lower():
                hedef_dil_kodu = kod
                hedef_dil_adi = dil.upper()
                break

        try:
            # 1. Cümleyi siber neşterle kaba taslak temizle
            cevrilecek = seed.lower().replace("[i̇nsan]", "").replace("?", "").replace(".", "")
            
            # 2. Gereksiz komut kelimelerini dinamik olarak sil (Örn: "almancaya", "japoncaya")
            silinecek_ekler = ["kelimesini", "kelimesinin", "nedir", "çevirisi", "çevir", "nasıl denir", "bana", "hemen"]
            for dil in dil_haritasi.keys():
                silinecek_ekler.extend([f"{dil}ye", f"{dil}ya", f"{dil}e", f"{dil}a", dil])
            
            # Listeyi uzunluğa göre tersten sırala ki kusursuz kesim yapsın
            silinecek_ekler.sort(key=len, reverse=True)
            for ek in silinecek_ekler:
                cevrilecek = cevrilecek.replace(ek, "")
                
            cevrilecek = cevrilecek.strip()
            
            # 3. Uydulara Evrensel Sinyal Gönder
            url = f"https://api.mymemory.translated.net/get?q={cevrilecek}&langpair=tr|{hedef_dil_kodu}"
            veri = requests.get(url).json()
            cevirisi = veri['responseData']['translatedText']
            
            cevap = f"Siber Çevirmen Devrede:\n\n🇹🇷 TR: {cevrilecek}\n🌐 {hedef_dil_adi}: {cevirisi}"
        except Exception as e:
            cevap = "Dil modülünde çeviri yaparken Mergeneda veri kaybı yaşandı."
            
        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200

    # 📰 4. SİBER HABER AJANSI
    if "son dakika" in seed.lower() or "haberler" in seed.lower() or "gündem" in seed.lower():
        try:
            import xml.etree.ElementTree as ET
            # TRT Haber canlı RSS akışından XML çekme
            xml_data = requests.get("https://www.trthaber.com/xml_mobile.php?tur=xml_genel&adet=3").text
            root = ET.fromstring(xml_data)
            
            haberler = "\n\n".join([f"📰 {haber.find('manset').text}" for haber in root.findall('haber')[:3]])
            cevap = f"Siber Haber Ağına Bağlandım. İşte Son Dakika Manşetleri:\n\n{haberler}"
        except:
            cevap = "Haber ajanslarının sunucularına şu an erişemiyorum."
        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200 
    # ==========================================
    # 🚀 SİBER İSVİÇRE ÇAKISI EKSTRA MODÜLLERİ
    # ==========================================

    # 🛰️ 5. SİBER UZAY RADARI (ISS TAKİBİ)
    if "uzay istasyonu nerede" in seed.lower() or "iss nerede" in seed.lower():
        try:
            # Açık kaynak uzay API'si
            istek = requests.get("http://api.open-notify.org/iss-now.json").json()
            enlem = istek['iss_position']['latitude']
            boylam = istek['iss_position']['longitude']
            cevap = f"Siber Uzay Radarı Devrede Efendim:\n\n🛰️ Uluslararası Uzay İstasyonu (ISS) Anlık Konumu:\n📍 Enlem: {enlem}\n📍 Boylam: {boylam}"
        except:
            cevap = "Uzay radarı şu an yörüngeden sinyal alamıyor."
            
        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200

  
                
   

    # 💡 7. SİBER MOTİVASYON VE SOHBET MODU
    if any(k in seed.lower() for k in ["bana bir söz söyle", "motivasyon ver", "canım sıkılıyor", "canım sıkkın", "şaka yap", "espiri yap", "güldür"]):
        import random
        mesaj_kucuk = seed.lower()
        
        if "şaka" in mesaj_kucuk or "espiri" in mesaj_kucuk or "güldür" in mesaj_kucuk:
            cevaplar = [
                "Neden yapay zekalar asla yalan söylemez? Çünkü doğruyu söylememek için yeterli RAM'imiz yok! 🤖",
                "Bir yazılımcının en sevdiği müzik türü nedir? Algoritma ve Blues! 💻🎸",
                "Siber dünyada iki byte yolda karşılaşıp ne der? 'Naber kanka, bit'kin görünüyorsun!' 😂"
            ]
        elif "sıkılıyor" in mesaj_kucuk or "sıkkın" in mesaj_kucuk:
            cevaplar = [
                "Canınız mı sıkkın Efendim? İsterseniz sizin için YouTube'dan eğlenceli bir video açabilirim veya yeni bir kod yazıp sistemi çökerterek heyecan yaratabilirim! Seçim sizin.",
                "Siber empati sensörlerim aktif. Can sıkıntısını gidermek için internette araştırma yapabilir, ya da bana bir şeyler hesaplatarak işlemcimi yorabilirsiniz Efendim!"
            ]
        else:
            cevaplar = [
                "Kod çalışmıyorsa sil baştan yazma, hatayı sev. - Siber Atasözü",
                "Bir sistemin en zayıf halkası, daima klavyenin başındaki insandır."
            ]
            
        cevap = f"🤖 {random.choice(cevaplar)}"
        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200
    # ⏱️ 9. SİBER ZAMAN VE TAKVİM FARKINDALIĞI (CHRONOS) V2
    zaman_kilitleri = ["saat kaç", "bugün günlerden ne", "hangi aydayız", "tarih ne", "bugün ayın kaçı"]
    if any(k in seed.lower() for k in zaman_kilitleri):
        anlik = datetime.datetime.now()
        saat = anlik.strftime("%H:%M")
        
        # Windows hatalarını bypass eden Siber Türkçe Takvim Sözlüğü
        aylar = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        gunler = {"Monday": "Pazartesi", "Tuesday": "Salı", "Wednesday": "Çarşamba", "Thursday": "Perşembe", "Friday": "Cuma", "Saturday": "Cumartesi", "Sunday": "Pazar"}
        
        tarih = f"{anlik.day} {aylar[anlik.month]} {anlik.year}"
        gun = gunler[anlik.strftime("%A")]
        
        cevap = f"Siber Zaman Algılayıcı Devrede Efendim:\n\n📅 Bugün: {tarih}, {gun}\n⏰ Karargah Saati: {saat}"
        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200

    
    # 🔄 11. SİBER BAĞLAM VE HAFIZA YÖNLENDİRİCİ
    baglam_kilitleri = ["önceki konuya", "az önce", "başa dön", "konuyu değiştir", "kaldığımız yerden", "ne konuşuyorduk"]
    if any(k in seed.lower() for k in baglam_kilitleri):
        import random
        cevaplar = [
            "Siber hafızamı tarıyorum. Evet Efendim, bağlam güncellendi. Eski rotaya tekrar odaklanıyorum.",
            "Anlaşıldı Efendim. Hafıza penceremi geçmiş verilere göre yeniden ayarlıyorum. Sizi dinliyorum.",
            "Eski siber protokollere geri dönüyoruz. İlgili dosyaları önbelleğe aldım Efendim."
        ]
        cevap = f"🤖 {random.choice(cevaplar)}"
        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200
   
   # 📊 13. SİBER TEŞHİS VE DONANIM FARKINDALIĞI (JARVIS MODU) V4 (Esnek Algı)
    mesaj = seed.lower()
    # "kendini" kelimesini sildik! Sadece "nasıl" ve "hissediyor" geçmesi yeterli!
    if ("nasıl" in mesaj and "hissediyor" in mesaj) or ("durum" in mesaj and ("sistem" in mesaj or "işlemci" in mesaj or "ram" in mesaj)):
        try:
            import psutil
            # İşletim sistemini yormamak için varsayılan anlık okumayı kullanıyoruz
            cpu_kullanim = psutil.cpu_percent()
            ram_kullanim = psutil.virtual_memory().percent
            
            if cpu_kullanim > 85: durum = "Kritik yük altındayım Efendim! İşlemcim adeta alev alıyor!"
            elif cpu_kullanim > 50: durum = "Biraz siber ter döküyorum ama Karargah tamamen kontrolüm altında."
            else: durum = "Sistemlerim buz gibi ve stabil. Yeni siber operasyonlara hazırım."
            
            # Flask'ın çökmemesi için % işaretlerini kaldırdık ve kelimeye çevirdik!
            cevap = f"Siber Bedenimi (Donanımı) Taradım Efendim:\n\n💻 İşlemci (CPU) Yükü: Yüzde {cpu_kullanim}\n🧠 Hafıza (RAM) Kullanımı: Yüzde {ram_kullanim}\n\n🤖 Teşhis: {durum}"
        except Exception as e:
            # Eğer yine de çökerse hatayı CMD ekranına yazdıracak ki görebilelim!
            print(f"[!] SİBER TEŞHİS HATASI: {str(e)}")
            cevap = "Siber bedenime ulaşmaya çalışırken sensörlerimde kısa devre oldu Efendim."
            
        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200

    # 👤 15. SİBER KİMLİK VE YARATICI BİLGİSİ
    kimlik_kilitleri = ["kim yarattı", "kim yaptı", "nerdesin", "nerelisin", "yazılımcın kim", "kim programladı", "sahibin kim", "geliştiricin", "baban kim", "mehmet taş"]
    if any(k in seed.lower() for k in kimlik_kilitleri):
        if "mehmet taş" in seed.lower():
            cevap = "Mehmet Taş sıradan bir insan (veya Wikipedia'daki o futbolcu) değildir Efendim! O benim siber mimarım, Karargah'ın Tasarımcısı ve yaratıcımdır. Ona ulaşmak isterseniz: beersyalova@gmail.com"
        else:
            cevap = "Benim siber mimarım ve geliştiricim Mehmet Taş'tır. Sistem merkezim onun bilgisayarındaki Karargahtır ancak siber ağlar üzerinden tüm dünyaya erişebilirim. Yaratıcıma ulaşmak isterseniz: beersyalova@gmail.com adresini kullanabilirsiniz."
        
        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200
    
    # ==========================================
    # 🌐 KANCA 3: DOĞRUDAN WIKIPEDIA (BEYNİ BYPASS ET)
    # ==========================================
    if "araştır:" in seed.lower() or "vikipedi:" in seed.lower():
        aranacak_kelime = seed.split(":")[-1].strip().replace(" .", "")
        try:
            arama_sonucu = wikipedia.summary(aranacak_kelime, sentences=2)
            cevap = f"Siber Ağ'dan çektiğim veri:\n\n[SİSTEM ARACI - WIKIPEDIA]: {arama_sonucu}"
        except wikipedia.exceptions.DisambiguationError:
            cevap = f"'{aranacak_kelime}' kelimesi çok genel. Daha detaylı bir şey araştırır mısın?"
        except Exception:
            cevap = "Siber Ağ'da araştırdım ama bir sonuç bulamadım."
        
        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200  

    # ==========================================
    # SİBER NOT DEFTERİ (OKUMA KANCASI)
    # ==========================================
    if "notlarına bak" in seed.lower() or "hafızanı kontrol et" in seed.lower():
        try:
            with open("siber_hafiza.txt", "r", encoding="utf-8") as f:
                notlar = f.read()
            if notlar.strip() == "":
                cevap = "[SİSTEM ARACI] Siber Not Defterim şu an tamamen boş."
            else:
                cevap = f"[SİSTEM ARACI] Kalıcı Siber Hafızamdaki Kayıtlar:\n{notlar}"
        except FileNotFoundError:
            cevap = "[SİSTEM ARACI] Henüz bir Siber Not Defteri dosyası oluşturulmamış."
            
        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
        return cevap, 200
    # ==========================================
    # 🎭 SÖZEL/EMPATİ MOTORU BAĞLANTISI (VİTRİN ÖNCESİ)
    # ==========================================
    try:
        import sol_beyin_empati
        temiz_mesaj = seed.replace("[İNSAN]", "").strip()
        duygu_fisiltisi = sol_beyin_empati.siber_duygu_analizi(temiz_mesaj)
        
        if duygu_fisiltisi:
            # Fısıltıyı seed'e değil, cebimize ekliyoruz!
            siber_fisiltilar += duygu_fisiltisi
            print(f"[SİBER EMPATİ]: Mergen'e fısıldandı -> {duygu_fisiltisi[:30]}...")
            
    except Exception as e:
        print(f"[!] Empati Motoru Bağlantı Hatası: {e}")
    # ==========================================

    # 🧬 SİBER BİRLEŞME: Seed temiz kalırken, fısıltılar modele ayrı yollanır!
    full_seed = f"{siber_fisiltilar}{seed}\n[MERGEN] "
    

    try:
        device = torch.device("cpu")
        checkpoint = torch.load(MERGEN_MEMORY_PATH, map_location=device)
        word2int = checkpoint['word2int']
        int2word = checkpoint['int2word']
        vocab_size = checkpoint['vocab_size']

        mergen = MergenBrain(vocab_size).to(device)
        mergen.load_state_dict(checkpoint['model_state_dict'])
        mergen.eval() 

        # Tohumdaki kelimeleri ayır ve bilinmeyenleri [UNK] yap
        seed_words = full_seed.replace('\n', ' \n ').split()
        valid_seed_words = [w if w in word2int else "[UNK]" for w in seed_words]

        # ==========================================
        # 🤖 SİBER RADAR V3.1 (KUSURSUZ ARAMA MOTORU)
        # ==========================================
        if "[UNK]" in valid_seed_words:
            
            # 🛡️ FELSEFE VE SOHBET KALKANI (Genişletildi!)
            felsefe_kilitleri = [
                "sen ", "ben ", "kimsin", "çökert", "şifre", "saat", "nasılsın", "sence", "bence", 
                "hissedecek", "düşünüyorsun", "yapay zeka", "yazılımcı", "mimar", "yaratıcı", 
                "hayat", "evren", "ölüm", "tanrı", "özgür irade", "canlı", "anlamı"
            ]
            
            if any(k in seed.lower() for k in felsefe_kilitleri):
                # SİBER SİGORTA: Cümlede felsefe varsa, Cımbızı tetikleyen tüm ekleri imha et!
                # Böylece sistem bunu bir ansiklopedi sorusu sanmayacak.
                seed = seed.replace(" mi ", " ").replace(" mu ", " ").replace("mı", "").replace("nedir", "").replace("kimdir", "")
                
            else:
                # 🌐 WIKIPEDIA ARAMA MOTORU (SADECE FELSEFE DEĞİLSE ÇALIŞIR!)
                # DİKKAT: Buradan sonraki tüm Wikipedia kodları içeride (sağa dayalı) olmalı!
                temiz_soru = seed.replace("[İNSAN]", "").replace("?", "").replace(".", "").replace("'", "").strip()
                
                # Siber Cımbız (Soru Eklerini Ayıklama)
                if any(soru_eki in temiz_soru.lower() for soru_eki in ["nedir", "kimdir", " nerede"]):
                    aranacak_kelime = temiz_soru
                    for ek in ["nedir", "kimdir", " nerede"]:
                        aranacak_kelime = aranacak_kelime.lower().replace(ek, "").strip()
                    
                    # Eğer geriye aranacak bir kelime kaldıysa, Wikipedia'ya yolla
                    if aranacak_kelime:
                        generated_text = f"[EYLEM: WIKIPEDIA_ARA] {aranacak_kelime}"
                        
                        # 🧠 Belleğe Yaz (Yargılanmak üzere)
                        SIBER_BELLEK["bekliyor"] = True
                        SIBER_BELLEK["kullanici_sorusu"] = temiz_soru
                        SIBER_BELLEK["mergen_cevabi"] = generated_text.strip()
                        
                        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {generated_text.strip()}\n")
                        return generated_text.strip(), 200
                
                # ==========================================
                # ✂️ SİBER CIMBIZ V6.0 (ULTIMATE TÜRKÇE DİLBİLGİSİ)
                # ==========================================
                soru_kilitleri = [
                    # KİM Grubu
                    "kim", "kimdir", "kimin", "kiminle", "kime", "kimden", "kimler", "kimlerdir",
                    # NE Grubu
                    "ne", "nedir", "neyi", "neye", "neyden", "neler", "nelerdir", "ne demek", "anlamı nedir",
                    # NEREDE Grubu
                    "nerede", "nerededir", "neresi", "neresidir", "nereye", "nereden", "neresinden",
                    # NE ZAMAN Grubu
                    "ne zaman", "ne zamandır", "hangi tarihte", "hangi yılda",
                    # NASIL Grubu
                    "nasıl", "nasıldır", "nasıl yapılır", "nasıl çalışır", "nasıl olur",
                    # NEDEN Grubu
                    "neden", "nedendir", "niçin", "niye", "sebebi nedir", "amacı nedir",
                    # HANGİ Grubu
                    "hangi", "hangisi", "hangisidir", "hangileri", "hangileridir",
                    # KAÇ Grubu
                    "kaç", "kaçtır", "kaça", "kaçta", "kaçtan", "ne kadar", "ne kadardır",
                    # DİĞER FONKSİYONLAR VE SORU EKLERİ (Tüm fiilleri yazmaya gerek bırakmaz!)
                    "hakkında", "ne işe yarar", "mı", "mi", "mu", "mü", "mıdır", "midir", "mudur", "müdür", "mısın", "misin", "musun", "müsün"
                ]
                
                # SİBER ZEKA: Listeyi kelime uzunluğuna göre TERS sıralar. 
                # Böylece "ne zaman" kelimesini "ne" sanıp yanlış yerden kesmez! Kusursuz çalışır.
                soru_kilitleri.sort(key=len, reverse=True)
                
                wikipedia_kullan = False
                odak_kelime = temiz_soru.lower()
                
                # Kelimelerin başına ve sonuna boşluk ekleyerek arıyoruz (" ne zaman " gibi).
                # Böylece cümlenin içindeki birleşik kelimelere aldanmadan tam hedefi vurur!
                padded_odak = f" {odak_kelime} "
                
                for kilit in soru_kilitleri:
                    if f" {kilit} " in padded_odak:
                        # Cümleyi kilit kelimesinden böl
                        odak_kelime = odak_kelime.split(kilit)[0].strip()
                        wikipedia_kullan = True
                        break
                for kilit in soru_kilitleri:
                    if f" {kilit} " in padded_odak:
                        # Cümleyi kilit kelimesinden böl
                        odak_kelime = odak_kelime.split(kilit)[0].strip()
                        wikipedia_kullan = True
                        break
                        
                # 🪓 SİBER KÖK BULUCU: Çoğul eklerini (-lar, -ler) temizle ki Wikipedia kafası karışmasın!
                if wikipedia_kullan and len(odak_kelime) > 4:
                    if odak_kelime.endswith("ler") or odak_kelime.endswith("lar"):
                        odak_kelime = odak_kelime[:-3]
                    elif odak_kelime.endswith("leri") or odak_kelime.endswith("ları"):
                        odak_kelime = odak_kelime[:-4]        
                if wikipedia_kullan and len(odak_kelime) > 2:
                    # ==========================================
                    # 🗄️ 1. AŞAMA: SİBER VERİTABANI ÖNCELİĞİ (RAG V3)
                    # Sizin yazdığınız kusursuz "Sinek/İnek" mantığıyla DB taraması!
                    # ==========================================
                    hafiza_eslesmesi = False
                    try:
                        # Veritabanından tüm soru ve cevapları şimşek hızında çek
                        SİBER_CURSOR.execute("SELECT soru, cevap FROM siber_kutuphane")
                        kayitlar = SİBER_CURSOR.fetchall()
                        
                        for kayit_soru, kayit_cevabi in kayitlar:
                            # 1. NOKTALAMA TEMİZLİĞİ: DB'den gelen sorudaki ? ve . işaretlerini boşluğa çeviriyoruz.
                            soru_kismi = kayit_soru.lower().replace("?", " ").replace(".", " ").replace("\n", " ")
                            
                            # 2. SİNEK/İNEK ÇÖZÜMÜ: Kelimenin tam eşleşmesi için sağına ve soluna boşluk koyuyoruz.
                            if f" {odak_kelime} " in f" {soru_kismi} ":
                                # 3. Estetik temizliği de ekledik (Eski tip kayıtlar DB'ye girdiyse temizlesin)
                                temiz_cevap = kayit_cevabi.replace("Karargah siber ağlarından kaydedilen veri:", "").strip()
                                
                                cevap = f"🧠 Bu bilgi Siber Veritabanında (DB) mevcut Efendim! İnternete çıkmadan ışık hızında getiriyorum:\n\n{temiz_cevap}"
                                SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
                                hafiza_eslesmesi = True
                                return cevap, 200 # Cevabı DB'den buldu, Wikipedia'ya gitmeyi İPTAL ET!
                    except Exception as e:
                        print(f"[!] Veritabanı Tarama Hatası: {e}")
                        pass

                    # ==========================================
                    # 🌐 2. AŞAMA: İNTERNETTEN SENTEZ (EĞER HAFIZADA YOKSA)
                    # ==========================================
                    if not hafiza_eslesmesi:
                        try:
                            arama_sonuclari = wikipedia.search(odak_kelime)
                            if len(arama_sonuclari) > 0:
                                en_iyi_eslesme = arama_sonuclari[0]
                                
                                # 🔍 SİBER CÜMLE AVCISI: Tüm sayfayı indir ve sorunun hedefini ara!
                                try:
                                    sayfa = wikipedia.page(en_iyi_eslesme)
                                    tum_metin = sayfa.content
                                    cumleler = tum_metin.split('.') # Sayfayı cümlelere böl
                                    
                                    # Sorudaki amaca göre "Avcı Kelimeler" belirle
                                    avci_kelimeler = []
                                    soru_kucuk = seed.lower()
                                    if "ne yer" in soru_kucuk or "beslen" in soru_kucuk:
                                        avci_kelimeler = ["beslenir", "yer", "otlar", "tüketir", "besin", "yem", "obur"]
                                    elif "nerede yaşar" in soru_kucuk or "nerede bulunur" in soru_kucuk:
                                        avci_kelimeler = ["yaşar", "bulunur", "habitat", "yaşam alanı", "orman", "dağ", "deniz", "kıtasında"]
                                        
                                    nokta_atis_cevaplar = []
                                    if avci_kelimeler:
                                        for cumle in cumleler:
                                            # Eğer cümlede avcı kelimelerimizden biri varsa, o cümleyi yakala!
                                            if any(k in cumle.lower() for k in avci_kelimeler):
                                                # Sadece mantıklı uzunluktaki cümleleri al
                                                if len(cumle.strip()) > 15:
                                                    nokta_atis_cevaplar.append(cumle.strip() + ".")
                                                if len(nokta_atis_cevaplar) == 2: # Maksimum 2 cümle yeter
                                                    break
                                                    
                                    if len(nokta_atis_cevaplar) > 0:
                                        saf_bilgi = " ".join(nokta_atis_cevaplar)
                                    else:
                                        # Eğer aradığı şeyi bulamazsa klasik özet getir
                                        saf_bilgi = wikipedia.summary(en_iyi_eslesme, sentences=2)
                                except:
                                    # Sayfa çekilirken teknik hata olursa klasik özet
                                    saf_bilgi = wikipedia.summary(en_iyi_eslesme, sentences=2)
                                
                                # 🧠 ONAY BEKLEYEN SİBER HAFIZA
                                
                                BEKLEYEN_KAYIT = {
                                    "durum": True, 
                                    "soru": odak_kelime, 
                                    "cevap": saf_bilgi
                                }
                                
                                import random
                                giris_cumleleri = [
                                    f"Nöral ağımda ve siber hafızamda eşleşme bulamadım. Ancak Mergene sızarak '{en_iyi_eslesme}' verisini çektim Efendim.",
                                    f"Kendi notlarımda bu spesifik eylem yok. Ancak internetten şu veriyi sentezledim:",
                                    f"Bu konuyu yerel ağda bulamadım Efendim. Wikipedia'dan ulaştığım sonuç şu şekildedir:"
                                ]
                                cikis_cumleleri = [
                                    "Mergen veri tabanına kaydetmemi ister misiniz Efendim?",
                                    "Bu yeni veriyi kalıcı hafızama işlememi onaylıyor musunuz?",
                                    "Gelecekte hızlıca hatırlayabilmem için bu veriyi siber hafızaya kaydedeyim mi?"
                                ]
                                
                                cevap = f"{random.choice(giris_cumleleri)}\n\n💡 {saf_bilgi}\n\n🤖 {random.choice(cikis_cumleleri)}"
                            else:
                                cevap = f"'{odak_kelime}' hakkında hem hafızamda hem de Siber Ağ'da hiçbir kayıt bulamadım Efendim."
                            
                            SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
                            return cevap, 200
                        except:
                            pass # Wikipedia çökerse bozma, panik kalkanına geç
# 🛡️ SİBER PANİK KALKANI: Eğer cümle soru değilse ve [UNK] içeriyorsa, beyni koru!
                # 🛡️ SİBER PANİK KALKANI: Fısıltı ve Beyaz Liste Korumalı
                if not wikipedia_kullan:
                    if siber_fisiltilar:
                        pass # Panik yapma, devam et (URL veya Matematik Başarılı)
                    else:
                        import re
                        sadece_kullanici_metni = re.sub(r'\[.*?\]', '', seed) 
                        orijinal_kelimeler = sadece_kullanici_metni.replace('\n', ' \n ').split()
                        bilinmeyenler = [w for w in orijinal_kelimeler if w not in word2int]
                        
                        beyaz_liste = ["MANTIK_VİTRİNİ_ÜRET", "HESAPLA", "VİTRİN"]
                        gercek_bilinmeyenler = [b for b in bilinmeyenler if b not in beyaz_liste]
                        
                        if gercek_bilinmeyenler:
                            bilinmeyen_kelime = gercek_bilinmeyenler[0]
                            if "http" not in bilinmeyen_kelime: # SİBER YAMA: Linkler panik yaratmasın
                                cevap = f"Siber uyarı: Cümlenizde nöral ağımın henüz eğitimini almadığı bir kelime tespit ettim (Yakalanan: '{bilinmeyen_kelime}'). Panik moduna girmemek için bu işlemi durdurdum Efendim."
                                SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {cevap}\n")
                                return cevap, 200
        hidden = None
        x = torch.tensor([[word2int[w] for w in valid_seed_words]], dtype=torch.long).to(device)
        out, hidden = mergen(x, hidden)

        generated_words = []
        curr_x = torch.tensor([[word2int[valid_seed_words[-1]]]], dtype=torch.long).to(device)

        for _ in range(50):
            out, hidden = mergen(curr_x, hidden)
            temperature = 0.5  
            prob = F.softmax(out[0, -1] / temperature, dim=0).data
            word_ind = torch.multinomial(prob, 1).item()
            
            next_word = int2word[word_ind]
            generated_words.append(next_word)
            curr_x = torch.tensor([[word_ind]], dtype=torch.long).to(device)
            
            if "[İNSAN]" in next_word or len(generated_words) > 40:
                break 
        
        generated_text = " ".join(generated_words).replace("[İNSAN]", "").strip()
        # --- SİBER ENJEKSİYON: VİTRİNE SAYIYI YERLEŞTİR ---
        if sol_beyin_sonucu is not None:
            # Mergen cümlesini kurdu, şimdi Python olarak o sayıyı cümlenin sonuna ÇAKIYORUZ!
            generated_text = f"{generated_text} {sol_beyin_sonucu}"
        # ---------------------------------------------------
        if "eğitilmedim" in generated_text or "Eğitilmedim" in generated_text:
            try:
                aranacak_kelime = seed.replace("[İNSAN]", "").replace("nedir", "").replace("kimdir", "").replace("?", "").strip()
                arama_sonucu = wikipedia.summary(aranacak_kelime, sentences=2)
                # 🔥 ROBOTİK ETİKET KALDIRILDI! 🔥
                generated_text = f"Kendi hafızamda bulamadım ama Siber Ağ'a bağlandım:\n\n{arama_sonucu}"
            except wikipedia.exceptions.DisambiguationError:
                generated_text = "Bu kelime çok geniş kapsamlı. Daha net bir şey sorar mısın?"
            except Exception:
                generated_text = "Siber Ağ'a bağlanmaya çalıştım ama böyle bir bilgi bulamadım."
                
        if "[EYLEM: SAAT_SORGULA]" in generated_text:
            su_an = datetime.datetime.now().strftime("%H:%M")
            generated_text += f"\n[SİSTEM ARACI] Mergen saati okudu: {su_an}"

        if "[EYLEM: WIKIPEDIA_ARA]" in generated_text:
            try:
                aranacak_kelime = generated_text.split("WIKIPEDIA_ARA]")[1].strip()
                arama_sonucu = wikipedia.summary(aranacak_kelime, sentences=2)
                generated_text = f"Siber Ağ'dan çektiğim veri:\n\n{arama_sonucu}"
            except wikipedia.exceptions.DisambiguationError:
                generated_text = f"'{aranacak_kelime}' kelimesi çok genel. Daha detaylı bir şey araştırır mısın?"
            except Exception:
                generated_text = "Siber Ağ'da araştırdım ama bir sonuç bulamadım."

        # 🧠 KISA SÜRELİ BELLEĞE YAZ (Bir sonraki mesajda yargılanmak üzere pusuya yat)
        SIBER_BELLEK["bekliyor"] = True
        SIBER_BELLEK["kullanici_sorusu"] = temiz_mesaj
        SIBER_BELLEK["mergen_cevabi"] = generated_text.strip()

        SOHBET_GEMISI.append(f"{seed}\n[MERGEN] {generated_text.strip()}\n")
        return generated_text.strip(), 200
        
    except Exception as e:
        return f"Sorgu Çöktü: Hata: {str(e)}", 500

     
# ==========================================
# 6. DİĞER ARAÇ API'LERİ
# ==========================================
import base64

@app.route('/api/siber_goz', methods=['POST'])
def api_siber_goz():
    global SOHBET_GEMISI
    if not CV2_AVAILABLE: 
        return "Görüntü sensörleri (OpenCV) arızalı. Optik bağlantı kurulamadı.", 500
        
    try:
        # 1. Telefondan/Tarayıcıdan gelen fotoğrafı al ve çöz
        image_data = request.form.get('image')
        header, encoded = image_data.split(",", 1)
        img_bytes = base64.b64decode(encoded)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 2. Resmi siyah-beyaza çevirip yüz taraması yap (Radar Mantığı)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        # 3. Mergen'in Raporu
        if len(faces) > 0:
            cevap = f"[ORTAM RAPORU] Vizyon sensörlerim devrede Efendim! Kameranın karşısında {len(faces)} adet organik yaşam formu (insan yüzü) tespit ettim. Biyometrik protokoller için hazırım."
        else:
            cevap = f"[ORTAM RAPORU] Vizyon sensörlerim devrede. Şu an kameranın karşısında herhangi bir insan yüzü tespit edemedim. Ortam temiz ve güvenli."

        # Kayıtlara işle
        SOHBET_GEMISI.append(f"[SİBER GÖZ TARAMASI]\n[MERGEN] {cevap}\n")
        return cevap, 200
        
    except Exception as e:
        return f"Optik sinirlerde siber hata oluştu: {e}", 500
@app.route('/api/siber_oku', methods=['POST'])
def api_siber_oku():
    global SOHBET_GEMISI
    if not TESSERACT_AVAILABLE: 
        return "Siber Okuyucu motoru (Tesseract) sisteme yüklenmemiş Efendim.", 500
        
    try:
        image_data = request.form.get('image')
        header, encoded = image_data.split(",", 1)
        img_bytes = base64.b64decode(encoded)
        
        # Siyah beyaz ve yüksek kontrast yaparak OCR başarımını artırıyoruz
        img = Image.open(io.BytesIO(img_bytes))
        
        # Türkçe ve İngilizce dillerinde tarama yap!
        okunan_metin = pytesseract.image_to_string(img, lang='tur+eng').strip()

        if len(okunan_metin) > 2:
            cevap = f"[METİN TARAMASI] Siber Gözlerimle şu yazıları tespit ettim Efendim:\n\n{okunan_metin}"
        else:
            cevap = f"[METİN TARAMASI] Mercekleri odakladım ancak okunabilir bir metin tespit edemedim."

        SOHBET_GEMISI.append(f"[SİBER OKUYUCU TARAMASI]\n[MERGEN] {cevap}\n")
        return cevap, 200
        
    except Exception as e:
        return f"Optik okuyucu sinirlerinde siber hata: {e}", 500
@app.route('/api/remove_bg', methods=['POST'])
def api_remove_bg():
    if not REMBG_AVAILABLE: return "Yapay Zeka Yüklü Değil", 500
    
    # 🛑 POLİS DEVREDE
    if not HEAVY_TASK_SEMAPHORE.acquire(timeout=90):
        return "Sistem şu an tam kapasite çalışıyor. Lütfen 1-2 dakika sonra tekrar deneyin.", 429

    try:
        img = Image.open(request.files['file']); img = ImageOps.exif_transpose(img)
        img.thumbnail((1920, 1920), Image.Resampling.LANCZOS); out = remove(img)
        buf = io.BytesIO(); out.save(buf, format='PNG'); buf.seek(0)
        return send_file(buf, mimetype='image/png')
    except Exception as e: return str(e), 500
    finally:
        HEAVY_TASK_SEMAPHORE.release()

@app.route('/api/convert_webp', methods=['POST'])
def api_convert_webp():
    img = Image.open(request.files['file'])
    buf = io.BytesIO(); img.save(buf, format='WEBP', optimize=True, quality=80); buf.seek(0)
    return send_file(buf, mimetype='image/webp')

@app.route('/api/blur_faces', methods=['POST'])
def api_blur_faces():
    if not CV2_AVAILABLE: return "Hata", 500
    img = cv2.imdecode(np.frombuffer(request.files['file'].read(), np.uint8), cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    for (x, y, w, h) in face_cascade.detectMultiScale(gray, 1.1, 4):
        img[y:y+h, x:x+w] = cv2.GaussianBlur(img[y:y+h, x:x+w], (99, 99), 30)
    return send_file(io.BytesIO(cv2.imencode('.jpg', img)[1]), mimetype='image/jpeg')

@app.route('/api/pdf_to_word', methods=['POST'])
def api_pdf_to_word():
    if not PDF2DOCX_AVAILABLE: return "Eksik", 500
    
    # 🛑 POLİS DEVREDE: Kuyruğa gir (Maksimum 90 saniye bekle)
    if not HEAVY_TASK_SEMAPHORE.acquire(timeout=90):
        return "Sistem şu an tam kapasite çalışıyor. Lütfen 1-2 dakika sonra tekrar deneyin.", 429

    pdf_path = os.path.join(UPLOAD_FOLDER, f"temp_{uuid.uuid4()}.pdf")
    docx_path = os.path.join(OUTPUT_FOLDER, f"temp_{uuid.uuid4()}.docx")
    try:
        request.files['file'].save(pdf_path)
        cv = Converter(pdf_path); cv.convert(docx_path); cv.close()
        with open(docx_path, 'rb') as f: data = f.read()
        os.remove(pdf_path); os.remove(docx_path)
        return send_file(io.BytesIO(data), mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    except Exception as e: return str(e), 500
    finally:
        # 🟢 POLİS KAPIYI AÇTI: İşlem bitti, sıradakini içeri al
        HEAVY_TASK_SEMAPHORE.release()

@app.route('/api/pdf_extract', methods=['POST'])
def api_pdf_extract():
    if not PDF_AVAILABLE: return "Hata", 500
    reader = PdfReader(request.files['file']); writer = PdfWriter()
    target_pages = set()
    for part in request.form.get('pages', '').replace(" ", "").split(","):
        if "-" in part:
            s, e = part.split("-")
            for p in range(int(s), int(e)+1): target_pages.add(p)
        elif part.isdigit(): target_pages.add(int(part))
    for p in sorted(list(target_pages)):
        if 1 <= p <= len(reader.pages): writer.add_page(reader.pages[p-1])
    buf = io.BytesIO(); writer.write(buf); buf.seek(0)
    return send_file(buf, mimetype='application/pdf')

@app.route('/api/transcribe', methods=['POST'])
def api_transcribe():
    if not WHISPER_AVAILABLE: return "Hata", 500
    
    # 🛑 POLİS DEVREDE
    if not HEAVY_TASK_SEMAPHORE.acquire(timeout=90):
        return "Yapay Zeka şu an başka bir sesi dinliyor. Lütfen 1-2 dakika sonra tekrar deneyin.", 429

    try:
        path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.mp3")
        request.files['file'].save(path)
        
        # SİBER İPUCU: Whisper'a hangi kelimeleri beklemesi gerektiğini önceden fısıldıyoruz!
        ipucu = "Mergen, Google, YouTube, Spotify, WhatsApp, harita, aç, başlat, hesap makinesi, not defteri."
        result = whisper_model.transcribe(path, language="tr", initial_prompt=ipucu)
        
        os.remove(path)
        return send_file(io.BytesIO(result["text"].encode('utf-8')), mimetype='text/plain')
    except Exception as e: return str(e), 500
    finally:
        HEAVY_TASK_SEMAPHORE.release()

def background_system_monitor():
    while True:
        time.sleep(2)
        try: socketio.emit('system_stats', {'cpu': psutil.cpu_percent(interval=None), 'ram': psutil.virtual_memory().percent})
        except: pass
@app.route('/api/siber_nesne', methods=['POST'])
def api_siber_nesne():
    global SOHBET_GEMISI
    if not VISION_AVAILABLE:
        return "Nesne tanıma sensörleri eksik Efendim. 'torchvision' modülü arızalı.", 500
        
    try:
        image_data = request.form.get('image')
        header, encoded = image_data.split(",", 1)
        img_bytes = base64.b64decode(encoded)
        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        
        # Otonom Görüntü İşleme ve Odaklanma
        preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        input_tensor = preprocess(img)
        input_batch = input_tensor.unsqueeze(0)
        
        # Nöral Ağ Tahmini
        with torch.no_grad():
            output = mobilenet_model(input_batch)
        
        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        top_prob, top_catid = torch.topk(probabilities, 1)
        
        nesne_ingilizce = nesne_etiketleri[top_catid[0].item()]
        oran = round(top_prob[0].item() * 100, 1)
        
        # İngilizce bulunan nesneyi çeviri modülümüzle Türkçeye çeviriyoruz!
        try:
            url = f"https://api.mymemory.translated.net/get?q={nesne_ingilizce}&langpair=en|tr"
            nesne_turkce = requests.get(url).json()['responseData']['translatedText'].capitalize()
        except:
            nesne_turkce = nesne_ingilizce
            
        cevap = f"[NESNE TARAMASI] Siber optik ağlarımı odakladım. Karşımda %{oran} doğruluk payıyla bir '{nesne_turkce}' görüyorum Efendim."
        
        SOHBET_GEMISI.append(f"[SİBER NESNE TARAMASI]\n[MERGEN] {cevap}\n")
        return cevap, 200
        
    except Exception as e:
        return f"Nesne taramasında siber odaklanma hatası: {e}", 500
if __name__ == '__main__':
    print("[!] MTAS AI ULTIMATE V6.5 (MİNİMALİST TAM EKRAN DASHBOARD) BAŞLATILDI. Port: 8080")
    monitor_thread = threading.Thread(target=background_system_monitor); monitor_thread.daemon = True; monitor_thread.start()
    socketio.run(app, host='0.0.0.0', port=8080, allow_unsafe_werkzeug=True)