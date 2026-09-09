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
- **Riwayat Trip** - Setiap prediksi tersimpan ke SQLite, dapat di-retrain model dengan data nyata
- **Interactive Map** - Visualisasi peta interaktif dengan Folium
- **ML Models** - Model machine learning untuk prediksi dan scoring
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
```

### 5. Jalankan Aplikasi

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Aplikasi akan berjalan di http://localhost:8000

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
    "priority": "time"
  }
}
```

### Visualisasi Rute (dengan waypoint)

```http
GET /api/v1/route/visualize?origin_lat=-8.6500&origin_lng=115.2167&dest_lat=-8.3405&dest_lng=115.0920&waypoints=-8.7930,115.2280
```

### Riwayat & Retrain Model

```http
GET /api/v1/history             # Daftar prediksi tersimpan
GET /api/v1/history/stats       # Statistik agregat
POST /api/v1/models/retrain     # Retrain ML dengan riwayat nyata
```

Retrain juga bisa dijalankan sebagai script:

```bash
python scripts/retrain.py --min-samples 10
```

Model akan diblend dengan data riwayat hanya jika jumlah sampel riwayat ≥ `--min-samples`.

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
│   ├── config.py            # Configuration
│   ├── models/              # Data models
│   ├── services/            # Business logic (osrm_service, history_service, traffic_service...)
│   ├── ml/                  # AI/ML models (trainer.py: retrain dengan riwayat)
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
