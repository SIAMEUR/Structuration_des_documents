import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from apscheduler.schedulers.background import BackgroundScheduler
from bson.objectid import ObjectId

from db import db, sources_collection, articles_collection
from utils.scraper import fetch_and_parse_sitemap
from utils.wordcloud import generate_svg_wordcloud

app = Flask(__name__)
app.secret_key = "clé session" 

scheduler = BackgroundScheduler()

def scrape_all_sources():
    if sources_collection is None:
        return
    sources = list(sources_collection.find())
    for source in sources:
        print(f"[{datetime.now()}] Automatisation : Scraping de {source['journal_name']}")
        fetch_and_parse_sitemap(source['url'], source['journal_name'])

scheduler.add_job(func=scrape_all_sources, trigger="interval", hours=1)
scheduler.start()

@app.route('/')
def index():
    query = request.args.get('q', '')
    
    if query:

        regex_query = {"$regex": query, "$options": "i"}
        articles = list(articles_collection.find({
            "$or": [
                {"title": regex_query},
                {"source": regex_query},
                {"keywords": regex_query}
            ]
        }).sort("pub_date", -1))
        
        return render_template('index.html', articles=articles, query=query, grouped=False)
    else:
        pipeline = [
            {"$sort": {"pub_date": -1}},
            {
                "$group": {
                    "_id": "$source",
                    "articles": {"$push": "$$ROOT"}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        grouped_data = list(articles_collection.aggregate(pipeline)) if articles_collection is not None else []
        return render_template('index.html', grouped_data=grouped_data, grouped=True)

@app.route('/track_click/<article_id>', methods=['POST'])
def track_click(article_id):
    """ Enregistre la date de consultation lorsqu'un utilisateur clique sur un lien """
    try:
        articles_collection.update_one(
            {"_id": ObjectId(article_id)},
            {"$push": {"consultation_dates": datetime.now()}}
        )
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/admin')
def admin():
    sources = list(sources_collection.find()) if sources_collection is not None else []
    return render_template('admin.html', sources=sources)

@app.route('/add_source', methods=['POST'])
def add_source():
    url = request.form.get('url')
    name = request.form.get('name')
    interval = int(request.form.get('interval', 1))
    
    if url and name:
        try:
            result = fetch_and_parse_sitemap(url, name)
            
            if result["status"] == "success":
                sources_collection.insert_one({
                    "url": url,
                    "journal_name": name,
                    "update_interval": interval
                })
                flash(f"Source ajoutée avec succès ! {result['message']}", "success")
            else:
                flash(f"Impossible d'ajouter la source (Erreur lors du scraping) : {result['message']}", "error")
                
        except Exception as e:
            flash(f"Erreur technique : {e}", "error")
            print("Erreur:", e)
            
    return redirect(url_for('admin'))

@app.route('/delete_source/<source_id>', methods=['POST'])
def delete_source(source_id):
    try:
        source = sources_collection.find_one({"_id": ObjectId(source_id)})
        if source:
            source_name = source['journal_name']
            sources_collection.delete_one({"_id": ObjectId(source_id)})
            
            articles_collection.delete_many({"source": source_name})
    except Exception as e:
        print("Erreur:", e)
        
    return redirect(url_for('admin'))


@app.route('/wordcloud', methods=['GET', 'POST'])
def wordcloud():
    svg_content = None
    num_words = 50
    days = 7
    
    if request.method == 'POST':
        num_words = int(request.form.get('num_words', 50))
        days = int(request.form.get('days', 7))
        
        date_limit = datetime.now() - timedelta(days=days)
        
        articles = list(articles_collection.find(
            {"pub_date": {"$gte": date_limit}},
            {"title": 1, "_id": 0}
        ))
        
        titles = [a['title'] for a in articles]
        svg_content = generate_svg_wordcloud(titles, num_words)
        
    return render_template('wordcloud.html', svg_content=svg_content, num_words=num_words, days=days)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
