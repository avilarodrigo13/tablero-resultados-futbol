// Configuración del Tablero de Resultados Multiliga 2
const SPEED = 85; // Velocidad del scroll en píxeles por segundo (coincide con el anterior)
const TITLE_DURATION = 4500; // Duración de los títulos de día en ms
const INTRO_DURATION = 4000; // Duración de los separadores en ms (Templo del Fútbol)
const FETCH_INTERVAL = 30000; // Reintento si no hay datos cargados

// Elementos del DOM
const container1 = document.getElementById('container1');
const container2 = document.getElementById('container2');

// Precarga y decodificación forzada en GPU para evitar retrasos de renderizado
const tdfLogoPreload = new Image();
tdfLogoPreload.src = 'logo_tdf.png';
if (tdfLogoPreload.decode) {
    tdfLogoPreload.decode().catch(err => console.log('Logo TDF precargado en GPU'));
}

// Variables de estado
let playlist = [];
let currentPlaylistIndex = 0;
let fetchTimeoutId = null;
let playlistTimeoutId = null;

// Determinar URL de datos según el entorno o query params
// Por defecto en la Nube (Vercel) consulta la API Serverless /api/partidos.
// Si se agrega ?mock=true en la URL, consultará el archivo de prueba partidos.json.
const urlParams = new URLSearchParams(window.location.search);
const useMockData = urlParams.get('mock') === 'true';

const DATA_URL = useMockData ? 'partidos.json' : '/api/partidos';

/**
 * Carga el archivo de partidos (JSON o API) y arma la lista de reproducción
 */
async function loadMatchesData() {
    try {
        const response = await fetch(DATA_URL + '?t=' + new Date().getTime());
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        buildPlaylist(data);
    } catch (error) {
        console.error("Error cargando partidos:", error);
        
        // Si hay un error de red pero ya teníamos datos, seguimos reproduciendo con la playlist vieja
        if (playlist.length > 0) {
            console.log("Continuando con la playlist existente debido a error de red.");
            if (!playlistTimeoutId) {
                playNextItem();
            }
        } else {
            // Si es el primer arranque y falla, reintentamos pronto
            clearTimeout(fetchTimeoutId);
            fetchTimeoutId = setTimeout(loadMatchesData, FETCH_INTERVAL);
        }
    }
}

/**
 * Construye la lista de reproducción secuencial por ligas
 */
function buildPlaylist(data) {
    const newPlaylist = [];
    const leagues = data.today;

    if (leagues && leagues.length > 0) {
        leagues.forEach(league => {
            if (league.matches && league.matches.length > 0) {
                // Intercalar la introducción (Templo del Fútbol) antes de cada liga
                newPlaylist.push({
                    type: 'intros'
                });
                // Agregar el título de la competencia como diapositiva dedicada
                newPlaylist.push({
                    type: 'league_title',
                    leagueName: league.leagueName,
                    leagueCrest: league.leagueCrest
                });
                // Agregar la liga con sus partidos para el scroll
                newPlaylist.push({
                    type: 'league',
                    leagueName: league.leagueName,
                    matches: league.matches
                });
            }
        });
    }

    // Si no hay ligas con partidos programados hoy
    if (newPlaylist.length === 0) {
        newPlaylist.push({
            type: 'title',
            text: 'Sin partidos programados'
        });
    }

    playlist = newPlaylist;

    // Resetear índices de ser necesario
    if (currentPlaylistIndex >= playlist.length) {
        currentPlaylistIndex = 0;
    }

    // Comenzar el ciclo de reproducción si no está activo
    if (!playlistTimeoutId) {
        playNextItem();
    }
}

/**
 * Genera el HTML de un partido individual
 */
