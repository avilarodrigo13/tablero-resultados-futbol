import json
import random
import os
from datetime import datetime, timedelta

# Ruta al archivo partidos.json
JSON_PATH = os.path.join(os.path.dirname(__file__), "partidos.json")

# Definición del mapeo de prioridades para el ordenamiento estricto
# Menor valor = Mayor prioridad
LEAGUE_PRIORITY = {
    # 1. Selecciones (Solo Oficiales)
    "Copa América": 10,
    "Eurocopa": 20,
    "Nations League": 30,
    "E. CONMEBOL": 40,
    "Clasif. Eurocopa": 50,
    "Amistosos Int.": 60,
    
    # 2. Clubes Región Argentina
    "Copa Libertadores": 100,
    "Copa Sudamericana": 110,
    "Liga Profesional": 120,
    "Copa Argentina": 130,
    "Trofeo de Campeones": 140,
    "Supercopa Arg.": 150,
    
    # 3. Clubes Europa (Internacionales)
    "Champions League": 200,
    "Europa League": 210,
    "Conference League": 220,
    
    # 4. Clubes Europa (Inglaterra)
    "Premier League": 300,
    "FA Cup": 310,
    "Carabao Cup": 320,
    
    # 5. Clubes Europa (España)
    "LaLiga": 330,
    "Copa del Rey": 340,
    
    # 6. Clubes Europa (Italia)
    "Serie A": 350,
    "Coppa Italia": 360,
    
    # 7. Clubes Europa (Alemania)
    "Bundesliga": 370,
    "DFB-Pokal": 380,
    
    # 8. Clubes Europa (Francia)
    "Ligue 1": 390,
    "Coupe de France": 400
}

def get_league_priority(league_name):
    # Retorna la prioridad asignada, o un valor muy alto (999) si es desconocida
    return LEAGUE_PRIORITY.get(league_name, 999)

# Logos reales obtenidos de ESPN CDN para equipos y competiciones
LOGOS = {
    # Ligas
    "Liga Profesional": "https://a.espncdn.com/i/leaguelogos/soccer/500-dark/1.png",
    "Copa Libertadores": "https://a.espncdn.com/i/leaguelogos/soccer/500-dark/58.png",
    "Champions League": "https://a.espncdn.com/i/leaguelogos/soccer/500-dark/2.png",
    "Premier League": "https://a.espncdn.com/i/leaguelogos/soccer/500-dark/23.png",
    "LaLiga": "https://a.espncdn.com/i/leaguelogos/soccer/500-dark/15.png",
    
    # Clubes
    "Boca": "https://a.espncdn.com/i/teamlogos/soccer/500-dark/5.png",
    "River": "https://a.espncdn.com/i/teamlogos/soccer/500-dark/16.png",
    "Belgrano": "https://a.espncdn.com/i/teamlogos/soccer/500-dark/4.png",
    "Rosario Central": "https://a.espncdn.com/i/teamlogos/soccer/500-dark/17.png",
    "Fluminense": "https://a.espncdn.com/i/teamlogos/soccer/500-dark/3445.png",
    "Real Madrid": "https://a.espncdn.com/i/teamlogos/soccer/500-dark/86.png",
    "Barcelona": "https://a.espncdn.com/i/teamlogos/soccer/500-dark/83.png",
    "Man City": "https://a.espncdn.com/i/teamlogos/soccer/500-dark/382.png",
    "Arsenal": "https://a.espncdn.com/i/teamlogos/soccer/500-dark/359.png",
    "Inter": "https://a.espncdn.com/i/teamlogos/soccer/500-dark/110.png",
    "Milan": "https://a.espncdn.com/i/teamlogos/soccer/500-dark/103.png"
}

