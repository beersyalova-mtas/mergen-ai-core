from flask import Flask, request, jsonify, render_template_string
import os
import datetime
import requests

app = Flask(__name__)
LOG_FILE = "ziyaretci.txt"

# Eğer dosya yoksa ilk açılışta oluştur
if not os.path.exists(LOG_FILE):
    open(LOG_FILE, 'w', encoding='utf-8').close()

def konum_bul(ip):
    if ip == "127.0.0.1" or ip.startswith("192.168"):
        return "Karargah (Yerel Ağ)"
    try:
        # IP adresinden ülke, şehir ve internet sağlayıcı bilgisini çeker
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=country,city,isp", timeout=2).json()
        if res.get("status") == "fail": return "Bilinmeyen Sinyal"
        return f"{res.get('country', '')}, {res.get('city', '')} ({res.get('isp', '')})"
    except:
        return "Uydu Bağlantısı Koptu"

@app.route('/log', methods=['POST'])
def log_visitor():
    data = request.json
    ip = data.get('ip', 'Bilinmiyor')
    os_adi = data.get('os', 'Bilinmiyor')
    tarayici = data.get('browser', 'Bilinmiyor')
    
    konum = konum_bul(ip)
    zaman = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 📝 Arka planda txt dosyasına yaz (Kalıcı Kayıt)
    log_satiri = f"[{zaman}] | IP: {ip} | KONUM: {konum} | CİHAZ: {os_adi.capitalize()} | TARAYICI: {tarayici.capitalize()}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_satiri)
        
    return jsonify({"status": "ok"})

@app.route('/api/get_logs')
def get_logs():
    # Canlı radara verileri tersten (en yeni en üstte) gönder
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        satirlar = f.readlines()
    return jsonify({"logs": satirlar[::-1]})

# ==========================================
# 🌐 SİBER GÖZETLEME EKRANI (HTML/CSS)
# ==========================================
RADAR_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>👁️ MERGEN SİBER RADAR</title>
    <style>
        body { background-color: #09090b; color: #10b981; font-family: 'Courier New', monospace; margin: 0; padding: 20px; }
        h1 { color: #8b5cf6; text-shadow: 0 0 10px #8b5cf6; text-align: center; border-bottom: 1px solid #27272a; padding-bottom: 20px; }
        .stat-box { text-align: center; font-size: 18px; margin-bottom: 20px; color: #f4f4f5; }
        .blink { animation: blinker 1.5s linear infinite; color: #ef4444; font-weight: bold; }
        @keyframes blinker { 50% { opacity: 0; } }
        
        table { width: 100%; border-collapse: collapse; margin-top: 20px; background: rgba(16, 185, 129, 0.05); }
        th { background-color: #18181b; color: #8b5cf6; padding: 15px; border: 1px solid #27272a; text-align: left; }
        td { padding: 12px; border: 1px solid #27272a; color: #d4d4d8; }
        tr:nth-child(even) { background-color: rgba(255, 255, 255, 0.02); }
        tr:hover { background-color: rgba(16, 185, 129, 0.1); }
        
        .zaman { color: #3b82f6; }
        .ip { color: #ef4444; font-weight: bold; }
        .konum { color: #eab308; }
    </style>
</head>
<body>
    <h1>👁️ MERGEN SİBER GÖZETLEME KULESİ</h1>
    <div class="stat-box">
        <span class="blink">● CANLI İZLEME AKTİF</span> | Toplam Siber Temas: <span id="toplam-temas" style="color:#10b981; font-weight:bold;">0</span>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>ZAMAN</th>
                <th>IP ADRESİ</th>
                <th>KONUM & İNTERNET SAĞLAYICI</th>
                <th>CİHAZ / İŞLETİM SİSTEMİ</th>
                <th>TARAYICI</th>
            </tr>
        </thead>
        <tbody id="radar-body">
            </tbody>
    </table>

    <script>
        function verileriCek() {
            fetch('/api/get_logs')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('radar-body');
                    tbody.innerHTML = ''; // Tabloyu temizle
                    document.getElementById('toplam-temas').innerText = data.logs.length;
                    
                    data.logs.forEach(log => {
                        if(log.trim() === "") return;
                        
                        // Örnek Log: [2026-04-25 12:00:00] | IP: 1.1.1.1 | KONUM: TR | CİHAZ: Windows | TARAYICI: Chrome
                        let parcalar = log.split(' | ');
                        let zaman = parcalar[0].replace('[', '').replace(']', '');
                        let ip = parcalar[1].replace('IP: ', '');
                        let konum = parcalar[2].replace('KONUM: ', '');
                        let cihaz = parcalar[3].replace('CİHAZ: ', '');
                        let tarayici = parcalar[4].replace('TARAYICI: ', '');

                        let tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td class="zaman">${zaman}</td>
                            <td class="ip">${ip}</td>
                            <td class="konum">${konum}</td>
                            <td>${cihaz}</td>
                            <td>${tarayici}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                });
        }

        // Radarı her 3 saniyede bir sayfayı yenilemeden sessizce güncelle!
        setInterval(verileriCek, 3000);
        verileriCek(); // İlk açılışta hemen çek
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(RADAR_HTML)

if __name__ == '__main__':
    print("[!] SİBER RADAR BAŞLATILDI. http://127.0.0.1:8081 adresinden izleyebilirsiniz.")
    # Radarımız 8081 portunda çalışacak ki ana Mergen (8080) ile çakışmasın!
    app.run(host='0.0.0.0', port=8081)