function createMatchHTML(match) {
    let html = `<div class="match-item">`;

    // 1. Prefijo de estado
    if (match.status === 'IN_PLAY') {
        const minStr = match.minute ? match.minute : 'En vivo';
        html += `<span class="live-tag">${minStr}</span>`;
    } else {
        // Mostrar solo la hora para partidos finalizados o programados
        html += `<span class="match-meta">${match.time}</span>`;
    }

    // 2. Escudo local
    if (match.homeCrest) {
        html += `<img class="team-crest" src="${match.homeCrest}" alt="${match.home}" onerror="if (this.src.includes('500-dark')) { this.src = this.src.replace('500-dark', '500'); } else { this.style.display = 'none'; }">`;
    }

    // 3. Sigla local (TLA)
    html += `<span class="team-code">${match.home}</span>`;

    // 4. Marcador o vs
    if (match.homeScore !== null && match.awayScore !== null) {
        if (match.homePenalties !== undefined && match.homePenalties !== null && match.awayPenalties !== undefined && match.awayPenalties !== null) {
            html += `<span class="score-display">${match.homeScore}<span class="penalty-score">(${match.homePenalties})</span><span class="score-divider">-</span>${match.awayScore}<span class="penalty-score">(${match.awayPenalties})</span></span>`;
        } else {
            html += `<span class="score-display">${match.homeScore}<span class="score-divider">-</span>${match.awayScore}</span>`;
        }
    } else {
        html += `<span class="score-display">vs</span>`;
    }

    // 5. Sigla visitante (TLA)
    html += `<span class="team-code">${match.away}</span>`;

    // 6. Escudo visitante
    if (match.awayCrest) {
        html += `<img class="team-crest" src="${match.awayCrest}" alt="${match.away}" onerror="if (this.src.includes('500-dark')) { this.src = this.src.replace('500-dark', '500'); } else { this.style.display = 'none'; }">`;
    }

    html += `</div>`;
    return html;
}

/**
 * Genera el HTML completo para una liga
 */
function createLeagueHTML(item, repeatCount = 1) {
    // Generar el HTML de la tanda de partidos
    let groupHTML = `<div class="matches-row">`;
    item.matches.forEach(match => {
        groupHTML += createMatchHTML(match);
    });
    groupHTML += `</div>`; // Cerrar matches-row

    // Construir el bloque de la liga repitiendo el grupo completo R veces
    let html = `<div class="league-block" id="league-measurer">`;
    for (let r = 0; r < repeatCount; r++) {
        html += `<div class="league-group">${groupHTML}</div>`;
    }
    html += `</div>`;
    
    // Envolver en la animación vertical de descenso
    return `
        <div class="matches-entry-wrapper animate-matches-entry">
            ${html}
        </div>
    `;
}

/**
 * Genera el HTML para la diapositiva de título de la competencia (Intro de liga)
 */
function createLeagueTitleHTML(item) {
    const hasGlow = item.leagueCrest && (item.leagueCrest.includes('/1208.png') || item.leagueCrest.includes('/2395.png'));
    const crestClass = hasGlow ? 'logo-title-crest logo-glow-fix' : 'logo-title-crest';
    const isLong = item.leagueName && item.leagueName.length > 20;
    const titleClass = isLong ? 'league-title-text league-title-long' : 'league-title-text';
    
    // El logo y el nombre de la competencia se replican 5 veces para los 4 sectores del panel LED
    const titleHTML = `
        <div class="league-title-item" style="left: -148px;">
            ${item.leagueCrest ? `<img class="${crestClass}" src="${item.leagueCrest}" onerror="this.style.display='none';">` : ''}
            <span class="${titleClass}">${item.leagueName}</span>
            ${item.leagueCrest ? `<img class="${crestClass}" src="${item.leagueCrest}" onerror="this.style.display='none';">` : ''}
        </div>
        <div class="league-title-item" style="left: 400px;">
            ${item.leagueCrest ? `<img class="${crestClass}" src="${item.leagueCrest}" onerror="this.style.display='none';">` : ''}
            <span class="${titleClass}">${item.leagueName}</span>
            ${item.leagueCrest ? `<img class="${crestClass}" src="${item.leagueCrest}" onerror="this.style.display='none';">` : ''}
        </div>
        <div class="league-title-item" style="left: 900px;">
            ${item.leagueCrest ? `<img class="${crestClass}" src="${item.leagueCrest}" onerror="this.style.display='none';">` : ''}
            <span class="${titleClass}">${item.leagueName}</span>
            ${item.leagueCrest ? `<img class="${crestClass}" src="${item.leagueCrest}" onerror="this.style.display='none';">` : ''}
        </div>
        <div class="league-title-item" style="left: 1400px;">
            ${item.leagueCrest ? `<img class="${crestClass}" src="${item.leagueCrest}" onerror="this.style.display='none';">` : ''}
            <span class="${titleClass}">${item.leagueName}</span>
            ${item.leagueCrest ? `<img class="${crestClass}" src="${item.leagueCrest}" onerror="this.style.display='none';">` : ''}
        </div>
        <div class="league-title-item" style="left: 1900px;">
            ${item.leagueCrest ? `<img class="${crestClass}" src="${item.leagueCrest}" onerror="this.style.display='none';">` : ''}
            <span class="${titleClass}">${item.leagueName}</span>
            ${item.leagueCrest ? `<img class="${crestClass}" src="${item.leagueCrest}" onerror="this.style.display='none';">` : ''}
        </div>
    `;
    
    return `
        <div class="slide-league-title">
            ${titleHTML}
        </div>
    `;
}

