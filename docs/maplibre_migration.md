# Rencana Migrasi Leaflet → MapLibre GL JS (Fase 2)

**Tujuan**: Menuju pengalaman peta 3D seperti Google Maps 3D / Apple Maps saat flight mode aktif.

**Alasan di-fase terpisah (bukan dilakukan sekarang)**:
- Aplikasi ini berat menggunakan Leaflet: marker kustom, `polylineDecorator`, `Icon.Glyph`, vektor real-time (cuaca, lalu lintas). Migrasi langsung akan sangat tinggi risikonya.
- Pendekaman yang disarankan adalah **dual renderer** berfitur flag: mode Default tetap Leaflet; mode 3D aktifkan MapLibre + fase overlay (ETA, travel time, speed heatmap) dengan layer MapLibre terpisah.

## Strategi Penerapan

### 1. Flag konfigurasi
Tambah env:
```bash
MAP_RENDERER=leaflet   # leaflet | maplibre
```
Dengan catatan: konfigurasi ini hanya untuk sisi klien; backend tidak berubah.

### 2. Struktur UI baru
- Ganti `#map` element sesuai renderer; MapLibre membutuhkan container berbeda (`#map3d`).
- Tombol "3D" hanya muncul saat `MAP_RENDERER=maplibre` atau fitur sudah diaktifkan.
- Overlay layer (`tms_crud`, `polylineDecorator`, speed heatmap, ETA pills) harus punya adapter layer untuk MapLibre (misal `map.addSource`/`addLayer`).

### 3. Fitur yang harus di-port
- [ ] Marker vektor (mulai/tujuan)
- [ ] Marker real-time: bus, cuaca, insiden (biasanya `L.circleMarker` → MapLibre `circle` layer)
- [ ] Overlays: `rTraffic`, speed heatmap, flood overlay (biasanya tiled images → bisa jadi `raster` source)
- [ ] Progres polyline realtime (`routeProgressLine` → MapLibre `line` layer)
- [ ] Klik peta → `reverse_geocode` → dropdown marker
- [ ] Auto-fit-bounds (`map.fitBounds`)

### 4. Teknis kritis
- MapLibre membutuhkan token akses (`MAPLIBRE_STYLE_URL` atau MapTiler) atau gunakan style OSM publik.
- `map.on('load')` berbeda; layer harus didefinisikan `beforeId` untuk tidak menumpuk.
- `setIcon` Leaflet tidak ada di MapLibre; solusi: `setHTML` via marker `divIcon` atau MapLibre `Marker` with `element`.

### 5. Tahap penerapan (detail)

#### Tahap 2.1 — Riset & Setup
- Setup MapLibre GL JS di static, style basemap (misal `https://demotiles.maplibre.org/style.json` untuk MVP).
- Flag `MAP_RENDERER` di `index.html` (global `window.__MAP_RENDERER__` atau fetch dari `/api/v1/config`).
- Tambah `/config` global JS yang baca config backend.

#### Tahap 2.2 — Layer adapter
- Buat abstraction: `BaseMapLayer` (abstract) dengan `addVector`, `addTiled`, `addLine`, `fitBounds`.
- Implementasi Leaflet, MapLibre.

#### Tahap 2.3 — Porting fitur
- Migrasikan fitur satu per satu, uji komparasi visual secara paralel.

#### Tahap 2.4 — QA & Roam
- Uji coba GPS real-time dengan kedua renderer.
- Pastikan tidak ada race condition antara `connectGPS` dan MapLibre `requestAnimationFrame`.

### 6. Risiko & mitigasi
- **Risiko**: Beberapa fitur Leaflet (PolylineDecorator) tidak ada padanan native MapLibre → harus pakai plugin atau fallback.
- **Mitigasi**: Gunakan `@mapbox/polyline` atau `@turf/turf` untuk vektor arah, atau tampilkan panah via marker berulang.

---

**Status**: Rencana disimpan. Implementasi konkret akan dimulai saat kondisi peta stabil dan ada dorongan untuk visual 3D. Tidak half-migrate.
