# ✈️ TripSplit — Trip Expense Splitter App

Trip ke kharche ko easily split karo! Group banao, friends ko invite karo, expenses add karo, aur automatic settlement dekho.

---

## 🚀 Setup & Run Kaise Karein

### Step 1 — Python install hai? Check karo
```bash
python --version   # Python 3.9+ chahiye
```

### Step 2 — Project folder mein jao
```bash
cd tripsplit
```

### Step 3 — Dependencies install karo
```bash
pip install -r requirements.txt
```

### Step 4 — Server start karo
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 5 — App kholne ke liye browser mein jao
```
http://localhost:8000
```

**Mobile se bhi open kar sakte ho:** Apna PC/Laptop ka IP address lo aur mobile mein kholo:
```
http://<TUMHARA-IP>:8000
```
(e.g. `http://192.168.1.5:8000`)

---

## 📱 App Use Kaise Karein

### Flow 1 — Group Creator (Trip Organizer)
1. "Naya Group Banao" pe click karo
2. Trip ka naam + apna naam daalo
3. **6-character code** copy karo
4. Dosto ko code bhejo (WhatsApp/SMS)

### Flow 2 — Friend (Join karna)
1. App kholke code box mein code daalo
2. Apna naam daalo → Join!

### Expenses Add Karo
1. "Expenses" tab → "+ Add Expense"
2. Description, Amount, Kisne pay kiya
3. **Checkboxes se select karo** — kiske beech split hoga
4. Save karo

### Settlement Dekho
- "Settlement" tab mein automatically calculate hoga
- Har person ka net balance dikhega
- **Minimum transactions** se settle kaise karein, yeh bhi dikhega

---

## 🗄️ Tech Stack

| Layer     | Technology          |
|-----------|---------------------|
| Backend   | FastAPI (Python)    |
| Database  | SQLite (SQLAlchemy) |
| Frontend  | Vanilla JS + CSS    |
| Server    | Uvicorn             |

---

## 📁 File Structure

```
tripsplit/
├── main.py          ← FastAPI app + all API endpoints
├── models.py        ← Database models (Group, Member, Expense)
├── schemas.py       ← Pydantic validation schemas
├── database.py      ← SQLite connection setup
├── requirements.txt ← Python dependencies
├── tripsplit.db     ← SQLite database (auto-create hoga)
└── static/
    └── index.html   ← Frontend SPA (mobile-friendly)
```

---

## 🔗 API Endpoints

| Method | URL | Kya karta hai |
|--------|-----|----------------|
| POST | `/api/groups` | Group banao |
| GET  | `/api/groups/{code}` | Group info |
| POST | `/api/groups/{code}/members` | Member add karo |
| GET  | `/api/groups/{code}/members` | Sare members |
| POST | `/api/groups/{code}/expenses` | Expense add karo |
| GET  | `/api/groups/{code}/expenses` | Sare expenses |
| DELETE | `/api/groups/{code}/expenses/{id}` | Expense delete karo |
| GET  | `/api/groups/{code}/settlement` | Settlement calculate karo |

API docs: `http://localhost:8000/docs`
