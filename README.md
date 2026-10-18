# CekFakta: AI Fake News & Political Bias Detector

[![CI Pipeline](https://github.com/subki72/CekFakta/actions/workflows/ci.yml/badge.svg)](https://github.com/subki72/CekFakta/actions)
[![Maturity Grade: Production](https://img.shields.io/badge/Maturity%20Grade-Production%20(68.3%2F100)-success.svg)](https://github.com/subki72/CekFakta)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-005571?logo=fastapi)](https://fastapi.tiangolo.com)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL%20RLS-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com/)
[![Groq Llama 3](https://img.shields.io/badge/Groq-Llama_3-f55036)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**CekFakta** adalah platform cerdas berbasis *Artificial Intelligence* (Generative AI) yang dirancang untuk membongkar narasi manipulatif, mendeteksi indikasi *buzzer*, dan mengukur tingkat objektivitas sebuah teks, artikel berita, maupun *screenshot* media sosial. Dibangun dengan antarmuka bergaya **Neo-Brutalism** yang berani dan modern.

---

## Fitur Utama

- **Analisis Berbasis AI (Groq + Llama 3):** Membedah teks untuk mencari logical fallacy, bias politik, dan sentimen emosional dengan kecepatan kilat.
- **Optical Character Recognition (OCR):** Tidak hanya teks dan URL, AI mampu membaca teks langsung dari tangkapan layar (screenshot) media sosial atau berita.
- **Smart Web Scraping:** Otomatis mengekstrak teks utama dari URL berita Indonesia untuk dianalisis.
- **Sistem Skor & Transparansi:** Memberikan skor objektivitas (0-100) dan penjelasan poin-per-poin (*reasoning*) mengapa sebuah narasi dianggap bias atau manipulatif.
- **Sistem Komunitas (Vote & Diskusi):** Pengguna yang *login* dapat memberikan *vote* (Setuju/Tidak Setuju) dan berdiskusi pada hasil analisis.
- **Neo-Brutalism UI:** Desain antarmuka yang tegas, berani, tanpa kompromi—mencerminkan perlawanan terhadap misinformasi.
- **Hardened Security & Headers:** Dilengkapi CSP (*Content Security Policy*), HSTS, anti-clickjacking (`X-Frame-Options: DENY`), dan Row-Level Security (RLS) PostgreSQL.

---

## Tech Stack

- **Frontend:** Next.js 15 (App Router), React 19, Tailwind CSS v4, Lucide React
- **Backend:** FastAPI (Python 3.10+), httpx, BeautifulSoup4, Pydantic v2
- **Database & Auth:** Supabase (PostgreSQL + RLS + Google OAuth)
- **AI Inference:** Groq API (Llama-3-70b-8192)
- **Deployment:** Vercel (Next.js Edge & Serverless Python Runtime)

---

## Project Structure

```text
CekFakta/
├── .github/workflows/          # CI/CD automated linting & test pipelines
├── api/                        # FastAPI backend & Python services
│   ├── tests/                  # Automated pytest suite (38 tests)
│   ├── main.py                 # FastAPI application & endpoints
│   ├── extractor.py            # Article scraper & text extractor
│   ├── ocr.py                  # Image OCR processor
│   ├── analyzer.py             # Llama 3 prompt reasoning engine
│   └── supabase_client.py      # Supabase connection & RLS client
├── Prompt/                     # System prompts & few-shot examples
├── public/                     # Static assets & icons
├── qa-report/                  # Production readiness QA reports
├── src/                        # Next.js 15 frontend application
│   ├── app/                    # App Router pages and API routes
│   ├── components/             # Neo-Brutalism UI components
│   └── lib/                    # Supabase browser clients & utilities
├── supabase/                   # Database schemas & RLS migrations
├── .env.example                # Environment variables template
├── .gitignore                  # Git exclusion rules
├── .pre-commit-config.yaml     # Pre-commit git hooks configuration
├── CHANGELOG.md                # Semantic versioning changelog
├── CONTRIBUTING.md             # Developer contribution guidelines
├── LICENSE                     # MIT License
├── Makefile                    # Single-command developer targets
├── next.config.ts              # Next.js config with hardened security headers
├── package.json                # Frontend dependencies & scripts
├── requirements.txt            # Python dependencies
├── ruff.toml                   # Ruff Python linter configuration
├── SECURITY.md                 # Vulnerability disclosure policy
└── vercel.json                 # Vercel deployment & rewrite configuration
```

---

## Quickstart & Local Development

### Single-Command Workflow (Makefile)

```bash
# Clone repository
git clone https://github.com/subki72/CekFakta.git
cd CekFakta

# 1. Instalasi seluruh dependensi (Node & Python):
make install

# 2. Menjalankan automated test suite (38 pytest cases):
make test

# 3. Menjalankan linter (ESLint & Ruff):
make lint

# 4. Menjalankan frontend development server:
make run

# 5. Build bundle production:
make build
```

---

### Manual Setup

#### 1. Persiapan Kebutuhan (Prerequisites)
- [Node.js](https://nodejs.org/) (Versi 18+ direkomendasikan)
- [Python](https://www.python.org/) (Versi 3.10+)
- Akun [Supabase](https://supabase.com/) & [Groq Cloud](https://console.groq.com/)

#### 2. Instalasi Dependencies Manual
Aplikasi ini berjalan sebagai Monorepo (Next.js dan FastAPI berada di direktori yang sama untuk Vercel Serverless).
```bash
# Instal dependency frontend (Node)
npm install

# Instal dependency backend (Python)
pip install -r requirements.txt
```

#### 3. Konfigurasi Environment Variables
Salin file `.env.example` ke `.env` di *root directory* proyek, dan isi nilai kredensial Anda:
```bash
cp .env.example .env
```

Pastikan variabel penting berikut terisi:
- `GROQ_API_KEY`: Kunci API dari Groq Cloud Console.
- `NEXT_PUBLIC_SUPABASE_URL` & `NEXT_PUBLIC_SUPABASE_ANON_KEY`: URL dan Anon Key Supabase.
- `SUPABASE_SERVICE_ROLE_KEY`: Service role secret untuk operasi backend.
- `CRON_SECRET`: Secret token untuk otentikasi cron job Vercel.

#### 4. Setup Database & Migrasi RLS
Jalankan file SQL berikut pada Supabase SQL Editor:
1. `supabase/schema.sql` (Inisialisasi tabel, relasi, indeks, dan RLS policies)
2. Atau jalankan migrasi `supabase/migrations/20261005_enable_rls.sql` untuk mengaktifkan Row-Level Security pada database yang sudah berjalan.

#### 5. Menjalankan Tes & Verifikasi Kualitas
Untuk memverifikasi kesiapan production:
```bash
# Menjalankan 38 automated unit & integration tests
pytest api/tests/ -v

# Menjalankan linter Next.js/TypeScript
npm run lint

# Menjalankan linter Python
ruff check api/

# Menjalankan production build frontend
npm run build
```

#### 6. Menjalankan Server Pengembangan
Karena frontend (Next.js) dan backend (FastAPI) berjalan di *port* terpisah saat mode pengembangan, Anda dapat membuka dua terminal:

**Terminal 1 (Backend - FastAPI):**
```bash
uvicorn api.main:app --reload --port 8000
```
Backend berjalan di `http://localhost:8000`.

**Terminal 2 (Frontend - Next.js):**
```bash
npm run dev
```
Buka `http://localhost:3000` di browser Anda!

---

## Security & Governance

- **Vulnerability Disclosure**: Review our security reporting guidelines in [SECURITY.md](SECURITY.md).
- **Contribution Guidelines**: Development setup and pull request etiquette in [CONTRIBUTING.md](CONTRIBUTING.md).
- **Release Changelog**: Track semantic releases and version updates in [CHANGELOG.md](CHANGELOG.md).
- **License**: Explicit open source licensing under the [MIT License](LICENSE).

---

## License

Distributed under the MIT License. See `LICENSE` for more information.
