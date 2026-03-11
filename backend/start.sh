#!/bin/bash

# Créer un environnement virtuel si inexistant
if [ ! -d ".venv" ]; then
    echo "Création de l'environnement virtuel..."
    python -m venv .venv
fi

# Activer l'environnement virtuel
source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null

# Installer les dépendances
echo "Installation des dépendances..."
pip install -r requirements.txt

# Lancer le serveur
echo "Démarrage du serveur FastAPI..."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
