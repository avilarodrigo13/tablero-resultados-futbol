import urllib.request
import json
import ssl
import sys
import os
import concurrent.futures
from datetime import datetime, timedelta

# Mapeo de ligas con su respectiva prioridad (menor valor = mayor prioridad)
SLUG_PRIORITY = {
    # 1. Selecciones Nacionales (Copa América, Eurocopa, Nations League, Eliminatorias, Amistosos)
    "conmebol.america": 10,
    "uefa.euro": 20,
    "uefa.nations": 30,
    "conmebol.wcq": 40,
    "uefa.ecq": 50,
    "fifa.friendly": 60,
    
    # 2. Competencias Continentales de Clubes de América
    "conmebol.libertadores": 100,
    "conmebol.sudamericana": 110,
    
    # 3. Clubes de Argentina (Ligas y Copas Locales)
    "arg.1": 120,
    "arg.copa": 130,
    "arg.supercopa": 140,
    
    # 4. Competencias Continentales de Clubes de Europa
    "uefa.champions": 200,
    "uefa.europa": 210,
    "uefa.europa.conf": 220,
    
    # 5. Clubes de Inglaterra
    "eng.1": 300,
    "eng.fa": 310,
    "eng.league_cup": 320,
    
    # 6. Clubes de España
    "esp.1": 330,
    "esp.copa_del_rey": 340,
    
    # 7. Clubes de Italia
    "ita.1": 350,
    "ita.coppa_italia": 360,
    
    # 8. Clubes de Alemania
    "ger.1": 370,
    "ger.dfb_pokal": 380,
    
    # 9. Clubes de Francia
    "fra.1": 390,
    "fra.coupe_de_france": 400
}

# Traducción de nombres de ligas al español y simplificaciones aprobadas
LEAGUE_NAME_TRANSLATIONS = {
    # 1. Selecciones Nacionales
    "Copa América": "Copa América",
    "UEFA European Championship": "Eurocopa",
    "UEFA Euro": "Eurocopa",
    "UEFA Nations League": "Nations League",
    "FIFA World Cup Qualifying - CONMEBOL": "E. CONMEBOL",
    "CONMEBOL World Cup Qualifying": "E. CONMEBOL",
    "UEFA European Championship Qualifying": "Clasif. Eurocopa",
    "UEFA ECQ": "Clasif. Eurocopa",
    "International Friendly": "Amistosos Int.",
    "Friendly": "Amistosos Int.",

    # 2. Clubes Región Argentina y América
    "Argentine Liga Profesional de Fútbol": "Liga Profesional",
    "Argentine Primera División": "Liga Profesional",
    "Argentine Supercopa": "Supercopa Arg.",
    "Argentine Copa Argentina": "Copa Argentina",
    "CONMEBOL Sudamericana": "Copa Sudamericana",
    "CONMEBOL Libertadores": "Copa Libertadores",

    # 3. Clubes Europa (Internacionales)
    "UEFA Champions League": "Champions League",
    "UEFA Europa League": "Europa League",
    "UEFA Conference League": "Conference League",

    # 4. Inglaterra
    "English Premier League": "Premier League",
    "English FA Cup": "FA Cup",
    "FA Cup": "FA Cup",
    "English Carabao Cup": "Carabao Cup",
    "English League Cup": "Carabao Cup",
    "Carabao Cup": "Carabao Cup",

    # 5. España
    "Spanish LaLiga": "LaLiga",
    "Spanish Primera División": "LaLiga",
    "Spanish Copa del Rey": "Copa del Rey",
    "Copa del Rey": "Copa del Rey",

    # 6. Italia
    "Italian Serie A": "Serie A",
    "Italian Coppa Italia": "Coppa Italia",
    "Coppa Italia": "Coppa Italia",

    # 7. Alemania
    "German Bundesliga": "Bundesliga",
    "German DFB Pokal": "DFB-Pokal",
    "German DFB-Pokal": "DFB-Pokal",
    "DFB-Pokal": "DFB-Pokal",

    # 8. Francia
    "French Ligue 1": "Ligue 1",
    "French Coupe de France": "Coupe de France",
    "Coupe de France": "Coupe de France"
}

# Transición global a logos dark-theme de ESPN
def fix_dark_logo(logo_url):
    if not logo_url:
        return logo_url
    return logo_url.replace("/500/", "/500-dark/")

def fetch_scoreboard(slug):
    url = f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard"
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*'
        }
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error al consultar la liga '{slug}': {e}")
        return None

