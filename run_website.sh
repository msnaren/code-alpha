#!/usr/bin/env bash
# ShopKart India - Local Development Web Server Launcher for Linux / macOS

echo "======================================================================"
echo "  ShopKart India - Local Development Web Server Launcher"
echo "======================================================================"
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 could not be found. Please install Python 3.10+."
    exit 1
fi

# 2. Copy .env if not exists
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "[*] Creating .env from .env.example..."
    cp .env.example .env
fi

# 3. Install requirements
echo "[*] Installing Python dependencies..."
python3 -m pip install -r requirements.txt --quiet

# 4. Run migrations
echo "[*] Applying migrations..."
python3 manage.py migrate --noinput

# 5. Seed data if needed
if [ ! -f "db.sqlite3" ]; then
    echo "[*] Seeding database..."
    python3 seed.py
fi

# 6. Start server
echo ""
echo "======================================================================"
echo "  Website running at: http://127.0.0.1:8000/"
echo "  Demo Credentials:"
echo "    - Admin:    admin / Admin@123"
echo "    - Customer: rahul / Password@123"
echo "======================================================================"
echo ""
python3 manage.py runserver 0.0.0.0:8000
