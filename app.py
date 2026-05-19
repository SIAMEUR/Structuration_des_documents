import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from apscheduler.schedulers.background import BackgroundScheduler
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError
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
    current= datetime.now()

    for source in sources:

        interval_hours= source.get('update_interval', 1)
        latest_update = source.get('latest_update', datetime.min)

        if current >= latest_update + timedelta(hours = interval_hours):
            print(f"[{current}] Automatisation : Scraping de {source['journal_name']} (avec l'intervalle de: {interval_hours} heures)")
            fetch_and_parse_sitemap(source['url'], source['journal_name'])
            
            sources_collection.update_one(
                {"_id": source["_id"]},
                {"$set": {"latest_update": current}}
            )
        else:
            print(f"[{current}] Saut de {source['journal_name']} (pas encore à jour, prochain scrap dans quelques heures)")


scheduler.add_job(func=scrape_all_sources, trigger="interval", minutes=20)
scheduler.start()

@app.route('/')
def index():

    query = request.args.get('q', '')
    date_query= request.args.get('date_clic')

    
    filter = {}

    if date_query:
        dt = datetime.strptime(date_query, "%Y-%m-%d")
        start = datetime.combine(dt, datetime.min.time())
        end = datetime.combine(dt, datetime.max.time())

        filter = {"consultation_dates": {"$elemMatch": {"$gte": start, "$lte": end}}}



    elif query:
        regex = {"$regex": query, "$options": "i"}
        filter = {"$or": [
                {"title": regex},
                {"source": regex},
                {"keywords": regex}
                 ]
        }

    else:
        limit = datetime.now() - timedelta(days=3)
        filter = {"pub_date": {"$gte": limit}} 

    req = [
        {"$match": filter}, {"$sort": {"pub_date": -1}}, {"$group": { "_id": "$source","articles": {"$push": "$$ROOT"}
                    }},
    {"$sort": {"_id": 1}}              
    ]
    
    res = list(articles_collection.aggregate(req)) if articles_collection is not None else []
    return render_template('index.html', grouped_data=res, query=query or date_query, grouped=True)

@app.route('/track_click/<article_id>', methods=['POST'])
def track_click(article_id):
    try:
        res = articles_collection.update_one(
            {"_id": ObjectId(article_id)},
            {"$push": {"consultation_dates": datetime.now()}}
        )
        
        if res.modified_count == 0:
            res = articles_collection.update_one(
                {"_id": article_id},
                {"$push": {"consultation_dates": datetime.now()}}
            )
            
        print(f"Résultat pour {article_id} : {res.modified_count} modifié(s)")
        return jsonify({"status": "success", "modified": res.modified_count})
    except Exception as e:
        print(f"Erreur : {e}")
        return jsonify({"status": "error"}), 400

@app.route('/admin', methods=['GET'])
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
                flash(f"Source ajoutée avec succès {result['message']}", "success")
            else:
                print("Détails de l'erreur lors du scalping:" , result.get('message'))
                flash(f"Impossible d'ajouter la source", "error")
        
        except DuplicateKeyError:
            flash(f"Cette source est déja crée","warning")

                
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

    sources = list(sources_collection.find())
    sourceSelect = "all"


    svg_content = None
    num_words = 50
    days = 7
    
    if request.method == 'POST':
        num_words = int(request.form.get('num_words', 50))
        days = int(request.form.get('days', 7))
        sourceSelect = request.form.get('source', 'all')
        
        date_limit = datetime.now() - timedelta(days=days)

        query = {"pub_date": {"$gte": date_limit}}

        
        if sourceSelect and sourceSelect != "all":
            query["source"] = sourceSelect

        
        articles = list(articles_collection.find(query).sort("pub_date", -1))
        
        titles = [a['title'] for a in articles]
        svg_content = generate_svg_wordcloud(titles, num_words)
        
    return render_template('wordcloud.html', svg_content=svg_content,
            num_words=num_words, days=days, sources=sources, selected_source=sourceSelect)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
