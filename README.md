# Prediksi Rute Terbaik Kendaraan dengan AI

Sistem prediksi rute terbaik untuk kendaraan di Bali menggunakan AI yang mempertimbangkan lalu lintas, kondisi cuaca, dan faktor lingkungan lainnya.

## Fitur Utama

- **Real Road Routing** - Rute di jalan asli lewat OSRM (Open Source Routing Machine), dengan fallback ke OSMnx & garis lurus
- **Multi-Stop Routing** - Dukungan titik singgah/waypoint berurutan untuk pengiriman & antar-jemput
- **Rute Alternatif + Skoring** - Bandingkan hingga 3 rute alternatif (yang disintesis dari detour) dan pilih terbaik
- **Traffic Prediction** - Prediksi kepadatan lalu lintas berdasarkan waktu dan lokasi
- **Traffic-Colored Map** - Segmen rute diwarnai per tingkat kepadatan (lancar/normal/padat/macet) pada peta interaktif
- **Real Traffic Data** - Integrasi TomTom Traffic Flow API bila `TOMTOM_API_KEY` diisi, fallback simulasi bila tidak
- **Weather Integration** - Integrasi data cuaca untuk penyesuaian rute
- **Interactive Map** - Peta interaktif Leaflet langsung di halaman utama (bukan iframe): klik peta untuk menempatkan titik, marker bisa digeser (drag), live update
- **Turn-by-Turn Navigation** - Panduan arah per belokan (OSRM steps) dalam Bahasa Indonesia, ikon manuver, jarak per langkah
- **Panduan Otomatis A-Z (ala Google Maps)** - Setelah rute diprediksi, bar panduan sticky muncul di peta memberi arahan belokan demi belokan (`N / total`), diberi suara jika navigasi suara aktif, maju otomatis/lewat tombol "⚡ Langkah berikut", berhenti dengan "⏹ Selesai"
- **Waktu Tiba** - Panel hasil & bar panduan menampilkan perkiraan jam tiba (diperbarui tiap auto-refresh 45 detik)
- **Perbandingan Rute** - Tabel banding rute terbaik vs alternatif (jarak, waktu, lalu lintas, skor) + rincian per leg/segmen
- **Pencarian Tempat (Autocomplete)** - Cari lokasi di Bali via Nominatim dengan saran instan
- **Layer Peta** - Ganti tampilan: Jalan (OSM/Carto), Satelit (Esri), Medan (OpenTopoMap)
- **Overlay Lalu Lintas** - Lapisan "Traffic" ala Google Maps (grid kepadatan berwarna) yang bisa dinyalakan/dimatikan
- **Ekspor & Berbagi Rute** - Unduh GPX/KML, salin tautan rute (URL berisi titik, auto-prediksi saat dibuka)
- **119 Lokasi Ikonik Bali** - POI kurasi (pura, pantai, air terjun, gunung & danau, kuliner, dll) dengan layer peta per kategori + saran autocomplete (digabung dengan Nominatim). Endpoint: `/pois`, `/pois/categories`, `/pois/near`, `/pois/{id}`
- **Profil Kendaraan** - Pilih mode kendaraan: 🚗 Mobil, 🏍 Motor, 🚶 Jalan Kaki (waktu ETA & kecepatan disesuaikan otomatis)
- **Realtime Tracking Live (SSE)** - Mulai tracking perjalanan, perangkat bergerak di peta dengan progress, ETA tersisa & kecepatan live; bagikan tautan `/?track=<id>` agar orang lain ikut memantau
- **Navigasi ala Google Maps** - Panduan turn-by-turn otomatis menyala di rute: posisi 🚗 bergerak live di peta sepanjang rute, langkah berikutnya maju sesuai jarak yang sudah ditempuh (bukan timer), sisa ETA, waktu tiba & sisa jarak ditampilkan, chip 🚦 lalu lintas di posisi kendaraan diperbarui tiap 15 detik, progress bar visual, suara per belokan, dan animasi hubungi saat tiba di tujuan
- **Navigasi Suara Bahasa Indonesia** - Panduan arah dibacakan via SpeechSynthesis (`id-ID`), toggle on/off
- **Auto-Refresh Lalu Lintas & ETA** - Rute di-refresh otomatis tiap 45 detik (segmen traffic + ETA terbaru tanpa merekam riwayat)
- **Rute Favorit & Riwayat Terakhir** - Simpan rute dengan nama, muat ulang sekali klik; 5 perjalanan terakhir ditampilkan di panel
- **Lapor Hambatan Crowdsourced** - Laporkan macet/banjir/tutup jalan langsung dari peta; insiden memengaruhi skor & ETA rute pengguna lain; marker insiden sebar ke peta (TTL 2 jam)
- **Tombol Lokasi GPS Saya** - Isi otomatis titik awal dengan lokasi perangkat saat ini
- **Tracking Live Sekali Klik** - Tombol "🔴 Mulai Tracking Saya (live)" langsung di panel hasil; posisi kendaraan bergerak di peta + ETA tersisa terupdate, dengan tautan berbagi. `Enter` pada kolom asal/tujuan langsung memprediksi rute
- **Riwayat Trip** - Setiap prediksi tersimpan ke SQLite, dapat di-retrain model dengan data nyata
- **ML Models** - Model machine learning untuk prediksi dan scoring
 - **AI Real-time Engine (ML Terawasi)** - Model travel-time dilatih dari `trip_history` nyata dan diblend dengan estimasi heuristik (`blend_weight` naik seiring jumlah sampel). Status model & blend tampil live di UI (kartu "🤖 AI Real-time Engine")
 - **Antigravity / Gemini ETA** - Saat `GEMINI_API_KEY` diisi, estimasi waktu tempuh rute terbaik & denyut SSE juga diblend dengan prediksi Gemini (keluarga Antigravity, default `gemini-2.5-flash`) sebesar `gemini_eta_weight`. Tanpa API key, aplikasi tetap berfungsi penuh dengan model lokal (degradasi tenang)
