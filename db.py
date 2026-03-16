import os
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    
    db = client["SD2026_projet"]
    
    sources_collection = db["G_ASA_sources"]
    articles_collection = db["G_ASA_articles"]
    
    articles_collection.create_index("link", unique=True)
    sources_collection.create_index("url", unique=True)
    
except Exception as e:
    print(f"Erreur de connexion à la base de données : {e}")
    db = None
    sources_collection = None
    articles_collection = None
