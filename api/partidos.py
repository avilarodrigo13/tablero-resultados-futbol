import os
import json
import ssl
import urllib.request
import concurrent.futures
import threading
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

# ==========================================================================
# CONFIGURACIÓN Y MAPEO DE PRIORIDADES
# ==========================================================================

# Mapeo de prioridades por slug de ESPN (Menor valor = Mayor prioridad)
SLUG_PRIORITY = {
    # 1. Selecciones (Solo Oficiales)
    "conmebol.america": 10,
    "uefa.euro": 20,
    "uefa.nations": 30,
    "conmebol.wcq": 40,
    "uefa.ecq": 50,
    
    # 2. Clubes Región Argentina
    "conmebol.libertadores": 100,
    "conmebol.sudamericana": 110,
    "arg.1": 120,
    "arg.copa": 130,
    "arg.supercopa": 140,
    
    # 3. Clubes Europa (Internacionales)
    "uefa.champions": 200,
    "uefa.europa": 210,
    "uefa.europa.conf": 220,
    
    # 4. Clubes Europa (Inglaterra)
    "eng.1": 300,
    "eng.fa": 310,
    "eng.league_cup": 320,
    
    # 5. Clubes Europa (España)
    "esp.1": 330,
    "esp.copa_del_rey": 340,
    
    # 6. Clubes Europa (Italia)
    "ita.1": 350,
    "ita.coppa_italia": 360,
    
    # 7. Clubes Europa (Alemania)
    "ger.1": 370,
    "ger.dfb_pokal": 380,
    
    # 8. Clubes Europa (Francia)
    "fra.1": 390,
    "fra.coupe_de_france": 400
}

# ==========================================================================
# TRADUCCIÓN DE NOMBRES DE LIGAS Y SIMPLIFICACIONES APROBADAS
# ==========================================================================
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

# ==========================================================================
# TRANSICIÓN GLOBAL A LOGOS DARK-THEME
# ==========================================================================
def fix_dark_logo(logo_url):
    if not logo_url:
        return logo_url
    return logo_url.replace("/500/", "/500-dark/")

# ==========================================================================
# SISTEMA DE CACHÉ EN MEMORIA (DURACIÓN: 2 MINUTOS)
# ==========================================================================
CACHE = {
    "data": None,
    "timestamp": None
}
CACHE_LOCK = threading.Lock()
CACHE_DURATION = timedelta(minutes=2)

# ==========================================================================
# PARSEO DE DATOS DE LA API DE ESPN
# ==========================================================================

def fetch_scoreboard(slug):
    url = f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard"
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*'
        }
    )
    # Ignorar la verificación SSL para evitar problemas de certificados locales
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
    # Parsear la fecha del partido en UTC y convertirla a hora de Argentina (UTC-3)
    date_str_utc = event.get('date', '')
    try:
        # Formato esperado: YYYY-MM-DDTHH:MMZ
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
        
    # Determinar Local y Visitante
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
    
    # Siglas (TLA)
    home_abbr = home_team.get('abbreviation')
    if not home_abbr:
        home_abbr = home_team.get('name', 'HOME')[:3]
    home_abbr = home_abbr.upper()
    
    away_abbr = away_team.get('abbreviation')
    if not away_abbr:
        away_abbr = away_team.get('name', 'AWAY')[:3]
    away_abbr = away_abbr.upper()
    
    # Marcador
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
            
    # Penales en caso de definición
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

def process_all_leagues():
    slugs = list(SLUG_PRIORITY.keys())
    raw_results = {}
    
    # Consultar concurrentemente las ligas con un pool de hilos
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(slugs)) as executor:
        future_to_slug = {executor.submit(fetch_scoreboard, slug): slug for slug in slugs}
        for future in concurrent.futures.as_completed(future_to_slug):
            slug = future_to_slug[future]
            try:
                data = future.result()
                if data:
                    raw_results[slug] = data
            except Exception as e:
                print(f"Excepción al traer datos de '{slug}': {e}")
                
    # Agrupar por días
    now_arg = datetime.utcnow() - timedelta(hours=3)
    yesterday_date = (now_arg - timedelta(days=1)).date()
    today_date = now_arg.date()
    tomorrow_date = (now_arg + timedelta(days=1)).date()
    
    grouped = {
        "yesterday": {},
        "today": {},
        "tomorrow": {}
    }
    
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
                
            if match_date == yesterday_date:
                day_key = "yesterday"
            elif match_date == today_date:
                day_key = "today"
            elif match_date == tomorrow_date:
                day_key = "tomorrow"
            else:
                continue
                
            if slug not in grouped[day_key]:
                grouped[day_key][slug] = {
                    "leagueName": league_name,
                    "leagueCrest": league_crest,
                    "matches": []
                }
            grouped[day_key][slug]["matches"].append(match_data)
            
    # Ordenar las ligas por prioridad y armar el JSON final
    output = {
        "yesterday": [],
        "today": [],
        "tomorrow": []
    }
    
    for day in ["yesterday", "today", "tomorrow"]:
        sorted_slugs = sorted(grouped[day].keys(), key=lambda s: SLUG_PRIORITY.get(s, 999))
        for slug in sorted_slugs:
            output[day].append(grouped[day][slug])
            
    return output

def get_partidos_data():
    global CACHE
    with CACHE_LOCK:
        now = datetime.now()
        if CACHE["data"] is not None and CACHE["timestamp"] is not None:
            if now - CACHE["timestamp"] < CACHE_DURATION:
                return CACHE["data"]
                
        # Si la caché expiró o está vacía, hacer la llamada concurrentemente
        data = process_all_leagues()
        CACHE["data"] = data
        CACHE["timestamp"] = now
        return data

# ==========================================================================
# INTERFAZ HANDLER PARA VERCEL (SERVERLESS) Y SERVIDOR LOCAL
# ==========================================================================

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            data = get_partidos_data()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 's-maxage=120, stale-while-revalidate=60')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Error interno del servidor: {e}".encode('utf-8'))
            
        # Servidor estático (solo activo cuando se corre localmente)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Enrutamiento por defecto a index.html
        file_path = req_path
        if file_path == '/':
            file_path = '/index.html'
            
        full_path = os.path.abspath(os.path.join(base_dir, file_path.lstrip('/')))
        
        # Evitar path traversal
        if not full_path.startswith(base_dir):
            self.send_response(403)
            self.end_headers()
            return
            
        if os.path.exists(full_path) and os.path.isfile(full_path):
            content_type = 'text/plain'
            if full_path.endswith('.html'):
                content_type = 'text/html; charset=utf-8'
            elif full_path.endswith('.css'):
                content_type = 'text/css; charset=utf-8'
            elif full_path.endswith('.js'):
                content_type = 'application/javascript; charset=utf-8'
            elif full_path.endswith('.png'):
                content_type = 'image/png'
            elif full_path.endswith('.svg'):
                content_type = 'image/svg+xml'
                
            try:
                with open(full_path, 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-Type', content_type)
                    self.end_headers()
                    self.wfile.write(f.read())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

# Levantar servidor de desarrollo cuando se ejecuta el script directamente
if __name__ == '__main__':
    PORT = 8000
    server = HTTPServer(('127.0.0.1', PORT), handler)
    print(f"Servidor de desarrollo corriendo en: http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo servidor...")
        server.server_close()