- **Auto-Retrain Background** - Deteksi otomatis saat sampel riwayat ≥ `auto_retrain_threshold` lalu retrain semua model di background (thread) tanpa blokir request
- **Traffic ML Blend** - Prediksi kepadatan menggabungkan + faktor model traffic dengan simulasi heuristik bila API TomTom tak tersedia
- **Realtime Feed (SSE)** - Stream insiden baru, denyut traffic, & ETA rute aktif ke browser secara live (`/realtime/incidents`, `/realtime/traffic`, `/realtime/route`); insiden baru muncul sebagai toast di UI, ETA/waktu tiba/lalu lintas rute diperbarui otomatis tanpa re-routing (traffic+insiden+blend AI dihitung ulang per denyut)
- **Pratinjau Lalu Lintas per Jam** - Slider jam (0-23) di peta menampilkan prediksi kepadatan grid per jam dari `/traffic/hourly`
- **Konfigurasi Dapat Disesuaikan** - Settings realtime/AI (interval stream, threshold auto-retrain, min sampel ML, TTL insiden, bounds cakupan) di `config.py` dan terekspos `GET /config/public` (badge mode data ditampilkan di UI)
- **Docker Deployment** - Dockerfile + docker-compose untuk produksi

## Tech Stack

- **Backend**: FastAPI, Python 3.10+
- **AI/ML**: scikit-learn, XGBoost
- **Peta**: OSMnx, NetworkX, Folium
- **Database**: SQLite

## Instalasi

### 1. Clone Repository

```bash
git clone <repository-url>
cd route-prediction
```

### 2. Buat Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

```bash
cp .env.example .env
# Edit .env dan tambahkan API key OpenWeatherMap
# Opsional: GEMINI_API_KEY=<key dari aistudio.google.com> untuk blend ETA Antigravity/Gemini
# GEMINI_MODEL=gemini-2.5-flash   # (default) model Gemini untuk estimasi ETA
```

### 5. Jalankan Aplikasi

```bash
./start.sh            # instal dependensi otomatis (sekali) lalu jalankan di :9000
# atau manual:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Variabel env: `PORT` (default 9000), `HOST`, `RELOAD=1` untuk auto-reload saat pengembangan. `./start.sh` juga membuat `.env` dari `.env.example` bila belum ada.

Aplikasi akan berjalan di http://localhost:9000

Model ML yang sudah dilatih (travel-time AI, traffic, route scorer) **disimpan otomatis ke disk** dan langsung dimuat ulang saat server dinyalakan — AI sudah aktif tanpa perlu retrain manual setelah restart.

Routing menggunakan OSRM public server (https://router.project-osrm.org) secara default. Untuk memakai server OSRM sendiri, atur `OSRM_BASE_URL` di `.env`. Jika OSRM tidak tersedia, sistem otomatis fallback ke graph OSMnx lokal atau garis lurus.

Traffic menggunakan **TomTom Traffic Flow API** secara otomatis jika `TOMTOM_API_KEY` diisi (lihat `.env.example`). Tanpa API key, sistem memakai simulasi kepadatan berbasis pola jam kerja & jarak ke pusat Denpasar. Cuaca memakai OpenWeatherMap bila `OPENWEATHERMAP_API_KEY` ada, selain itu data mock.

> Catatan: Memuat peta OSMnx bersifat opsional dan lambat (unduh dari internet). Gunakan `POST /api/v1/map/load` jika ingin mengaktifkannya sebagai fallback routing.

### Deployment dengan Docker

```bash
docker compose up --build -d
```

Aplikasi berjalan di http://localhost:9000. Gunakan `docker compose logs -f route-api` untuk melihat log.

## API Endpoints

### Prediksi Rute

```http
POST /api/v1/route/predict
Content-Type: application/json

