# Big Mart AI

AI-powered inventory management combining **shelf image analysis** (YOLOv8) with **demand forecasting** (Prophet) to prevent stock-outs and optimize restocking.

![Stack](https://img.shields.io/badge/React-18-blue) ![Stack](https://img.shields.io/badge/FastAPI-0.110-green) ![Stack](https://img.shields.io/badge/YOLOv8-ultralytics-purple) ![Stack](https://img.shields.io/badge/Prophet-Meta-orange)

## Features

- **Shelf Scanner** — Upload rack photos → YOLOv8 detects products, counts stock, flags empty spots
- **Demand Forecast** — Prophet models predict 7-day demand per SKU+store with confidence bands
- **Smart Alerts** — Compares current shelf stock vs predicted demand → critical / warning / OK
- **Restock Suggestions** — Calculates optimal restock quantity (weekly demand − current stock + 20% buffer)
- **Dashboard** — KPI cards, sales-vs-forecast trends, risk distribution, aisle occupancy charts
- **Product Management** — Full CRUD with search, category filters, and pagination

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, TailwindCSS, Recharts |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| ML Models | YOLOv8 nano (object detection), Prophet (time series) |
| Database | PostgreSQL (Neon serverless) |
| Storage | Cloudinary (shelf images) |
| Hosting | Vercel (frontend), Render (backend) |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (or use Docker)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

# Copy and fill environment variables
cp .env.example .env
# Edit .env with your DATABASE_URL, Cloudinary keys, etc.

# Run server
uvicorn app.main:app --reload
```

### Seed Demo Data

```bash
# Via CLI
python seed.py

# Or via API (after server is running)
curl -X POST http://localhost:8000/api/seed
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — login with:
- `admin` / `admin123`
- `manager` / `manager123`

### Docker (alternative)

```bash
docker-compose up --build
```

## Project Structure

```
big-mart-ai/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # auth, products, images, forecasts, alerts, dashboard
│   │   ├── core/            # config, database, security
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   └── services/        # shelf_detector, forecaster, alerting, image_storage
│   ├── Dockerfile
│   ├── requirements.txt
│   └── seed.py
├── frontend/
│   ├── src/
│   │   ├── api/             # Axios client with JWT interceptor
│   │   ├── components/      # ui/ (Button, Card, Badge...) + layout/ (Sidebar, Navbar)
│   │   ├── context/         # AuthContext
│   │   ├── pages/           # 8 pages (Dashboard, Upload, ShelfAnalysis, Forecast, Alerts, Products, Settings, Login)
│   │   └── types/           # TypeScript interfaces
│   └── vercel.json
├── docker-compose.yml
└── render.yaml
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Login → JWT |
| GET | `/api/auth/me` | Current user |
| GET/POST | `/api/products` | List / create products |
| POST | `/api/images/upload` | Upload shelf photo |
| POST | `/api/images/{id}/analyze` | Run YOLO detection |
| POST | `/api/forecasts/run` | Run Prophet forecast |
| GET | `/api/alerts` | Get stock-out alerts |
| GET | `/api/dashboard/stats` | KPI metrics |
| POST | `/api/seed` | Seed demo data |

## Deployment

**Frontend → Vercel**: Connect the `frontend/` directory, set `VITE_API_URL` to your Render URL.

**Backend → Render**: Use the `render.yaml` blueprint or deploy Docker manually. Set all env vars from `.env.example`.

**Database → Neon**: Create a serverless Postgres database and use the connection string as `DATABASE_URL`.

## License

MIT
