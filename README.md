# Tablero de Resultados Multiliga (Cloud-Native)

Sistema dinámico de marcadores y resultados de fútbol multitorneo en tiempo real, optimizado para pantallas LED modulares publicitarias de 1024x128 px (equivalente a una marquesina física continua de 2048x64 px).

## 🚀 Arquitectura Cloud-Native (Vercel)

El proyecto está diseñado para funcionar 100% de forma autónoma en la nube sin depender de servidores o hardware domótiico local.

```
[ Raspberry Pi / Pantalla LED ] ---> [ Vercel Edge CDN ] ---> [ Serverless API /api/partidos.py ] ---> [ ESPN Real-Time API ]
```

* **Frontend:** HTML5, CSS3 dinámico y JavaScript puro (sin frameworks ni dependencias de compilación).
* **Backend Serverless:** Función Python en Vercel (`api/partidos.py`) que consulta concurrentemente la API en vivo de ESPN con un sistema de caché de 2 minutos en memoria.
* **Dominio Personalizado:** Enrutado vía CNAME en Cloudflare hacia `tablero.avilarodrigo.com.ar`.

---

## ⚽ Jerarquía y Prioridad de Competencias

El sistema ordena automáticamente las ligas y partidos bajo la siguiente prioridad estricta:

1. **Selecciones Nacionales:** Copa América, Eurocopa, Nations League, E. CONMEBOL, Clasif. Eurocopa, Amistosos Int.
2. **Clubes Región Argentina:** Copa Libertadores, Copa Sudamericana, Liga Profesional, Copa Argentina, Supercopa Arg.
3. **Clubes Europa (Internacionales):** Champions League, Europa League, Conference League.
4. **Clubes Europa (Ligas Locales):** Premier League, FA Cup, Carabao Cup, LaLiga, Copa del Rey, Serie A, Coppa Italia, Bundesliga, DFB-Pokal, Ligue 1, Coupe de France.

---

## 🎨 Especificaciones Visuales y Animación

* **Resolución Física:** 1024x128 px (mapeado en 2 viewports de 1024x64 px con offset CSS de `-1024px`).
* **Tipografía Uniforme:** Títulos de competencia en `32px` constante. Nombres simplificados a 17 caracteres o menos para evitar truncation o desfasajes.
* **Optimización de Rendimiento:** Sin animaciones CSS secundarias ni parpadeos internos para garantizar 60 FPS estables en hardware de bajos recursos como Raspberry Pi.

---

## 💻 Desarrollo Local

Para probar cambios localmente antes de desplegarlos a producción:

1. Iniciar el servidor local:
   ```bash
   powershell -File server.ps1
   ```
2. Abrir en el navegador: `http://localhost:8000`
3. Opciones de Query Params:
   * `http://localhost:8000/` (Consulta la API Serverless `/api/partidos`)
   * `http://localhost:8000/?mock=true` (Usa el archivo de datos de prueba local `partidos.json`)

---

## ⚙️ Despliegue Automatizado a Vercel

Cualquier cambio empujado a la rama principal (`main`) de este repositorio de GitHub activa el despliegue automático en producción en menos de 5 segundos.
