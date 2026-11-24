import os

apps = [
    ("accounts", "Accounts"),
    ("profiles", "Profiles"),
    ("resumes", "Resumes"),
    ("opportunities", "Opportunities"),
    ("preferences", "Preferences"),
    ("search", "Search"),
    ("recommendations", "Recommendations"),
    ("ai_agent", "AiAgent"),
    ("evaluations", "Evaluations"),
]

base_dir = r"C:\Users\patel\OneDrive\Desktop\PROJECT\matchforge\apps"

for slug, class_name in apps:
    app_dir = os.path.join(base_dir, slug)
    os.makedirs(app_dir, exist_ok=True)
    
    # __init__.py
    with open(os.path.join(app_dir, "__init__.py"), "w") as f:
        f.write("")
        
    # apps.py
    with open(os.path.join(app_dir, "apps.py"), "w") as f:
        f.write(f'''from django.apps import AppConfig


class {class_name}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.{slug}'
''')

print("All app configs initialized successfully.")