{
  "origin": {"lat": -8.6500, "lng": 115.2167},
  "destination": {"lat": -8.3405, "lng": 115.0920},
  "waypoints": [{"lat": -8.7930, "lng": 115.2280}],
  "preferences": {
    "avoid_tolls": false,
    "avoid_highways": false,
    "priority": "time",
    "mode": "motorcycle"
  }
}
```

### Visualisasi Rute (dengan waypoint)

```http
GET /api/v1/route/visualize?origin_lat=-8.6500&origin_lng=115.2167&dest_lat=-8.3405&dest_lng=115.0920&waypoints=-8.7930,115.2280
```

### Data Rute untuk Peta Live (JSON, GeoJSON-style)

```http
GET /api/v1/route/geometry?origin_lat=-8.6500&origin_lng=115.2167&dest_lat=-8.3405&dest_lng=115.0920&waypoints=-8.5000,115.1500&mode=car&priority=time
```

Mengembalikan `best` + `alternatives` (koordinat, jarak, waktu, skor, **instruksi turn-by-turn**, **rincian per leg**), `traffic_segments` (warna per segmen), dan `weather_summary`. Parameter `mode` (car|motorcycle|walking) & `priority` opsional.

### Pencarian Tempat (Autocomplete)

```http
GET /api/v1/places/search?q=Pura Luhur Uluwatu&limit=5
```

Pencarian terbatas di area Bali via OpenStreetMap Nominatim.

### Overlay Lalu Lintas (Grid Kepadatan)

```http
GET /api/v1/traffic/overlay?lat=-8.6500&lng=115.2193&grid=11&radius_km=15
```

Mengembalikan grid titik dengan tingkat kepadatan untuk lapisan "Traffic" ala Google Maps.

### Riwayat & Retrain Model

```http
GET /api/v1/history             # Daftar prediksi tersimpan
GET /api/v1/history/stats       # Statistik agregat
GET /api/v1/history/last?limit=5  # Perjalanan terakhir (untuk UI "Riwayat Terakhir")
POST /api/v1/models/retrain     # Retrain ML dengan riwayat nyata
```

### Lokasi Ikonik Bali (POI)

```http
GET /api/v1/pois                # 119 POI (filter: ?category=pantai, ?q=uluwatu, ?limit=)
GET /api/v1/pois/categories     # Kategori beserta ikon & label
GET /api/v1/pois/near?lat=-8.65&lng=115.22&radius_km=15   # POI terdekat
GET /api/v1/pois/pura-besakih   # Detail per POI
```

### Insiden Crowdsourced

```http
GET    /api/v1/incidents?lat=-8.65&lng=115.22&radius_km=30   # List insiden aktif (TTL 2 jam)
POST   /api/v1/incidents        # {"lat","lng","incident_type","description","reporter"}
DELETE /api/v1/incidents/{id}   # Tandai selesai
```

Tipe: `macet`, `banjir`, `tutup_jalan`, `kecelakaan`, `konstruksi`, `lainnya`. Insiden aktif memberi penalti pada skor rute (`incident_penalty`) sehingga rute pengguna lain menyesuaikan.

### Favorit & Tracking Real-time

```http
GET/POST /api/v1/favorites                # Simpan/muat rute favorit (SQLite)
PATCH/DELETE /api/v1/favorites/{id}       # Ubah nama / hapus
POST   /api/v1/track/start                # Mulai tracking -> {session_id, share_url}
GET    /api/v1/track/{id}/status          # Snapshot posisi & ETA live
GET    /api/v1/track/{id}/stream          # SSE realtime (data tiap beberapa detik)
```

Retrain juga bisa dijalankan sebagai script:

```bash
python scripts/retrain.py --min-samples 10
```

Model akan diblend dengan data riwayat hanya jika jumlah sampel riwayat ≥ `--min-samples`. Saat melatih, trip multi-stop (waypoint) disaring agar tidak mencemari pembelajaran ETA per-leg, dan outlier (waktu/jarak tak wajar) dibuang.

Prediksi ML dibatasi (clamp 0.6x–1.8x waktu heuristik) sehingga tidak pernah menghasilkan ETA liar; fitur `mode_factor` memastikan model membedakan mobil, motor, dan jalan kaki.

### AI Models & Konfigurasi

```http
GET  /api/v1/models/info         # Status semua model: travel-time AI, traffic ML, route scorer, sampel riwayat, blend_weight, metrik
POST /api/v1/models/retrain      # Retrain sinkron (409 bila training sedang berjalan)
GET  /api/v1/config/public       # Konfigurasi publik (interval realtime, threshold AI, keaktifan TomTom/OWM, bounds cakupan)
```

Respons `road_conditions.ai` pada `/route/predict` berisi:
`model_active`, `blend_weight`, `samples`, `predicted_minutes` (estimasi ML) dan `heuristic_minutes` (estimasi dasar) — UI menampilkan keduanya.

### Traffic Real-time & Preview per Jam

```http
GET /api/v1/traffic/now?lat=-8.65&lng=115.2            # Kepadatan saat ini + sumber (heuristic/model)
GET /api/v1/traffic/hourly?lat=-8.65&lng=115.2&hour=9  # Kurva kepadatan 24 jam + grid preview
GET /api/v1/realtime/incidents                         # SSE: insiden baru/resolved (event=init|traffic|...)
GET /api/v1/realtime/traffic?lat=-8.65&lng=115.2&interval_s=5  # SSE: denyut kepadatan traffic live
GET /api/v1/realtime/route?origin_lat=..&origin_lng=..&dest_lat=..&dest_lng=..&distance_km=..&base_minutes=..&coords="lat,lng;lat,lng"&mode=car&interval_s=20 # SSE: ETA live rute aktif (traffic/insiden/AI diperbarui tiap denyut)
```

`/traffic/now` dihasilkan dari model ML bila sudah dilatih (blend_weight > 0), selain itu heuristic; `checked_at` menandai timestamp.

### Daftar Daerah Bali

Sistem mencakup **seluruh Bali** (9 kabupaten/kota). Daftar daerah tersedia lewat API untuk dropdown UI:

```http
GET /api/v1/areas               # Semua daerah (32+ titik: kota, pantai, pura, dll)
GET /api/v1/areas?q=uluwatu     # Pencarian per nama/kabupaten
GET /api/v1/areas/regencies     # Dikelompokkan per kabupaten
```

Cakupan koordinat: lat `-8.85..-8.0` (termasuk Uluwatu/Bukit), lng `114.4..115.8` (termasuk Gilimanuk di barat).

### Info Lalu Lintas

```http
GET /api/v1/traffic/{lat}/{lng}
```

### Info Cuaca

```http
GET /api/v1/weather/{lat}/{lng}
```

## Contoh Penggunaan

### Menggunakan curl

```bash
# Prediksi rute
curl -X POST "http://localhost:8000/api/v1/route/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "origin": {"lat": -8.6500, "lng": 115.2167},
    "destination": {"lat": -8.3405, "lng": 115.0920}
  }'

# Cek kesehatan sistem
curl "http://localhost:8000/health"
```

### Menggunakan Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/route/predict",
    json={
        "origin": {"lat": -8.6500, "lng": 115.2167},
        "destination": {"lat": -8.3405, "lng": 115.0920},
    }
)

data = response.json()
print(f"Jarak: {data['best_route']['distance_km']} km")
print(f"Estimasi: {data['best_route']['estimated_time_minutes']} menit")
print(f"Skor: {data['best_route']['overall_score']}/100")
```

## Struktur Proyek

```
route-prediction/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration (termasuk settings realtime/AI publik)
│   ├── models/              # Data models
│   ├── services/            # Business logic (osrm_service, history_service, traffic_service, realtime_feed...)
│   ├── ml/                  # AI/ML (trainer.py, travel_time_model.py, registry.py, traffic_predictor.py)
│   ├── api/                 # API endpoints
│   └── utils/               # Utilities
├── scripts/retrain.py       # Retrain models dari CLI
├── tests/                   # Tests
├── data/                    # Data storage
├── Dockerfile               # Produksi image
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Testing

```bash
pytest tests/ -v
```

## Dokumentasi API

Setelah menjalankan aplikasi, akses dokumentasi interaktif di:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT
