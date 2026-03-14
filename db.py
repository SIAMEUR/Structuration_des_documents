import os
from pymongo import MongoClient

# URI de connexion par défaut (modifiable via les variables d'environnement)
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")

try:
    # Initialisation de la connexion MongoDB
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    
    # Base de données spécifiée
    db = client["SD2026_projet"]
    
    # Collections spécifiées
    sources_collection = db["G_ASA_sources"]
    articles_collection = db["G_ASA_articles"]
    
    # Création d'index pour améliorer les performances (optionnel mais recommandé)
    # On s'assure que le lien de l'article est unique
    articles_collection.create_index("link", unique=True)
    sources_collection.create_index("url", unique=True)
    
except Exception as e:
    print(f"Erreur de connexion à la base de données : {e}")
    db = None
    sources_collection = None
    articles_collection = None
