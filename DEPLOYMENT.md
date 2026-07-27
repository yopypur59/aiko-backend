# Panduan Deployment Railway - LiveKit Agent & Token Server

Panduan ini berisi petunjuk lengkap untuk mengaudit, mengonfigurasi, dan menyelaraskan penempatan (*deployment*) backend LiveKit ini di [Railway](https://railway.app/).

---

## 1. Ringkasan Arsitektur Proyek

Repositori ini memiliki 2 komponen utama yang saling melengkapi:

1. **LiveKit Agent Worker** ([`src/agent.py`](file:///c:/Users/MyBook%20Hype%20AMD/Documents/aiko_2/src/agent.py))
   - Berjalan sebagai **Worker Process** yang terhubung secara persistent via WebSocket ke LiveKit Cloud.
   - Menggunakan Gemini Realtime Model (`gemini-2.5-flash-native-audio-preview-12-2025`) untuk interaksi suara & teks.
   - Perintah produksi: `uv run src/agent.py start`

2. **FastAPI Token Generator Server** ([`src/token_server.py`](file:///c:/Users/MyBook%20Hype%20AMD/Documents/aiko_2/src/token_server.py))
   - Berjalan sebagai **Web Service (HTTP API)**.
   - Menyediakan endpoint `POST /get-token` untuk memproduksi JWT Access Token bagi peserta room LiveKit.
   - Perintah produksi: `uv run uvicorn src.token_server:app --host 0.0.0.0 --port ${PORT:-8000}`

---

## 2. Daftar Environment Variables Wajib & Opsional

Semua variabel lingkungan berikut harus dikonfigurasi di **Railway Dashboard -> Settings -> Environment Variables**:

| Nama Variabel | Status | Deskripsi & Contoh Nilai |
| :--- | :--- | :--- |
| `LIVEKIT_URL` | **Wajib** | URL WebSocket LiveKit Cloud (misal: `wss://aiko-xxx.livekit.cloud`) |
| `LIVEKIT_API_KEY` | **Wajib** | API Key dari LiveKit Cloud Dashboard |
| `LIVEKIT_API_SECRET` | **Wajib** | API Secret dari LiveKit Cloud Dashboard |
| `GOOGLE_API_KEY` | **Wajib** | API Key Google Gemini (untuk Gemini Realtime Audio Model) |
| `SUPABASE_URL` | *Opsional* | URL Supabase Project (untuk menyimpan riwayat percakapan/transcript) |
| `SUPABASE_SERVICE_ROLE_KEY` | *Opsional* | Service Role Key Supabase (agar backend dapat melakukan insert ke tabel `transcripts`) |
| `PORT` | *Otomatis* | Diatur otomatis oleh Railway untuk Web Service (default: `8000`) |
| `HOST` | *Opsional* | Host binding untuk uvicorn (default: `0.0.0.0`) |

---

## 3. Langkah Deploy di Railway

### Opsi A: Deploy LiveKit Agent Worker (Worker Service)

1. Buat **New Project** di Railway, pilih **Deploy from GitHub repo**.
2. Pilih repositori `aiko_2`.
3. Di bagian **Settings -> Build**:
   - Builder: **Dockerfile** (Railway akan otomatis mendeteksi [`Dockerfile`](file:///c:/Users/MyBook%20Hype%20AMD/Documents/aiko_2/Dockerfile) di root proyek).
4. Di bagian **Settings -> Deploy**:
   - Start Command: (Kosongkan untuk memakai `CMD` default di Dockerfile, yaitu `uv run src/agent.py start`).
5. Di bagian **Variables**:
   - Tambahkan `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, dan `GOOGLE_API_KEY` (serta `SUPABASE_*` jika menggunakan Supabase).
6. Deploy service. Setelah status berubah menjadi *Active*, periksa **Logs** untuk memastikan agen berhasil login ke LiveKit Cloud (*connected to room / listening for jobs*).

---

### Opsi B: Deploy Token Generator (HTTP Web Service)

Jika Anda juga membutuhkan HTTP Server untuk melayani permintaan token dari frontend:

1. Di proyek Railway yang sama, klik **+ New Service** -> pilih **GitHub Repo** (pilih repositori yang sama).
2. Di **Settings -> General**:
   - Ubah nama service menjadi `token-server`.
3. Di **Settings -> Deploy**:
   - Start Command:  
     ```bash
     uv run uvicorn src.token_server:app --host 0.0.0.0 --port ${PORT:-8000}
     ```
4. Di **Settings -> Networking**:
   - Klik **Generate Domain** untuk mendapatkan Public URL (misal: `https://token-server-production.up.railway.app`).
5. Di **Variables**:
   - Isi `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`.
6. Akses `https://<domain-railway>/` untuk menguji response JSON:  
   `{"message": "LiveKit Token Server is running"}`

---

## 4. Struktur Dockerfile & Pre-download Assets

[`Dockerfile`](file:///c:/Users/MyBook%20Hype%20AMD/Documents/aiko_2/Dockerfile) proyek ini menggunakan **Debian Bookworm + Python 3.11** dengan `uv` package manager:

- **Multi-stage build**: Mengisolasi *build dependencies* (`gcc`, `g++`, `python3-dev`) sehingga image produksi tetap aman dan ringan.
- **Pre-download assets**: Baris `RUN uv run --module livekit.agents download-files` mengeksekusi pengunduhan model pendukung (seperti model VAD Silero) pada saat *build stage*, sehingga container saat berjalan tidak perlu mengunduh file lagi.
- **Locked dependencies**: `uv sync --locked` menjamin ketersediaan versi package yang konsisten dari `uv.lock`.

---

## 5. Pengujian & Verifikasi Lokal

Sebelum deploy ke Railway, pastikan semua test dan linter berjalan lancar:

```bash
# 1. Jalankan unit test suite
uv run pytest

# 2. Cek linter & format
uv run ruff check
uv run ruff format --check

# 3. Jalankan Agent Worker secara lokal (mode dev)
uv run src/agent.py dev

# 4. Jalankan Token Server secara lokal
uv run python src/token_server.py
```