def parse_match(event):
    date_str_utc = event.get('date', '')
    try:
        dt_str = date_str_utc.replace('Z', '')
        parts = dt_str.split('T')
        date_parts = list(map(int, parts[0].split('-')))
        time_parts = list(map(int, parts[1].split(':')[:2]))
        dt_utc = datetime(date_parts[0], date_parts[1], date_parts[2], time_parts[0], time_parts[1])
        dt_arg = dt_utc - timedelta(hours=3)
    except Exception as e:
        print(f"Error parsing date {date_str_utc}: {e}")
        return None, None

    status_obj = event.get('status', {})
    type_obj = status_obj.get('type', {})
    state = type_obj.get('state', 'pre') # 'pre', 'in' o 'post'
    
    if state == 'in':
        status = 'IN_PLAY'
    elif state == 'post':
        status = 'FINISHED'
    else:
        status = 'TIMED'
        
    minute = status_obj.get('displayClock', '')
    
    competitions = event.get('competitions', [])
    if not competitions:
        return None, None
    comp = competitions[0]
    competitors = comp.get('competitors', [])
    if len(competitors) < 2:
        return None, None
        
    home_comp = None
    away_comp = None
    for c in competitors:
        if c.get('homeAway') == 'home':
            home_comp = c
        else:
            away_comp = c
            
    if not home_comp or not away_comp:
        home_comp = competitors[0]
        away_comp = competitors[1]
        
    home_team = home_comp.get('team', {})
    away_team = away_comp.get('team', {})
    
    home_abbr = home_team.get('abbreviation')
    if not home_abbr:
        home_abbr = home_team.get('name', 'HOME')[:3]
    home_abbr = home_abbr.upper()
    
    away_abbr = away_team.get('abbreviation')
    if not away_abbr:
        away_abbr = away_team.get('name', 'AWAY')[:3]
    away_abbr = away_abbr.upper()
    
    if status == 'TIMED':
        home_score = None
        away_score = None
    else:
        try:
            home_score = int(home_comp.get('score', 0))
            away_score = int(away_comp.get('score', 0))
        except:
            home_score = 0
            away_score = 0
            
    home_penalties = home_comp.get('shootoutScore')
    away_penalties = away_comp.get('shootoutScore')
    if home_penalties is not None:
        try: home_penalties = int(home_penalties)
        except: pass
    if away_penalties is not None:
        try: away_penalties = int(away_penalties)
        except: pass
        
    disp_date = dt_arg.strftime("%d/%m")
    disp_time = dt_arg.strftime("%H:%M")
    
    match_data = {
        "home": home_abbr,
        "away": away_abbr,
        "homeCrest": fix_dark_logo(home_team.get('logo')),
        "awayCrest": fix_dark_logo(away_team.get('logo')),
        "homeScore": home_score,
        "awayScore": away_score,
        "homePenalties": home_penalties,
        "awayPenalties": away_penalties,
        "status": status,
        "minute": minute,
        "date": disp_date,
        "time": disp_time
    }
    
    return dt_arg.date(), match_data

def main():
    # Obtener la ruta de salida
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    else:
        output_path = os.path.join(os.path.dirname(__file__), "partidos.json")
        
    print(f"Iniciando actualización de partidos. Destino: {output_path}")
    
    slugs = list(SLUG_PRIORITY.keys())
    raw_results = {}
    
    # Consultar concurrentemente
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(slugs)) as executor:
        future_to_slug = {executor.submit(fetch_scoreboard, slug): slug for slug in slugs}
        for future in concurrent.futures.as_completed(future_to_slug):
            slug = future_to_slug[future]
            try:
                data = future.result()
                if data:
                    raw_results[slug] = data
            except Exception as e:
                print(f"Error con la liga '{slug}': {e}")
                
    # Procesar y filtrar solo los partidos de "Hoy" (Zona horaria de Argentina UTC-3)
    now_arg = datetime.utcnow() - timedelta(hours=3)
    today_date = now_arg.date()
    
    grouped = {}
    
    for slug, raw in raw_results.items():
        leagues_list = raw.get('leagues', [])
        if not leagues_list:
            continue
        league_info = leagues_list[0]
        league_name = league_info.get('name', slug)
        league_name = LEAGUE_NAME_TRANSLATIONS.get(league_name, league_name)
        
        league_crest = None
        logos = league_info.get('logos', [])
        if logos:
            league_crest = fix_dark_logo(logos[0].get('href'))
            
        events = raw.get('events', [])
        for event in events:
            match_date, match_data = parse_match(event)
            if not match_date:
                continue
                
            # Solo conservamos partidos de hoy
            if match_date == today_date:
                if slug not in grouped:
                    grouped[slug] = {
                        "leagueName": league_name,
                        "leagueCrest": league_crest,
                        "matches": []
                    }
                grouped[slug]["matches"].append(match_data)
                
    # Ordenar las ligas por prioridad
    today_leagues = []
    sorted_slugs = sorted(grouped.keys(), key=lambda s: SLUG_PRIORITY.get(s, 999))
    for slug in sorted_slugs:
        today_leagues.append(grouped[slug])
        
    # Mantener la estructura del JSON anterior (vaciar yesterday y tomorrow)
    output_data = {
        "yesterday": [],
        "today": today_leagues,
        "tomorrow": []
    }
    
    # Escribir de forma atómica para evitar que el servidor Nginx lea un archivo incompleto
    temp_path = output_path + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        # Reemplazo atómico
        if os.path.exists(output_path):
            os.remove(output_path)
        os.rename(temp_path, output_path)
        print(f"Actualización exitosa. Se guardaron {len(today_leagues)} ligas con partidos programados hoy.")
    except Exception as e:
        print(f"Error escribiendo el archivo partidos.json: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    main()
