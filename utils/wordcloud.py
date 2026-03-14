import re
from collections import Counter
import random

STOP_WORDS = set([
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "l", "à", "a", "au", "aux", 
    "et", "ou", "où", "en", "dans", "pour", "par", "sur", "avec", "sans", "sous", 
    "ce", "cet", "cette", "ces", "son", "sa", "ses", "mon", "ma", "mes", "ton", "ta", "tes",
    "qui", "que", "quoi", "dont", "où", "il", "elle", "ils", "elles", "on", "nous", "vous",
    "je", "tu", "me", "te", "se", "ne", "pas", "plus", "moins", "très", "trop", "est", "sont",
    "a", "ont", "être", "avoir", "fait", "faire", "comme", "tout", "tous", "toute", "toutes",
    "mais", "donc", "or", "ni", "car", "y", "c", "s", "n", "m", "t", "qu"
])

def generate_svg_wordcloud(titles, num_words=50):
    """
    Prend une liste de titres, nettoie le texte, compte les fréquences 
    et génère un fichier SVG natif contenant un nuage de mots.
    """
    if not titles:
        return '<svg width="800" height="400" xmlns="http://www.w3.org/2000/svg"><text x="400" y="200" font-family="Arial" font-size="20" text-anchor="middle">Aucune donnée disponible</text></svg>'

    text = " ".join(titles).lower()
    words = re.findall(r'\b[a-zàâçéèêëîïôûùüÿñæœ]{2,}\b', text)
    filtered_words = [w for w in words if w not in STOP_WORDS]
    word_counts = Counter(filtered_words).most_common(num_words)
    
    if not word_counts:
        return '<svg width="800" height="400" xmlns="http://www.w3.org/2000/svg"><text x="400" y="200" font-family="Arial" font-size="20" text-anchor="middle">Nuage de mots vide</text></svg>'

    max_count = word_counts[0][1]
    width, height = 800, 400
    
    svg_elements = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background-color:#ffffff; border: 1px solid #e0e0e0; border-radius: 8px;">'
    ]
    
    colors = ['#2c3e50', '#e74c3c', '#27ae60', '#2980b9', '#8e44ad', '#f39c12', '#d35400', '#16a085', '#34495e']
    
    for word, count in word_counts:
        font_size = max(14, int(60 * (count / max_count)))
        x = random.randint(50, width - 150)
        y = random.randint(50, height - 50)
        color = random.choice(colors)
        
        text_element = f'<text x="{x}" y="{y}" font-family="Inter, system-ui, sans-serif" font-weight="bold" font-size="{font_size}" fill="{color}">{word}</text>'
        svg_elements.append(text_element)
        
    svg_elements.append('</svg>')
    
    return "\n".join(svg_elements)
