import logging

logger = logging.getLogger(__name__)

POI_CATEGORIES = {
    "pura": {"label": "Pura & Keagamaan", "icon": "🛕"},
    "pantai": {"label": "Pantai", "icon": "🏖"},
    "air_terjun": {"label": "Air Terjun", "icon": "💦"},
    "alam": {"label": "Sawah & Alam", "icon": "🌾"},
    "gunung_danau": {"label": "Gunung & Danau", "icon": "⛰"},
    "kuliner": {"label": "Kuliner & Warung", "icon": "🍜"},
    "belanja": {"label": "Belanja & Pasar", "icon": "🛍"},
    "kesehatan": {"label": "Rumah Sakit & Klinik", "icon": "🏥"},
    "hotel": {"label": "Hotel & Penginapan", "icon": "🏨"},
    "hiburan": {"label": "Hiburan & Aktivitas", "icon": "🎭"},
    "lainnya": {"label": "Lainnya", "icon": "📍"},
}

# Kurasi database lokasi spesifik Bali. Koordinat mendekati posisi sebenarnya.
POIS = [
    # ============ Pura ============
    {"id": "pura-besakih", "name": "Pura Besakih", "category": "pura", "regency": "Karangasem", "lat": -8.3744, "lng": 115.4524, "note": "Mother Temple Bali, kompleks pura terbesar"},
    {"id": "pura-ulun-danu-bratan", "name": "Pura Ulun Danu Bratan", "category": "pura", "regency": "Tabanan", "lat": -8.2754, "lng": 115.1666, "note": "Pura di tepi Danau Beratan, ikon di uang Rp50rb"},
    {"id": "pura-tanah-lot", "name": "Pura Tanah Lot", "category": "pura", "regency": "Tabanan", "lat": -8.6214, "lng": 115.0864, "note": "Pura laut ikonik, sunset terkenal"},
    {"id": "pura-uluwatu", "name": "Pura Luhur Uluwatu", "category": "pura", "regency": "Badung", "lat": -8.8291, "lng": 115.0849, "note": "Pura tebing cliff, pertunjukan Kecak"},
    {"id": "pura-taman-ayun", "name": "Pura Taman Ayun", "category": "pura", "regency": "Badung", "lat": -8.5424, "lng": 115.1687, "note": "Taman kerajaan Mengwi, taman air UNESCO"},
    {"id": "pura-goa-lawah", "name": "Pura Goa Lawah", "category": "pura", "regency": "Klungkung", "lat": -8.5538, "lng": 115.4390, "note": "Pura Goa Kelelawar"},
    {"id": "pura-lempuyang", "name": "Pura Lempuyang Luhur", "category": "pura", "regency": "Karangasem", "lat": -8.3925, "lng": 115.6120, "note": "Gates of Heaven, gerbang surga"},
    {"id": "pura-tirta-empul", "name": "Pura Tirta Empul", "category": "pura", "regency": "Gianyar", "lat": -8.4157, "lng": 115.3147, "note": "Candi air suci ternama"},
    {"id": "pura-kehen", "name": "Pura Kehen", "category": "pura", "regency": "Bangli", "lat": -8.4122, "lng": 115.3072, "note": "Pura kerajaan tua di lereng Bangli"},
    {"id": "pura-penataran-agung-lempuyang", "name": "Pura Penataran Agung Lempuyang", "category": "pura", "regency": "Karangasem", "lat": -8.3925, "lng": 115.6150, "note": "Gapura candi bentar ikonik"},
    {"id": "pura-agung-jagatnatha", "name": "Pura Agung Jagatnatha", "category": "pura", "regency": "Kota Denpasar", "lat": -8.6506, "lng": 115.2164, "note": "Pura pusat Kota Denpasar"},
    {"id": "pura-saraswati", "name": "Pura Saraswati Ubud", "category": "pura", "regency": "Gianyar", "lat": -8.5069, "lng": 115.2628, "note": "Pura lotus di jantung Ubud"},
    {"id": "pura-gunung-kawi", "name": "Pura Gunung Kawi", "category": "pura", "regency": "Gianyar", "lat": -8.4193, "lng": 115.2693, "note": "Candi batu pahatan kuno di lembah"},
    {"id": "pura-meduwe-karang", "name": "Pura Meduwe Karang", "category": "pura", "regency": "Buleleng", "lat": -8.0643, "lng": 115.1077, "note": "Legenda Dewi Terpahit di Kubutambahan"},
    {"id": "pura-batukaru", "name": "Pura Luhur Batukaru", "category": "pura", "regency": "Tabanan", "lat": -8.3714, "lng": 115.0989, "note": "Pura di lereng Gunung Batukaru"},
    {"id": "pura-sakenan", "name": "Pura Sakenan Serangan", "category": "pura", "regency": "Kota Denpasar", "lat": -8.7133, "lng": 115.2293, "note": "Pura di Pulau Serangan, upacara Kuningan"},
    {"id": "pura-taman-gede", "name": "Pura Taman Gede Pule", "category": "pura", "regency": "Badung", "lat": -8.7835, "lng": 115.1295, "note": "Pura di pesisir Pecatu"},

    # ============ Pantai ============
    {"id": "pantai-kuta", "name": "Pantai Kuta", "category": "pantai", "regency": "Badung", "lat": -8.7234, "lng": 115.1683, "note": "Pantai pasir putih tersohor + sunset"},
    {"id": "pantai-legian", "name": "Pantai Legian", "category": "pantai", "regency": "Badung", "lat": -8.7096, "lng": 115.1693, "note": "Semua orang selancar santai"},
    {"id": "pantai-seminyak", "name": "Pantai Seminyak", "category": "pantai", "regency": "Badung", "lat": -8.6913, "lng": 115.1673, "note": "Beach club & sunset"},
    {"id": "pantai-double-six", "name": "Pantai Double Six", "category": "pantai", "regency": "Badung", "lat": -8.6837, "lng": 115.1658, "note": "Pantai Legian utara"},
    {"id": "pantai-batu-bolong", "name": "Pantai Batu Bolong", "category": "pantai", "regency": "Badung", "lat": -8.6450, "lng": 115.1333, "note": "Pantai Canggu tersohor untuk selancar"},
    {"id": "pantai-echo-beach", "name": "Pantai Echo Beach", "category": "pantai", "regency": "Badung", "lat": -8.6455, "lng": 115.0993, "note": "Pantai Batu Mejan"},
    {"id": "pantai-pererenan", "name": "Pantai Pererenan", "category": "pantai", "regency": "Badung", "lat": -8.6280, "lng": 115.1210, "note": "Pantai tenang barat Canggu"},
    {"id": "pantai-sanur", "name": "Pantai Sanur", "category": "pantai", "regency": "Kota Denpasar", "lat": -8.6901, "lng": 115.2630, "note": "Pantai pagi yang tenang, jalan senam"},
    {"id": "pantai-nusa-dua", "name": "Pantai Nusa Dua", "category": "pantai", "regency": "Badung", "lat": -8.8006, "lng": 115.2294, "note": "Pantai resort mewah"},
    {"id": "pantai-jimbaran", "name": "Pantai Jimbaran", "category": "pantai", "regency": "Badung", "lat": -8.7723, "lng": 115.1656, "note": "Seafood dinner sunset di pasir"},
    {"id": "pantai-balangan", "name": "Pantai Balangan", "category": "pantai", "regency": "Badung", "lat": -8.7905, "lng": 115.1610, "note": "Pantai cliff surga selancar"},
    {"id": "pantai-dreamland", "name": "Dreamland Beach (Pantai Cimongan)", "category": "pantai", "regency": "Badung", "lat": -8.7973, "lng": 115.1560, "note": "Pasir putih tebing tinggi"},
    {"id": "pantai-bingin", "name": "Pantai Bingin", "category": "pantai", "regency": "Badung", "lat": -8.7980, "lng": 115.1450, "note": "Karavan selancar cliff"},
    {"id": "pantai-pandawa", "name": "Pantai Pandawa", "category": "pantai", "regency": "Badung", "lat": -8.8320, "lng": 115.1715, "note": "Pantai tebing karang Bukit"},
    {"id": "pantai-melasti", "name": "Pantai Melasti", "category": "pantai", "regency": "Badung", "lat": -8.8285, "lng": 115.1635, "note": "Pantai karst indah di Ungasan"},
    {"id": "pantai-nyang-nyang", "name": "Pantai Nyang Nyang", "category": "pantai", "regency": "Badung", "lat": -8.8423, "lng": 115.1373, "note": "Pantai tersembunyi paling selatan"},
    {"id": "pantai-suluban", "name": "Pantai Suluban", "category": "pantai", "regency": "Badung", "lat": -8.8037, "lng": 115.0813, "note": "Pantai lewat gua di Uluwatu"},
    {"id": "pantai-padangbai", "name": "Pantai Padangbai", "category": "pantai", "regency": "Karangasem", "lat": -8.5283, "lng": 115.5003, "note": "Pelabuhan ferry ke Gili & Nusa Penida"},
    {"id": "pantai-candidasa", "name": "Pantai Candidasa", "category": "pantai", "regency": "Karangasem", "lat": -8.5020, "lng": 115.5560, "note": "Pantai tenang timur"},
    {"id": "pantai-amed", "name": "Pantai Amed", "category": "pantai", "regency": "Karangasem", "lat": -8.3420, "lng": 115.6470, "note": "Snorkeling pantai timur laut"},
    {"id": "pantai-tulamben", "name": "Tulamben / USAT Liberty Wreck", "category": "pantai", "regency": "Karangasem", "lat": -8.2870, "lng": 115.5910, "note": "Wreck diving terkenal"},
    {"id": "pantai-lovina", "name": "Pantai Lovina", "category": "pantai", "regency": "Buleleng", "lat": -8.1390, "lng": 115.0470, "note": "Dolphin watching pagi hari"},
    {"id": "pantai-pemuteran", "name": "Pantai Pemuteran", "category": "pantai", "regency": "Buleleng", "lat": -8.1435, "lng": 114.6620, "note": "Terumbu karang & bio-rock"},
    {"id": "pantai-menjangan", "name": "Menjangan Island", "category": "pantai", "regency": "Buleleng", "lat": -8.0860, "lng": 114.5200, "note": "Pulau snorkeling di Bali Barat"},
    {"id": "pantai-medewi", "name": "Pantai Medewi", "category": "pantai", "regency": "Jembrana", "lat": -8.3650, "lng": 114.6850, "note": "Long left point break barat"},
    {"id": "pantai-balian", "name": "Pantai Balian", "category": "pantai", "regency": "Tabanan", "lat": -8.5070, "lng": 115.0320, "note": "Surfer village barat"},

    # ============ Air Terjun ============
    {"id": "air-terjun-gitgit", "name": "Air Terjun Gitgit", "category": "air_terjun", "regency": "Buleleng", "lat": -8.1860, "lng": 115.1530, "note": "Air terjun besar dekat Singaraja"},
    {"id": "air-terjun-sekumpul", "name": "Air Terjun Sekumpul", "category": "air_terjun", "regency": "Buleleng", "lat": -8.1460, "lng": 115.1170, "note": "Air terjun tertinggi di Bali"},
    {"id": "air-terjun-tegenungan", "name": "Air Terjun Tegenungan", "category": "air_terjun", "regency": "Gianyar", "lat": -8.4970, "lng": 115.2770, "note": "Terjangkau dari Ubud"},
    {"id": "air-terjun-munduk", "name": "Air Terjun Munduk", "category": "air_terjun", "regency": "Buleleng", "lat": -8.2700, "lng": 115.0850, "note": "Alam pegunungan Munduk"},
    {"id": "air-terjun-banyumala", "name": "Air Terjun Banyumala", "category": "air_terjun", "regency": "Buleleng", "lat": -8.2790, "lng": 115.0920, "note": "Air terjun kembar yang tenang"},
    {"id": "air-terjun-nungnung", "name": "Air Terjun Nungnung", "category": "air_terjun", "regency": "Badung", "lat": -8.3730, "lng": 115.1290, "note": "Air terjun tinggi di utara Badung"},
    {"id": "air-terjun-tukad-cepung", "name": "Air Terjun Tukad Cepung", "category": "air_terjun", "regency": "Bangli", "lat": -8.2600, "lng": 115.4400, "note": "Cahaya matahari di antara tebing"},
    {"id": "air-terjun-aling-aling", "name": "Air Terjun Aling Aling", "category": "air_terjun", "regency": "Buleleng", "lat": -8.1750, "lng": 115.1650, "note": "Water slide alami di Sambangan"},
    {"id": "air-terjun-leke-leke", "name": "Air Terjun Leke Leke", "category": "air_terjun", "regency": "Badung", "lat": -8.3670, "lng": 115.1520, "note": "Air terjun tersembunyi antar hutan"},

    # ============ Sawah & Alam ============
    {"id": "tegallalang", "name": "Sawah Terasering Tegallalang", "category": "alam", "regency": "Gianyar", "lat": -8.4310, "lng": 115.2780, "note": "Ruang subak ikonik"},
    {"id": "jatiluwih", "name": "Sawah Terasering Jatiluwih", "category": "alam", "regency": "Tabanan", "lat": -8.3840, "lng": 115.0840, "note": "UNESCO World Heritage subak"},
    {"id": "sidemen", "name": "Sawah Sidemen", "category": "alam", "regency": "Karangasem", "lat": -8.4900, "lng": 115.4500, "note": "Lembah sawah Gunung Agung"},
    {"id": "monkey-forest", "name": "Monkey Forest Ubud", "category": "alam", "regency": "Gianyar", "lat": -8.5190, "lng": 115.2580, "note": "Kawasan monyet + hutan tropis"},
    {"id": "campuhan-ridge", "name": "Campuhan Ridge Walk", "category": "alam", "regency": "Gianyar", "lat": -8.5090, "lng": 115.2620, "note": "Jalan setapak bukit Ubud"},
    {"id": "taman-ayun-gardens", "name": "Taman Ayun Gardens", "category": "alam", "regency": "Badung", "lat": -8.5420, "lng": 115.1680, "note": "Taman air kerajaan Mengwi"},
    {"id": "hutan-pandan", "name": "Alas Pala 'Hutan Pandan'", "category": "alam", "regency": "Badung", "lat": -8.8100, "lng": 115.1580, "note": "Hutan bambu & pandan Bukit"},
    {"id": "kebun-binatang", "name": "Bali Safari & Marine Park", "category": "alam", "regency": "Gianyar", "lat": -8.6020, "lng": 115.3200, "note": "Taman safari di Gianyar"},
    {"id": "bali-zoo", "name": "Bali Zoo Park", "category": "alam", "regency": "Gianyar", "lat": -8.5680, "lng": 115.2780, "note": "Kebun binatang dekat Singapadu"},

    # ============ Gunung & Danau ============
    {"id": "gunung-agung", "name": "Gunung Agung", "category": "gunung_danau", "regency": "Karangasem", "lat": -8.3420, "lng": 115.5070, "note": "Gunung tertinggi Bali 3.142 m"},
    {"id": "gunung-batur", "name": "Gunung Batur", "category": "gunung_danau", "regency": "Bangli", "lat": -8.2420, "lng": 115.3760, "note": "Gunung berapi aktif + sunrise trek"},
    {"id": "gunung-batukaru", "name": "Gunung Batukaru", "category": "gunung_danau", "regency": "Tabanan", "lat": -8.3700, "lng": 115.0980, "note": "Gunung hutan hujan barat"},
    {"id": "gunung-catur", "name": "Gunung Catur / Buyan", "category": "gunung_danau", "regency": "Buleleng", "lat": -8.3780, "lng": 115.1670, "note": "Puncak Bedugul berbentuk Catur"},
    {"id": "danau-batur", "name": "Danau Batur", "category": "gunung_danau", "regency": "Bangli", "lat": -8.2550, "lng": 115.4030, "note": "Danau kawah di kaki Gunung Batur"},
    {"id": "danau-beratan", "name": "Danau Beratan", "category": "gunung_danau", "regency": "Tabanan", "lat": -8.2770, "lng": 115.1690, "note": "Danau Bedugul dengan Pura Ulun Danu"},
    {"id": "danau-buyan", "name": "Danau Buyan", "category": "gunung_danau", "regency": "Buleleng", "lat": -8.2480, "lng": 115.1280, "note": "Danau kembar di Bedugul"},
    {"id": "danau-tamblingan", "name": "Danau Tamblingan", "category": "gunung_danau", "regency": "Buleleng", "lat": -8.2550, "lng": 115.1000, "note": "Danau mistis di Munduk"},
    {"id": "taman-nasional-bali-barat", "name": "Taman Nasional Bali Barat", "category": "gunung_danau", "regency": "Jembrana", "lat": -8.1200, "lng": 114.5900, "note": "Hutan & pantai barat dengan jalak Bali"},

    # ============ Kuliner ============
    {"id": "ibu-oka", "name": "Babi Guling Ibu Oka", "category": "kuliner", "regency": "Gianyar", "lat": -8.5068, "lng": 115.2646, "note": "Babi guling legendaris Ubud"},
    {"id": "babi-guling-men-larih", "name": "Warung Babi Guling Men Larih", "category": "kuliner", "regency": "Badung", "lat": -8.5260, "lng": 115.2140, "note": "Babi guling dekat Sading"},
    {"id": "babi-guling-pak-malen", "name": "Babi Guling Pak Malen", "category": "kuliner", "regency": "Badung", "lat": -8.7165, "lng": 115.1680, "note": "Babi guling terkenal di Legian"},
    {"id": "ayam-betutu-gilimanuk", "name": "Ayam Betutu Khas Gilimanuk", "category": "kuliner", "regency": "Jembrana", "lat": -8.1650, "lng": 114.4380, "note": "Ayam betutu legendaris"},
    {"id": "mades-warang", "name": "Warung Mades", "category": "kuliner", "regency": "Badung", "lat": -8.6710, "lng": 115.1580, "note": "Rendang & sate Tanah Lot"},
    {"id": "seafood-jimbaran", "name": "Kawasan Makan Malam Jimbaran", "category": "kuliner", "regency": "Badung", "lat": -8.7780, "lng": 115.1620, "note": "Seafood BBQ di pantai"},
    {"id": "locavore", "name": "Locavore (Fine Dining Ubud)", "category": "kuliner", "regency": "Gianyar", "lat": -8.5083, "lng": 115.2620, "note": "Restoran peringkat Asia 50"},
    {"id": "warung-crispy", "name": "Warung Crispy Madu", "category": "kuliner", "regency": "Badung", "lat": -8.8120, "lng": 115.2030, "note": "Ayam crispy / madu di Pecatu"},

    # ============ Belanja ============
    {"id": "pasar-ubud", "name": "Pasar Seni Ubud", "category": "belanja", "regency": "Gianyar", "lat": -8.5060, "lng": 115.2610, "note": "Souvenir & kerajinan"},
    {"id": "pasar-badung", "name": "Pasar Badung", "category": "belanja", "regency": "Kota Denpasar", "lat": -8.6530, "lng": 115.2190, "note": "Pasar tradisional terbesar Denpasar"},
    {"id": "pasar-kumbasari", "name": "Pasar Kumbasari", "category": "belanja", "regency": "Kota Denpasar", "lat": -8.6520, "lng": 115.2160, "note": "Pasar kain & rempah tepi sungai"},
    {"id": "beachwalk", "name": "Beachwalk Shopping Center", "category": "belanja", "regency": "Badung", "lat": -8.7205, "lng": 115.1690, "note": "Mall tepi pantai Kuta"},
    {"id": "discovery-mall", "name": "Discovery Shopping Mall", "category": "belanja", "regency": "Badung", "lat": -8.7310, "lng": 115.1710, "note": "Mall Kuta ikonik (circular lift)"},
    {"id": "kuta-art-market", "name": "Kuta Art Market", "category": "belanja", "regency": "Badung", "lat": -8.7180, "lng": 115.1700, "note": "Pasar suvenir Kuta"},
    {"id": "galeria", "name": "Matahari Bali Galeria", "category": "belanja", "regency": "Kota Denpasar", "lat": -8.6640, "lng": 115.2100, "note": "Pusat perbelanjaan Kuta-selatan"},
    {"id": "ubin-senigi", "name": "Jalan Seni Ubud (Ubud Art Market)", "category": "belanja", "regency": "Gianyar", "lat": -8.5065, "lng": 115.2625, "note": "Lukisan & ornamen Ubud"},

    # ============ Kesehatan ============
    {"id": "rs-sanglah", "name": "RSUP Sanglah", "category": "kesehatan", "regency": "Kota Denpasar", "lat": -8.6630, "lng": 115.2390, "note": "Rumah sakit rujukan terbesar Bali"},
    {"id": "rs-bimc", "name": "BIMC Hospital Kuta", "category": "kesehatan", "regency": "Badung", "lat": -8.7110, "lng": 115.1810, "note": "RS internasional Kuta"},
    {"id": "rs-siloam", "name": "Siloam Hospital Denpasar", "category": "kesehatan", "regency": "Kota Denpasar", "lat": -8.6760, "lng": 115.2260, "note": "RS swasta Denpasar"},
    {"id": "rs-kasih-ibu", "name": "RS Kasih Ibu Denpasar", "category": "kesehatan", "regency": "Kota Denpasar", "lat": -8.6600, "lng": 115.2010, "note": "RS swasta pusat Denpasar"},
    {"id": "rs-prima-medika", "name": "Prima Medika Hospital", "category": "kesehatan", "regency": "Kota Denpasar", "lat": -8.6510, "lng": 115.1960, "note": "RS dekat Sunset Road"},
    {"id": "rs-bali-med", "name": "Bali Med Denpasar", "category": "kesehatan", "regency": "Kota Denpasar", "lat": -8.6660, "lng": 115.2150, "note": "RS & klinik Denpasar"},
    {"id": "rs-surya-husada", "name": "RSU Negara (Surya Husada)", "category": "kesehatan", "regency": "Jembrana", "lat": -8.3480, "lng": 114.6130, "note": "RS utama Jembrana"},
    {"id": "rs-buleleng", "name": "RSUD Kabupaten Buleleng", "category": "kesehatan", "regency": "Buleleng", "lat": -8.1080, "lng": 115.0840, "note": "RS rujukan Buleleng"},

    # ============ Hotel ============
    {"id": "hotel-ayana", "name": "AYANA Resort Jimbaran", "category": "hotel", "regency": "Badung", "lat": -8.7930, "lng": 115.1600, "note": "Resort tebing mewah"},
    {"id": "hotel-mulia", "name": "The Mulia Nusa Dua", "category": "hotel", "regency": "Badung", "lat": -8.8120, "lng": 115.2180, "note": "Resort super deluxe"},
    {"id": "hotel-apurva", "name": "The Apurva Kempinski", "category": "hotel", "regency": "Badung", "lat": -8.8260, "lng": 115.1980, "note": "Resort tebing Nusa Dua"},
    {"id": "hotel-st-regis", "name": "St. Regis Bali Resort", "category": "hotel", "regency": "Badung", "lat": -8.8450, "lng": 115.2330, "note": "Resort laguna Nusa Dua"},
    {"id": "hotel-hanging-gardens", "name": "Hanging Gardens Ubud", "category": "hotel", "regency": "Gianyar", "lat": -8.4250, "lng": 115.2550, "note": "Kolam renang infinity dunia"},
    {"id": "hotel-ayana-segi", "name": "Rimba Jimbaran (AYANA estate)", "category": "hotel", "regency": "Badung", "lat": -8.7950, "lng": 115.1620, "note": "Resort hutan tepi tebing"},
    {"id": "hotel-uluwatu-surfer", "name": "Brads at Uluwatu", "category": "hotel", "regency": "Badung", "lat": -8.8160, "lng": 115.1220, "note": "Surf camp Pantai Suluban"},
    {"id": "hotel-adiwarna", "name": "Adiwana Resort Ubud", "category": "hotel", "regency": "Gianyar", "lat": -8.5070, "lng": 115.2530, "note": "Resort hutan dekat Monkey Forest"},

    # ============ Hiburan ============
    {"id": "kecak-uluwatu", "name": "Pertunjukan Kecak Uluwatu", "category": "hiburan", "regency": "Badung", "lat": -8.8293, "lng": 115.0860, "note": "Tari kecak sunset di tebing"},
    {"id": "bali-swing", "name": "Bali Swing", "category": "hiburan", "regency": "Gianyar", "lat": -8.4290, "lng": 115.2740, "note": "Ayunan di atas sawah tegallalang"},
    {"id": "ubud-palace", "name": "Ubud Royal Palace", "category": "hiburan", "regency": "Gianyar", "lat": -8.5067, "lng": 115.2620, "note": "Istana Ubud + tari tradisional"},
    {"id": "waterbom", "name": "Waterbom Bali", "category": "hiburan", "regency": "Badung", "lat": -8.7245, "lng": 115.1770, "note": "Waterpark terbesar Asia"},
    {"id": "tirta-gangga", "name": "Taman Tirta Gangga", "category": "hiburan", "regency": "Karangasem", "lat": -8.4160, "lng": 115.5820, "note": "Kolam kerajaan air mancur"},
    {"id": "taman-ujung", "name": "Taman Air Ujung", "category": "hiburan", "regency": "Karangasem", "lat": -8.4610, "lng": 115.5520, "note": "Istana air tepi laut timur"},
    {"id": "gate-of-heaven", "name": "Gates of Heaven (Pura Penataran Lempuyang)", "category": "hiburan", "regency": "Karangasem", "lat": -8.3925, "lng": 115.6150, "note": "Spot foto gerbang surga"},
    {"id": "handara-gate", "name": "Handara Golf Resort Gate", "category": "hiburan", "regency": "Buleleng", "lat": -8.2620, "lng": 115.1590, "note": "Gerbang ikonik Bedugul"},
    {"id": "nusa-penida-keberangkatan", "name": "Penyeberangan Nusa Penida", "category": "hiburan", "regency": "Bandung", "lat": -8.7480, "lng": 115.1725, "note": "Fast boat ke Karang Asem / Nusa Penida"},

    # ============ Lainnya ============
    {"id": "bandara-ngurah-rai", "name": "Bandara I Gusti Ngurah Rai (DPS)", "category": "lainnya", "regency": "Badung", "lat": -8.7481, "lng": 115.1670, "note": "Bandara Internasional Bali"},
    {"id": "pelabuhan-gilimanuk", "name": "Pelabuhan Gilimanuk", "category": "lainnya", "regency": "Jembrana", "lat": -8.1650, "lng": 114.4380, "note": "Ferry ke Banyuwangi, Jawa"},
    {"id": "pelabuhan-ubud-hills", "name": "Pelabuhan Padang Bai", "category": "lainnya", "regency": "Karangasem", "lat": -8.5280, "lng": 115.5010, "note": "Ferry ke Nusa Penida & Lembongan"},
    {"id": "pelabuhan-benoa", "name": "Pelabuhan Benoa", "category": "lainnya", "regency": "Kota Denpasar", "lat": -8.7480, "lng": 115.2130, "note": "Pelabuhan kapal pesiar & ferry"},
    {"id": "terminal-mengwi", "name": "Terminal Ubung Mengwi", "category": "lainnya", "regency": "Badung", "lat": -8.6340, "lng": 115.1700, "note": "Terminal bus antar kota"},
    {"id": "kantor-kelurahan-kerobokan", "name": "Kuta Square", "category": "lainnya", "regency": "Badung", "lat": -8.7180, "lng": 115.1665, "note": "Pusat kuliner & toko Kuta"},

    # Extra textbook Pasar & alat material
    {"id": "ubud-spa-desire", "name": "Karsa Spa Ubud", "category": "lainnya", "regency": "Gianyar", "lat": -8.5260, "lng": 115.2640, "note": "Spa sawah Ubud"},
    {"id": "asri-hospital-nusa-dua", "name": "BIMC Hospital Nusa Dua", "category": "kesehatan", "regency": "Badung", "lat": -8.7970, "lng": 115.2280, "note": "RS internasional Nusa Dua"},
]


