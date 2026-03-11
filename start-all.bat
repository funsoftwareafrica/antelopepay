@echo off
REM Script de démarrage complet pour Windows
REM Démarre le backend ET le frontend

echo ============================================
echo   ANTELOPEPAY - Demarrage complet
echo ============================================
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installe ou n'est pas dans le PATH
    pause
    exit /b 1
)

REM Vérifier si Node.js est installé
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js n'est pas installe ou n'est pas dans le PATH
    pause
    exit /b 1
)

echo [1/4] Installation des dependances Python...
cd backend
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1

echo [2/4] Demarrage du backend FastAPI...
start "AntelopePay Backend" cmd /k "venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo [3/4] Installation des dependances Node.js...
cd ..\frontend
call npm install >nul 2>&1

echo [4/4] Demarrage du frontend Next.js...
start "AntelopePay Frontend" cmd /k "npm run dev"

echo.
echo ============================================
echo   SERVEURS DEMARRES!
echo ============================================
echo.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo.
echo   Ouvrez http://localhost:3000 dans votre navigateur
echo.
pause
