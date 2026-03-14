import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from db import articles_collection

NAMESPACES = {
    'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9',
    'news': 'http://www.google.com/schemas/sitemap-news/0.9'
}

def fetch_and_parse_sitemap(source_url, source_name):
    """
    Récupère un sitemap XML et extrait les articles (news).
    """
    try:
        response = requests.get(source_url, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        articles_added = 0
        
        # Parcourir chaque balise <url>
        for url_node in root.findall('sm:url', NAMESPACES) or root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
            
            loc_node = url_node.find('sm:loc', NAMESPACES) or url_node.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if loc_node is None:
                continue
            link = loc_node.text
            
            news_node = url_node.find('news:news', NAMESPACES) or url_node.find('{http://www.google.com/schemas/sitemap-news/0.9}news')
            
            if news_node is not None:
                title_node = news_node.find('news:title', NAMESPACES) or news_node.find('{http://www.google.com/schemas/sitemap-news/0.9}title')
                date_node = news_node.find('news:publication_date', NAMESPACES) or news_node.find('{http://www.google.com/schemas/sitemap-news/0.9}publication_date')
                keywords_node = news_node.find('news:keywords', NAMESPACES) or news_node.find('{http://www.google.com/schemas/sitemap-news/0.9}keywords')
                
                title = title_node.text if title_node is not None else "Sans titre"
                
                pub_date_str = date_node.text if date_node is not None else datetime.now().isoformat()
                try:
                     pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                except ValueError:
                     pub_date = datetime.now()
                
                keywords = []
                if keywords_node is not None and keywords_node.text:
                    keywords = [k.strip() for k in keywords_node.text.split(',')]
                
                article_doc = {
                    "title": title,
                    "link": link,
                    "pub_date": pub_date,
                    "source": source_name,
                    "keywords": keywords,
                    "consultation_dates": []
                }
                
                try:
                    if articles_collection is not None:
                        result = articles_collection.update_one(
                            {"link": link},
                            {"$setOnInsert": article_doc},
                            upsert=True
                        )
                        if result.upserted_id:
                            articles_added += 1
                except Exception as e:
                    pass
                    
        return {"status": "success", "message": f"{articles_added} nouveaux articles trouvés pour {source_name}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
