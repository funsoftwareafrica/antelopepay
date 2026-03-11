@echo off

REM Créer un environnement virtuel si inexistant
if not exist ".venv" (
    echo Création de l'environnement virtuel...
    python -m venv .venv
)

REM Activer l'environnement virtuel
call .venv\Scripts\activate

REM Installer les dépendances
echo Installation des dépendances...
pip install -r requirements.txt

REM Lancer le serveur
echo Démarrage du serveur FastAPI...
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
