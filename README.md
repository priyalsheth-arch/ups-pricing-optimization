# UPS Store Pricing Intelligence Tool

A web application to help UPS Store franchise locations identify pricing gaps, flag upsell opportunities, and estimate revenue upside vs. competitors.

## What It Does

- **Pricing Gap Analysis** — Compare your prices vs. FedEx, USPS, Staples, Office Depot
- **Upsell Opportunity Engine** — 10 rule-based flags (ground→2day, no insurance, packing cross-sell, etc.)
- **Revenue Opportunity Model** — 3-bucket calculation: gap capture + upsell conversions + add-on attach
- **CSV Upload** — Import ConnectSuite daily/weekly exports; no live API integration needed
- **Multi-Store View** — Compare all 4 locations side by side
- **Role-Based Access** — Admin / Manager / Staff roles with appropriate permissions

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create database and seed data
python seed.py

# Start API server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Default Accounts

| Role    | Email                    | Password    |
|---------|--------------------------|-------------|
| Admin   | admin@upsstore.com       | admin123    |
| Manager | manager@upsstore.com     | manager123  |
| Staff   | staff@upsstore.com       | staff123    |

---

## First-Time Setup Workflow

1. **Log in** as manager or admin
2. **Upload → ConnectSuite CSV** — export your last 30-60 days from ConnectSuite and upload
3. **Competitor Pricing** — manually enter FedEx, USPS, Staples prices for your key services
4. **Dashboard** — pricing gaps and upsell opportunities populate automatically
5. **Revenue Opportunity** — see your total estimated upside with the 3-bucket model

---

## ConnectSuite CSV Export

Export from ConnectSuite with these columns:

```
Transaction ID, Transaction Date, Transaction Time, Store Number,
Department, Item Code, Item Description, Quantity, Unit Price,
Extended Price, Discount, Net Amount, Carrier, Service Level,
Weight, Zone, Ship To State, Customer Account
```

A sample CSV is at `data/sample_csvs/connectsuite_sample.csv`.

---

## Data You Need to Provide Per Store

### From ConnectSuite (CSV export)
- **Transaction history** — last 30–90 days recommended for meaningful analysis
- Export: go to ConnectSuite Reports → Transaction Detail → export as CSV

### Competitor Prices (manual entry in the app)
Enter via Competitor Pricing page:

| Service | Competitors to check |
|---|---|
| Ground shipping | FedEx Ground, USPS Priority Mail |
| 2-Day shipping | FedEx 2Day |
| Overnight | FedEx Standard Overnight |
| B&W copies | Staples, Office Depot |
| Color copies | Staples, Office Depot |
| Mailbox rentals | Local competitors |

### Your Current Prices (auto-seeded; update as needed)
The seed data includes default prices. Update via the API or directly in the database if your prices differ.

---

## API Docs

Auto-generated at http://localhost:8000/docs

---

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy async + SQLite + Pandas + Alembic
- **Frontend**: React 18 + Vite + TypeScript + Tailwind CSS + Recharts
- **Auth**: JWT (8-hour tokens)
