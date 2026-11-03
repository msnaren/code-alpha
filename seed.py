#!/usr/bin/env python
"""
ShopKart India - Database Seeder Script
Run this script anytime using:
    python seed.py
"""
import os
import sys

# Configure UTF-8 stdout if needed
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

try:
    import django
    django.setup()
    from django.core.management import call_command
except ImportError as exc:
    sys.exit("Error: Could not import Django. Make sure dependencies are installed.")

if __name__ == '__main__':
    print("=" * 65)
    print("[*] ShopKart India - Initializing Database & Seeding Products")
    print("=" * 65)
    call_command('migrate')
    call_command('seed_data')
    print("=" * 65)
    print("[+] Ready! Start the server with:")
    print("    python manage.py runserver")
    print("=" * 65)