class PoiService:
    """Catalog of curated specific destinations across Bali."""

    def __init__(self, pois: list[dict]):
        self._items = pois
        self._by_id = {p["id"]: p for p in pois}

    def list_pois(self, category=None, q=None, regency=None, limit=None) -> list[dict]:
        items = self._items
        if category:
            items = [p for p in items if p["category"] == category]
        if regency:
            items = [p for p in items if p["regency"].lower() == regency.lower()]
        if q:
            ql = q.lower()
            items = [p for p in items if ql in p["name"].lower() or ql in (p.get("note") or "").lower()]
        if limit:
            items = items[:limit]
        return items

    def get(self, poi_id: str) -> dict | None:
        return self._by_id.get(poi_id)

    def categories(self) -> list[dict]:
        return [
            {"id": cid, "label": meta["label"], "icon": meta["icon"], "count": sum(1 for p in self._items if p["category"] == cid)}
            for cid, meta in POI_CATEGORIES.items()
        ]

    def near(self, lat: float, lng: float, radius_km: float = 15.0, limit: int = 50) -> list[dict]:
        from app.models.route import Coordinate
        from app.utils.geo import haversine_distance

        center = Coordinate(lat=lat, lng=lng)
        scored = []
        for p in self._items:
            d = haversine_distance(center, Coordinate(lat=p["lat"], lng=p["lng"]))
            if d <= radius_km:
                scored.append({**p, "distance_km": round(d, 2)})
        scored.sort(key=lambda x: x["distance_km"])
        return scored[:limit]


poi_service = PoiService(POIS)
