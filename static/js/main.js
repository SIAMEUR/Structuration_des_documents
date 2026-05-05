document.addEventListener("DOMContentLoaded", function() {
    const articleLinks = document.querySelectorAll(".track-click");
    
    articleLinks.forEach(link => {
        link.addEventListener("click", function(e) {
            const articleId = this.getAttribute("data-id");
            
            // Ici on appel le backend pour incrémenter le compteur de clics
            fetch(`/track_click/${articleId}`, {
                method: "POST"
            })
            .then(response => {
                if (response.ok) {
                    console.log(`Clic enregistré pour l'article ${articleId}`);
                }
            })
            .catch(err => {
                console.error("Erreur de tracking", err);
            });
            
            // Le comportement par défaut continue (ouverture dans un nouvel onglet)
        });
    });
});

function downloadSVG() {
    const svgElement = document.querySelector(".svg-container svg");
    if (!svgElement) return;

    const serializer = new XMLSerializer();
    let source = serializer.serializeToString(svgElement);

    if (!source.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)) {
        source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
    }

    const blob = new Blob([source], {type: "image/svg+xml;charset=utf-8"});
    const url = URL.createObjectURL(blob);
    
    const downloadLink = document.createElement("a");
    downloadLink.href = url;
    downloadLink.download = "nuage_mots.svg";
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}