def generate_mock_data():
    today_date = datetime.now()
    yesterday_date = today_date - timedelta(days=1)
    tomorrow_date = today_date + timedelta(days=1)
    
    # Formatos de fecha en string
    fmt_yesterday = yesterday_date.strftime("%d/%m")
    fmt_today = today_date.strftime("%d/%m")
    fmt_tomorrow = tomorrow_date.strftime("%d/%m")
    
    # Partidos base simulados por liga
    raw_leagues_data = {
        "yesterday": [
            {
                "leagueName": "Liga Profesional",
                "leagueCrest": LOGOS["Liga Profesional"],
                "matches": [
                    {
                        "home": "BEL", "away": "ROS",
                        "homeCrest": LOGOS["Belgrano"], "awayCrest": LOGOS["Rosario Central"],
                        "homeScore": 2, "awayScore": 1,
                        "status": "FINISHED", "date": fmt_yesterday, "time": "20:00"
                    }
                ]
            },
            {
                "leagueName": "LaLiga",
                "leagueCrest": LOGOS["LaLiga"],
                "matches": [
                    {
                        "home": "RMA", "away": "BAR",
                        "homeCrest": LOGOS["Real Madrid"], "awayCrest": LOGOS["Barcelona"],
                        "homeScore": 3, "awayScore": 2,
                        "status": "FINISHED", "date": fmt_yesterday, "time": "16:00"
                    }
                ]
            }
        ],
        "today": [
            {
                "leagueName": "Copa Libertadores",
                "leagueCrest": LOGOS["Copa Libertadores"],
                "matches": [
                    {
                        "home": "FLU", "away": "BOC",
                        "homeCrest": LOGOS["Fluminense"], "awayCrest": LOGOS["Boca"],
                        "homeScore": 1, "awayScore": 1,
                        "status": "IN_PLAY", "minute": "72'", "date": fmt_today, "time": "19:15"
                    }
                ]
            },
            {
                "leagueName": "Champions League",
                "leagueCrest": LOGOS["Champions League"],
                "matches": [
                    {
                        "home": "MCI", "away": "ARS",
                        "homeCrest": LOGOS["Man City"], "awayCrest": LOGOS["Arsenal"],
                        "homeScore": 0, "awayScore": 0,
                        "status": "IN_PLAY", "minute": "15'", "date": fmt_today, "time": "16:00"
                    }
                ]
            },
            {
                "leagueName": "Liga Profesional",
                "leagueCrest": LOGOS["Liga Profesional"],
                "matches": [
                    {
                        "home": "RIV", "away": "BEL",
                        "homeCrest": LOGOS["River"], "awayCrest": LOGOS["Belgrano"],
                        "homeScore": None, "awayScore": None,
                        "status": "TIMED", "date": fmt_today, "time": "21:30"
                    }
                ]
            }
        ],
        "tomorrow": [
            {
                "leagueName": "Premier League",
                "leagueCrest": LOGOS["Premier League"],
                "matches": [
                    {
                        "home": "ARS", "away": "MCI",
                        "homeCrest": LOGOS["Arsenal"], "awayCrest": LOGOS["Man City"],
                        "homeScore": None, "awayScore": None,
                        "status": "TIMED", "date": fmt_tomorrow, "time": "15:00"
                    }
                ]
            },
            {
                "leagueName": "Liga Profesional",
                "leagueCrest": LOGOS["Liga Profesional"],
                "matches": [
                    {
                        "home": "BOC", "away": "ROS",
                        "homeCrest": LOGOS["Boca"], "awayCrest": LOGOS["Rosario Central"],
                        "homeScore": None, "awayScore": None,
                        "status": "TIMED", "date": fmt_tomorrow, "time": "19:00"
                    }
                ]
            }
        ]
    }
    
    # Procesar y ordenar jerárquicamente cada bloque de día
    processed_data = {}
    for day, leagues in raw_leagues_data.items():
        # Ordenar las ligas usando el mapeo de prioridades LEAGUE_PRIORITY
        # La función sorted ordena de menor a mayor prioridad (ej: 10 viene antes de 100)
        sorted_leagues = sorted(leagues, key=lambda l: get_league_priority(l["leagueName"]))
        processed_data[day] = sorted_leagues
        
    return processed_data

def main():
    print("Generando datos simulados ordenados jerárquicamente...")
    data = generate_mock_data()
    
    # Escribir en partidos.json con formato legible
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"Archivo actualizado correctamente en: {JSON_PATH}")
    
    # Imprimir resumen de verificación en consola
    for day in ["yesterday", "today", "tomorrow"]:
        print(f"\n[{day.upper()}] Ligas ordenadas:")
        for idx, league in enumerate(data[day]):
            prio = get_league_priority(league["leagueName"])
            print(f"  {idx + 1}. {league['leagueName']} (Prioridad: {prio}) - {len(league['matches'])} partidos")

if __name__ == "__main__":
    main()
