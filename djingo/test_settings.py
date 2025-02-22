# test_settings.py
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djingo.settings')
import django
django.setup()
print("Success!")
