# 🦌 AntelopePay - Full Stack

Application bancaire mobile pour l'Afrique avec **FastAPI** (backend) et **Next.js** (frontend).

---

## 📁 Structure du projet

```
antelopepay-fullstack/
├── backend/                 # FastAPI Python
│   ├── app/
│   │   ├── main.py         # Point d'entrée
│   │   ├── database.py     # Connexion DB
│   │   ├── auth.py         # Fonctions JWT
│   │   ├── models/         # Modèles SQLAlchemy
│   │   ├── schemas/        # Schémas Pydantic
│   │   └── routers/        # Routes API
│   ├── requirements.txt
│   └── start.sh / start.bat
│
├── frontend/               # Next.js React
│   ├── src/
│   │   ├── app/           # Pages
│   │   ├── components/    # Composants UI
│   │   ├── contexts/      # AuthContext
│   │   └── lib/           # API client
│   ├── package.json
│   └── .env.local
│
└── README.md
```

---

## 🚀 Installation

### 1. Backend (FastAPI)

```bash
cd backend

# Créer l'environnement virtuel
python -m venv .venv

# Activer l'environnement
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**OU** utiliser le script automatique:
- Windows: `start.bat`
- Linux/Mac: `chmod +x start.sh && ./start.sh`

### 2. Frontend (Next.js)

```bash
cd frontend

# Installer les dépendances
npm install

# Lancer le serveur
npm run dev
```

---

## 🔗 URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

---

## 📱 Fonctionnalités

### Authentification
- ✅ Inscription avec téléphone
- ✅ Connexion avec JWT
- ✅ Déconnexion

### Transferts
- ✅ Envoyer de l'argent
- ✅ Historique des transactions
- ✅ Calcul automatique des frais (1.5%)

### Services
- ✅ Recharges mobiles (Orange, MTN, Moov, Telecel)
- ✅ Paiement de factures (Électricité, Eau, Internet, TV)
- ✅ QR Code pour recevoir de l'argent

### Analytics
- ✅ Vue des revenus/dépenses
- ✅ Graphiques par période

---

## 🛡️ API Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/v1/auth/register` | Inscription |
| POST | `/api/v1/auth/login` | Connexion |
| POST | `/api/v1/auth/logout` | Déconnexion |
| GET | `/api/v1/auth/me` | Utilisateur connecté |
| GET | `/api/v1/transfers` | Historique transferts |
| POST | `/api/v1/transfers` | Nouveau transfert |
| GET | `/api/v1/contacts` | Liste contacts |
| POST | `/api/v1/contacts` | Ajouter contact |
| POST | `/api/v1/services/recharge` | Recharge mobile |
| POST | `/api/v1/services/bills` | Payer facture |
| GET | `/api/v1/analytics` | Statistiques |

---

## ⚙️ Configuration

### Backend (.env)
```
DATABASE_URL=sqlite+aiosqlite:///./antelopepay.db
SECRET_KEY=votre-clé-secrète
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 🛠️ Technologies

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy (async)
- SQLite
- JWT (python-jose)
- Passlib (bcrypt)

### Frontend
- Next.js 14
- React 18
- Tailwind CSS
- Framer Motion
- Recharts
- Radix UI
- Lucide Icons

---

© 2025 AntelopePay - La Banque qui court avec vous 🦌
