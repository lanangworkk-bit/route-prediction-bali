# Prediksi Rute Terbaik Kendaraan dengan AI

Sistem prediksi rute terbaik untuk kendaraan di Bali menggunakan AI yang mempertimbangkan lalu lintas, kondisi cuaca, dan faktor lingkungan lainnya.

## Fitur Utama

- **Multi-Route Scoring** - Hitung dan bandingkan beberapa rute alternatif
- **Traffic Prediction** - Prediksi kepadatan lalu lintas berdasarkan waktu dan lokasi
- **Weather Integration** - Integrasi data cuaca untuk penyesuaian rute
- **Interactive Map** - Visualisasi peta interaktif dengan Folium
- **ML Models** - Model machine learning untuk prediksi dan scoring

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

## API Endpoints

### Prediksi Rute

```http
POST /api/v1/route/predict
Content-Type: application/json

{
  "origin": {"lat": -8.6500, "lng": 115.2167},
  "destination": {"lat": -8.3405, "lng": 115.0920},
  "preferences": {
    "avoid_tolls": false,
    "avoid_highways": false,
    "priority": "time"
  }
}
```

### Visualisasi Rute

```http
GET /api/v1/route/visualize?origin_lat=-8.6500&origin_lng=115.2167&dest_lat=-8.3405&dest_lng=115.0920
```

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
│   ├── services/            # Business logic
│   ├── ml/                  # AI/ML models
│   ├── api/                 # API endpoints
│   └── utils/               # Utilities
├── tests/                   # Tests
├── data/                    # Data storage
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
