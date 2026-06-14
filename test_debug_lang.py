#!/usr/bin/env python
"""Debug UTF-8 and language loading"""
from app import app, t
from flask import render_template_string

print("=== Testing Language Detection ===")

# Test with German locale
with app.test_request_context(headers={'Accept-Language': 'de'}):
    print(f"Translator._language before render: {t._language}")
    result = render_template_string("{{ t('all_posts') }}")
    print(f"Translator._language after render: {t._language}")
    print(f"German translation result: {result}")
    print(f"Expected: Alle Beiträge")
    print(f"Contains ä: {'ä' in result}")
    print()

# Test with English
with app.test_request_context(headers={'Accept-Language': 'en'}):
    print(f"Translator._language before render: {t._language}")
    result = render_template_string("{{ t('all_posts') }}")
    print(f"Translator._language after render: {t._language}")
    print(f"English translation result: {result}")
    print(f"Expected: All posts")
