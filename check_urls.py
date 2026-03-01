# check_urls.py
from django.urls import get_resolver

def check_urls():
    resolver = get_resolver()
    print("\n=== URLS ENREGISTRÉES ===")
    for pattern in resolver.url_patterns:
        print(f"Pattern: {pattern.pattern}")
        if hasattr(pattern, 'callback'):
            print(f"  → Callback: {pattern.callback.__name__}")
        elif hasattr(pattern, 'url_patterns'):
            print(f"  → Includes: {pattern.url_patterns}")
    print("="*30)

if __name__ == "__main__":
    import django
    django.setup()
    check_urls()