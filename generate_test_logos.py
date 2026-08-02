import urllib.request
import json
import ssl
import os
import concurrent.futures

# Mapeo de ligas y copas para logos de competencia
COMPETITION_SLUGS = {
    "Copa América": "conmebol.america",
    "Eurocopa": "uefa.euro",
    "UEFA Nations League": "uefa.nations",
    "Eliminatorias CONMEBOL": "conmebol.wcq",
    "Clasificatorias Euro": "uefa.ecq",
    "Copa Libertadores": "conmebol.libertadores",
    "Copa Sudamericana": "conmebol.sudamericana",
    "UEFA Champions League": "uefa.champions",
    "UEFA Europa League": "uefa.europa",
    "UEFA Conference League": "uefa.europa.conf",
    "Liga Profesional Argentina": "arg.1",
    "Copa Argentina": "arg.copa",
    "Supercopa Argentina": "arg.supercopa",
    "Premier League": "eng.1",
    "FA Cup": "eng.fa",
    "Carabao Cup": "eng.league_cup",
    "LaLiga": "esp.1",
    "Copa del Rey": "esp.copa_del_rey",
    "Serie A": "ita.1",
    "Coppa Italia": "ita.coppa_italia",
    "Bundesliga": "ger.1",
    "DFB-Pokal": "ger.dfb_pokal",
    "Ligue 1": "fra.1",
    "Coupe de France": "fra.coupe_de_france"
}

# Ligas de las cuales traeremos TODOS sus clubes
CLUB_LEAGUE_SLUGS = {
    "Liga Profesional Argentina": "arg.1",
    "Premier League (Inglaterra)": "eng.1",
    "LaLiga (España)": "esp.1",
    "Serie A (Italia)": "ita.1",
    "Bundesliga (Alemania)": "ger.1",
    "Ligue 1 (Francia)": "fra.1"
}

def fetch_url(url):
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def fix_dark_logo(logo_url):
    if not logo_url:
        return logo_url
    return logo_url.replace("/500/", "/500-dark/")

def get_competition_logo(name, slug):
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard"
    data = fetch_url(url)
    logo = None
    if data and data.get("leagues"):
        logos = data["leagues"][0].get("logos", [])
        if logos:
            logo = fix_dark_logo(logos[0].get("href"))
    return {"name": name, "slug": slug, "logo": logo}

def get_league_clubs(name, slug):
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/teams?limit=100"
    data = fetch_url(url)
    clubs = []
    if data and data.get("sports"):
        teams_list = data["sports"][0]["leagues"][0].get("teams", [])
        for t in teams_list:
            team_info = t.get("team", {})
            logo_url = None
            logos = team_info.get("logos", [])
            if logos:
                logo_url = fix_dark_logo(logos[0].get("href"))
            clubs.append({
                "name": team_info.get("displayName"),
                "abbr": team_info.get("abbreviation"),
                "id": team_info.get("id"),
                "logo": logo_url
            })
    return {"leagueName": name, "slug": slug, "clubs": sorted(clubs, key=lambda x: x["name"] or "")}

def main():
    print("Iniciando recopilación de logos de competencias...")
    competitions = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_competition_logo, name, slug): name for name, slug in COMPETITION_SLUGS.items()}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                competitions.append(res)
    # Ordenar competencias por nombre para mostrar
    competitions.sort(key=lambda x: x["name"])

    print("Iniciando recopilación de clubes por ligas...")
    leagues_clubs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(get_league_clubs, name, slug): name for name, slug in CLUB_LEAGUE_SLUGS.items()}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                leagues_clubs.append(res)
    # Ordenar por nombre de liga
    leagues_clubs.sort(key=lambda x: x["leagueName"])

    # Generar contenido HTML
    html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Prueba Visual de Logos - ESPN API</title>
    <style>
        body {
            background-color: #000000;
            color: #ffffff;
            font-family: Arial, sans-serif;
            margin: 20px;
            padding: 20px;
        }
        h1, h2 {
            border-bottom: 2px solid #ffcc00;
            padding-bottom: 10px;
            color: #ffcc00;
        }
        h1 {
            text-align: center;
            font-size: 32px;
        }
        h2 {
            font-size: 24px;
            margin-top: 40px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .card {
            background-color: #111111;
            border: 1px solid #333333;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: space-between;
        }
        .card img {
            width: 80px;
            height: 80px;
            object-fit: contain;
            background-color: transparent;
            margin-bottom: 10px;
        }
        .title {
            font-weight: bold;
            font-size: 14px;
            margin-top: 5px;
            text-overflow: ellipsis;
            overflow: hidden;
            white-space: nowrap;
            width: 100%;
        }
        .meta {
            color: #aaaaaa;
            font-size: 12px;
            margin-top: 5px;
        }
        .badge {
            background-color: #ffcc00;
            color: #000000;
            font-weight: bold;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            margin-top: 5px;
        }
        .logo-glow-fix {
            filter: drop-shadow(0px 0px 1px #ffffff) drop-shadow(0px 0px 2px #ffffff);
        }
    </style>
</head>
<body>
    <h1>Panel de Verificación Visual de Logos (ESPN API)</h1>
    
    <h2>1. Competencias y Torneos</h2>
    <div class="grid">
    """

    for comp in competitions:
        logo_img = comp["logo"]
        if logo_img:
            has_glow = logo_img and ("/1208.png" in logo_img or "/2395.png" in logo_img)
            img_class = "comp-logo logo-glow-fix" if has_glow else "comp-logo"
            img_html = f'<img class="{img_class}" src="{logo_img}" alt="{comp["name"]}" onerror="if(this.src.includes(\'500-dark\')){{this.src=this.src.replace(\'500-dark\',\'500\');}}else{{this.src=\'https://placehold.co/80x80/222/fff?text=Error\';}}">'
        else:
            img_html = '<div style="width:80px;height:80px;display:flex;align-items:center;justify-content:center;background:#222;border-radius:50%;">Sin Logo</div>'
            
        html += f"""
        <div class="card">
            {img_html}
            <div class="title">{comp["name"]}</div>
            <div class="meta">Slug: {comp["slug"]}</div>
        </div>
        """

    html += """
    </div>
    """

    for league in leagues_clubs:
        html += f"""
        <h2>2. Clubes de {league["leagueName"]} ({len(league["clubs"])} equipos)</h2>
        <div class="grid">
        """
        for club in league["clubs"]:
            logo_img = club["logo"]
            if logo_img:
                img_html = f'<img src="{logo_img}" alt="{club["name"]}" onerror="if(this.src.includes(\'500-dark\')){{this.src=this.src.replace(\'500-dark\',\'500\');}}else{{this.src=\'https://placehold.co/80x80/222/fff?text=Error\';}}">'
            else:
                img_html = '<div style="width:80px;height:80px;display:flex;align-items:center;justify-content:center;background:#222;border-radius:50%;">Sin Logo</div>'
                
            html += f"""
            <div class="card">
                {img_html}
                <div class="title">{club["name"]}</div>
                <div class="badge">{club["abbr"]}</div>
                <div class="meta">ID: {club["id"]}</div>
            </div>
            """
        html += """
        </div>
        """

    html += """
</body>
</html>
"""

    output_path = os.path.join(os.path.dirname(__file__), "test_logos.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Página de prueba generada con éxito en: {output_path}")

if __name__ == "__main__":
    main()