/**
 * Controla el ciclo de reproducción secuencial
 */
function playNextItem() {
    if (playlist.length === 0) return;

    const item = playlist[currentPlaylistIndex];

    // Limpiar clases de animación y estilos anteriores
    container1.className = 'scroll-container';
    container2.className = 'scroll-container';
    container1.style.removeProperty('--scroll-end-x');
    container2.style.removeProperty('--scroll-end-x');
    container1.style.removeProperty('--scroll-duration');
    container2.style.removeProperty('--scroll-duration');
    container1.style.removeProperty('--title-duration');
    container2.style.removeProperty('--title-duration');
    container1.style.removeProperty('--intro-duration');
    container2.style.removeProperty('--intro-duration');

    let duration = 5000; // Duración por defecto

    if (item.type === 'intros') {
        const introsHTML = `
            <div class="slide-templo">
                <div class="intro-item" style="left: -148px;">
                    <img class="logo-tdf" src="logo_tdf.png" alt="Logo TDF">
                    <span class="slide-templo-text">El Templo del Futbol</span>
                    <img class="logo-tdf" src="logo_tdf.png" alt="Logo TDF">
                </div>
                <div class="intro-item" style="left: 400px;">
                    <img class="logo-tdf" src="logo_tdf.png" alt="Logo TDF">
                    <span class="slide-templo-text">El Templo del Futbol</span>
                    <img class="logo-tdf" src="logo_tdf.png" alt="Logo TDF">
                </div>
                <div class="intro-item" style="left: 900px;">
                    <img class="logo-tdf" src="logo_tdf.png" alt="Logo TDF">
                    <span class="slide-templo-text">El Templo del Futbol</span>
                    <img class="logo-tdf" src="logo_tdf.png" alt="Logo TDF">
                </div>
                <div class="intro-item" style="left: 1400px;">
                    <img class="logo-tdf" src="logo_tdf.png" alt="Logo TDF">
                    <span class="slide-templo-text">El Templo del Futbol</span>
                    <img class="logo-tdf" src="logo_tdf.png" alt="Logo TDF">
                </div>
                <div class="intro-item" style="left: 1900px;">
                    <img class="logo-tdf" src="logo_tdf.png" alt="Logo TDF">
                    <span class="slide-templo-text">El Templo del Futbol</span>
                    <img class="logo-tdf" src="logo_tdf.png" alt="Logo TDF">
                </div>
            </div>
        `;
        container1.innerHTML = introsHTML;
        container2.innerHTML = introsHTML;

        container1.style.setProperty('--intro-duration', `${INTRO_DURATION}ms`);
        container2.style.setProperty('--intro-duration', `${INTRO_DURATION}ms`);

        // Forzar reflow
        container1.offsetHeight;

        container1.children[0].classList.add('animate-templo');
        container2.children[0].classList.add('animate-templo');

        duration = INTRO_DURATION;

    } else if (item.type === 'title') {
        const isLong = item.text.length > 20;
        const titleClass = isLong ? 'title-item title-long' : 'title-item';
        const titleHTML = `
            <div class="title-block">
                <div class="${titleClass}" style="left: -148px;">${item.text}</div>
                <div class="${titleClass}" style="left: 400px;">${item.text}</div>
                <div class="${titleClass}" style="left: 900px;">${item.text}</div>
                <div class="${titleClass}" style="left: 1400px;">${item.text}</div>
                <div class="${titleClass}" style="left: 1900px;">${item.text}</div>
            </div>
        `;
        container1.innerHTML = titleHTML;
        container2.innerHTML = titleHTML;

        container1.style.setProperty('--title-duration', `${TITLE_DURATION}ms`);
        container2.style.setProperty('--title-duration', `${TITLE_DURATION}ms`);

        // Forzar reflow
        container1.offsetHeight;

        container1.classList.add('animate-title');
        container2.classList.add('animate-title');

        duration = TITLE_DURATION;

    } else if (item.type === 'league_title') {
        const titleHTML = createLeagueTitleHTML(item);
        container1.innerHTML = titleHTML;
        container2.innerHTML = titleHTML;

        container1.style.setProperty('--intro-duration', `${INTRO_DURATION}ms`);
        container2.style.setProperty('--intro-duration', `${INTRO_DURATION}ms`);

        // Forzar reflow
        container1.offsetHeight;

        container1.children[0].classList.add('animate-templo');
        container2.children[0].classList.add('animate-templo');

        duration = INTRO_DURATION;

    } else if (item.type === 'league') {
        // 1. Renderizar inicialmente con 1 tanda para medir
        const singleHTML = createLeagueHTML(item, 1);
        container1.innerHTML = singleHTML;

        const measurer = document.getElementById('league-measurer');
        const groupEl = measurer ? measurer.querySelector('.league-group') : null;
        const groupWidth = groupEl ? groupEl.getBoundingClientRect().width : 2048;

        // Calcular duración para una única pasada completa del grupo (inicia en X:0 y va a X:-groupWidth)
        const DELAY = 2; // retraso de 2s estático
        const singlePassScrollSec = groupWidth / SPEED;
        const singlePassTotalSec = DELAY + singlePassScrollSec;

        let repeatCount = 1;
        let playDurationMs = singlePassTotalSec * 1000;
        let endX = groupWidth;
        let scrollDurationSec = singlePassScrollSec;

        console.log(`[League Debug] groupWidth=${groupWidth}px, singlePassTotalSec=${singlePassTotalSec}s`);

        if (singlePassTotalSec < 60) {
            // Duración objetivo fija de 60 segundos
            playDurationMs = 60000;
            scrollDurationSec = 60 - DELAY; // 58s de scroll activo

            // Distancia total a recorrer a 85px/s en 58s: 58 * 85 = 4930px.
            // Para que no quede pantalla en negro a la derecha al final, el ancho total
            // del contenido debe cubrir la distancia de scroll más el ancho de la pantalla (2048px).
            endX = scrollDurationSec * SPEED; // 4930px
            const minWidthNeeded = endX + 2048; // 6978px

            if (groupWidth > 50) {
                repeatCount = Math.ceil(minWidthNeeded / groupWidth);
                if (repeatCount < 1) repeatCount = 1;
            }
            console.log(`[League Debug] LOOP MODE: minWidthNeeded=${minWidthNeeded}px, repeatCount=${repeatCount}, endX=${endX}px`);

            // Renderizar repitiendo el grupo completo R veces
            const repeatedHTML = createLeagueHTML(item, repeatCount);
            container1.innerHTML = repeatedHTML;
            container2.innerHTML = repeatedHTML;
        } else {
            console.log(`[League Debug] SINGLE PASS MODE: scrollDurationSec=${scrollDurationSec}s`);
            container2.innerHTML = singleHTML;
        }

        // Configurar variables CSS para la animación de desplazamiento
        container1.style.setProperty('--scroll-end-x', `-${endX}px`);
        container2.style.setProperty('--scroll-end-x', `-${endX}px`);
        container1.style.setProperty('--scroll-duration', `${scrollDurationSec}s`);
        container2.style.setProperty('--scroll-duration', `${scrollDurationSec}s`);
        container1.style.setProperty('--scroll-delay', `${DELAY}s`);
        container2.style.setProperty('--scroll-delay', `${DELAY}s`);

        // Forzar reflow
        container1.offsetHeight;

        container1.classList.add('animate-scroll');
        container2.classList.add('animate-scroll');

        duration = playDurationMs;
    }

    // Programar la transición al siguiente item
    playlistTimeoutId = setTimeout(() => {
        currentPlaylistIndex++;

        // Si terminamos la lista de reproducción, recargamos el origen de datos para refrescar marcadores
        if (currentPlaylistIndex >= playlist.length) {
            currentPlaylistIndex = 0;
            playlistTimeoutId = null;
            loadMatchesData();
        } else {
            playNextItem();
        }
    }, duration);
}

// Iniciar aplicación al cargar el DOM
window.addEventListener('DOMContentLoaded', () => {
    loadMatchesData();
});
