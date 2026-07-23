from flask import Flask, request, jsonify
from flask_cors import CORS
import swisseph as swe
from datetime import datetime
import math

# Mode Moshier : calcul analytique interne, sans fichiers d'éphémérides externes.
# Précision largement suffisante pour l'astrologie (écart < 1 seconde d'arc).
FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED

app = Flask(__name__)
CORS(app)

# Import des modules de connaissance et synthèse Zenitha (IA)
try:
    from zenitha_synthese import generer_portrait, repondre_question, analyser_reve, horoscope_du_jour
    IA_DISPONIBLE = True
except Exception as e:
    print(f"⚠ Modules IA non chargés : {e}")
    IA_DISPONIBLE = False

# Planètes à calculer
PLANETS = {
    'soleil':   swe.SUN,
    'lune':     swe.MOON,
    'mercure':  swe.MERCURY,
    'venus':    swe.VENUS,
    'mars':     swe.MARS,
    'jupiter':  swe.JUPITER,
    'saturne':  swe.SATURN,
    'uranus':   swe.URANUS,
    'neptune':  swe.NEPTUNE,
    'pluton':   swe.PLUTO,
}

SIGNES = [
    'Bélier','Taureau','Gémeaux','Cancer','Lion','Vierge',
    'Balance','Scorpion','Sagittaire','Capricorne','Verseau','Poissons'
]

GLYPHES = ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓']

MAISONS = [
    'Identité','Argent','Communication','Foyer','Créativité','Santé',
    'Relations','Transformation','Philosophie','Carrière','Amis','Spiritualité'
]

def degre_en_signe(degre):
    """Convertit un degré écliptique en signe et position"""
    signe_idx = int(degre / 30) % 12
    degre_dans_signe = degre % 30
    minutes = int((degre_dans_signe % 1) * 60)
    return {
        'signe': SIGNES[signe_idx],
        'glyph': GLYPHES[signe_idx],
        'longitude': round(degre, 4),
        'degre': f"{int(degre_dans_signe)}°{minutes:02d}'",
        'signe_idx': signe_idx
    }

def date_en_julien(annee, mois, jour, heure, minute, timezone_offset=0):
    """Convertit une date en jour julien"""
    heure_utc = heure - timezone_offset + minute / 60.0
    return swe.julday(annee, mois, jour, heure_utc)

def calculer_theme(annee, mois, jour, heure, minute, latitude, longitude, timezone_offset=1):
    """Calcule le thème astral complet"""
    jd = date_en_julien(annee, mois, jour, heure, minute, timezone_offset)

    # Positions planétaires
    positions = {}
    for nom, code in PLANETS.items():
        pos, _ = swe.calc_ut(jd, code, FLAGS)
        info = degre_en_signe(pos[0])
        positions[nom] = {
            **info,
            'longitude': round(pos[0], 4),
            'vitesse': round(pos[3], 4),
            'retrograde': pos[3] < 0
        }

    # Maisons et ascendant
    try:
        maisons, ascmc = swe.houses(jd, latitude, longitude, b'P')
        ascendant = degre_en_signe(ascmc[0])
        mc = degre_en_signe(ascmc[1])

        maisons_liste = []
        for i, m in enumerate(maisons):
            info = degre_en_signe(m)
            maisons_liste.append({
                'maison': i + 1,
                'domaine': MAISONS[i],
                **info
            })
    except:
        ascendant = {'signe': 'Inconnu', 'glyph': '?', 'degre': '0°00\''}
        mc = {'signe': 'Inconnu', 'glyph': '?', 'degre': '0°00\''}
        maisons_liste = []

    # Nœuds lunaires
    try:
        noeud, _ = swe.calc_ut(jd, swe.TRUE_NODE, FLAGS)
        noeud_nord = degre_en_signe(noeud[0])
        noeud_sud = degre_en_signe((noeud[0] + 180) % 360)
    except Exception:
        noeud_nord = None
        noeud_sud = None

    # Chiron — nécessite les fichiers d'éphémérides, donc optionnel
    try:
        chiron, _ = swe.calc_ut(jd, swe.CHIRON, FLAGS)
        chiron_pos = degre_en_signe(chiron[0])
    except Exception:
        chiron_pos = None

    return {
        'planetes': positions,
        'ascendant': ascendant,
        'mc': mc,
        'maisons': maisons_liste,
        'noeud_nord': noeud_nord,
        'noeud_sud': noeud_sud,
        'chiron': chiron_pos,
        'jour_julien': jd
    }

def calculer_signe_chinois(annee):
    """Calcule le signe chinois"""
    animaux = ['Rat','Bœuf','Tigre','Lapin','Dragon','Serpent',
               'Cheval','Chèvre','Singe','Coq','Chien','Cochon']
    elements = ['Métal','Eau','Bois','Feu','Terre']
    polarites = ['Yang','Yin']

    animal_idx = (annee - 4) % 12
    element_idx = math.floor((annee - 4) / 2) % 5
    polarite_idx = (annee - 4) % 2

    return {
        'animal': animaux[animal_idx],
        'element': elements[element_idx],
        'polarite': polarites[polarite_idx],
        'annee_cycle': (annee - 4) % 60 + 1
    }

def calculer_numerologie(jour, mois, annee):
    """Calcule les nombres numérologique"""
    def reduire(n):
        while n > 9 and n not in [11, 22, 33]:
            n = sum(int(d) for d in str(n))
        return n

    chemins = {
        1:'Le Pionnier', 2:'Le Médiateur', 3:'Le Créateur',
        4:'Le Bâtisseur', 5:"L'Aventurier", 6:'Le Protecteur',
        7:"L'Analyste", 8:"L'Ambitieux", 9:'Le Sage',
        11:"L'Illuminé", 22:'Le Maître Bâtisseur', 33:'Le Maître Enseignant'
    }

    total = sum(int(d) for d in f"{jour:02d}{mois:02d}{annee}")
    chemin = reduire(total)

    annee_actuelle = datetime.now().year
    total_annee = sum(int(d) for d in f"{jour:02d}{mois:02d}{annee_actuelle}")
    annee_perso = reduire(total_annee)

    return {
        'chemin_vie': chemin,
        'chemin_nom': chemins.get(chemin, 'Le Voyageur'),
        'annee_personnelle': annee_perso,
        'annee_nom': chemins.get(annee_perso, 'Le Voyageur')
    }

def calculer_nakshatra(lune_longitude):
    """Calcule le nakshatra védique"""
    nakshatras = [
        'Ashwini','Bharani','Krittika','Rohini','Mrigashira','Ardra',
        'Punarvasu','Pushya','Ashlesha','Magha','Purva Phalguni','Uttara Phalguni',
        'Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha',
        'Mula','Purva Ashadha','Uttara Ashadha','Shravana','Dhanishtha',
        'Shatabhisha','Purva Bhadrapada','Uttara Bhadrapada','Revati'
    ]
    # Ayanamsa Lahiri pour système védique
    ayanamsa = 23.85
    lune_vedique = (lune_longitude - ayanamsa) % 360
    nakshatra_idx = int(lune_vedique / (360/27))
    pada = int((lune_vedique % (360/27)) / (360/27/4)) + 1

    return {
        'nakshatra': nakshatras[nakshatra_idx % 27],
        'pada': pada,
        'longitude_vedique': round(lune_vedique, 4)
    }

def calculer_sephira(soleil_signe_idx, lune_signe_idx):
    """Calcule la Sephira kabbalistique dominante"""
    sephirot = [
        {'nom': 'Kether', 'sens': 'La Couronne', 'planete': 'Neptune'},
        {'nom': 'Chokmah', 'sens': 'La Sagesse', 'planete': 'Uranus'},
        {'nom': 'Binah', 'sens': 'La Compréhension', 'planete': 'Saturne'},
        {'nom': 'Chesed', 'sens': 'La Miséricorde', 'planete': 'Jupiter'},
        {'nom': 'Geburah', 'sens': 'La Force', 'planete': 'Mars'},
        {'nom': 'Tiphareth', 'sens': 'La Beauté', 'planete': 'Soleil'},
        {'nom': 'Netzach', 'sens': 'La Victoire', 'planete': 'Vénus'},
        {'nom': 'Hod', 'sens': 'La Gloire', 'planete': 'Mercure'},
        {'nom': 'Yesod', 'sens': 'Le Fondement', 'planete': 'Lune'},
        {'nom': 'Malkuth', 'sens': 'Le Royaume', 'planete': 'Terre'},
    ]
    idx = (soleil_signe_idx + lune_signe_idx) % 10
    return sephirot[idx]

# ── ROUTES ──

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'Zenitha Astro API'})

@app.route('/theme', methods=['POST'])
def theme():
    """Calcule le thème astral complet"""
    data = request.json

    try:
        annee = int(data['annee'])
        mois = int(data['mois'])
        jour = int(data['jour'])
        heure = int(data.get('heure', 12))
        minute = int(data.get('minute', 0))
        latitude = float(data.get('latitude', 48.8566))
        longitude = float(data.get('longitude', 2.3522))
        timezone = float(data.get('timezone', 1))

        theme = calculer_theme(annee, mois, jour, heure, minute, latitude, longitude, timezone)
        chinois = calculer_signe_chinois(annee)
        numero = calculer_numerologie(jour, mois, annee)
        nakshatra = calculer_nakshatra(theme['planetes']['lune']['longitude'])

        soleil_idx = theme['planetes']['soleil']['signe_idx']
        lune_idx = theme['planetes']['lune']['signe_idx']
        sephira = calculer_sephira(soleil_idx, lune_idx)

        return jsonify({
            'success': True,
            'occidental': {
                'soleil': theme['planetes']['soleil'],
                'lune': theme['planetes']['lune'],
                'ascendant': theme['ascendant'],
                'mercure': theme['planetes']['mercure'],
                'venus': theme['planetes']['venus'],
                'mars': theme['planetes']['mars'],
                'jupiter': theme['planetes']['jupiter'],
                'saturne': theme['planetes']['saturne'],
                'uranus': theme['planetes']['uranus'],
                'neptune': theme['planetes']['neptune'],
                'pluton': theme['planetes']['pluton'],
                'chiron': theme['chiron'],
                'noeud_nord': theme['noeud_nord'],
                'mc': theme['mc'],
                'maisons': theme['maisons'],
            },
            'chinois': chinois,
            'numerologie': numero,
            'vedique': nakshatra,
            'kabbale': sephira,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/transits', methods=['POST'])
def transits():
    """Calcule les transits actuels"""
    data = request.json

    try:
        now = datetime.utcnow()
        jd_now = swe.julday(now.year, now.month, now.day,
                            now.hour + now.minute/60.0)

        positions_actuelles = {}
        for nom, code in PLANETS.items():
            pos, _ = swe.calc_ut(jd_now, code, FLAGS)
            info = degre_en_signe(pos[0])
            positions_actuelles[nom] = {
                **info,
                'longitude': round(pos[0], 4),
                'retrograde': pos[3] < 0
            }

        # Comparer avec positions natales si fournies
        transits_list = []
        if 'natales' in data:
            natales = data['natales']
            aspects = [0, 60, 90, 120, 150, 180]
            noms_aspects = ['Conjonction','Sextile','Carré','Trigone','Quinconce','Opposition']
            orbes = [8, 6, 7, 8, 3, 8]

            for planete_transit, pos_transit in positions_actuelles.items():
                for planete_natale, lon_natale in natales.items():
                    diff = abs(pos_transit['longitude'] - lon_natale) % 360
                    if diff > 180:
                        diff = 360 - diff

                    for i, aspect in enumerate(aspects):
                        if abs(diff - aspect) <= orbes[i]:
                            transits_list.append({
                                'planete_transit': planete_transit,
                                'planete_natale': planete_natale,
                                'aspect': noms_aspects[i],
                                'orbe': round(abs(diff - aspect), 2),
                                'exact': abs(diff - aspect) < 1,
                            })

        return jsonify({
            'success': True,
            'positions_actuelles': positions_actuelles,
            'transits': sorted(transits_list, key=lambda x: x['orbe']),
            'timestamp': now.isoformat()
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/phase-lune', methods=['GET'])
def phase_lune():
    """Calcule la phase lunaire actuelle"""
    try:
        now = datetime.utcnow()
        jd = swe.julday(now.year, now.month, now.day, now.hour)

        soleil, _ = swe.calc_ut(jd, swe.SUN, FLAGS)
        lune, _ = swe.calc_ut(jd, swe.MOON, FLAGS)

        angle = (lune[0] - soleil[0]) % 360
        illumination = (1 - math.cos(math.radians(angle))) / 2 * 100

        phases = [
            (0, 45, 'Nouvelle Lune', '🌑'),
            (45, 90, 'Premier Croissant', '🌒'),
            (90, 135, 'Premier Quartier', '🌓'),
            (135, 180, 'Lune Gibbeuse Croissante', '🌔'),
            (180, 225, 'Pleine Lune', '🌕'),
            (225, 270, 'Lune Gibbeuse Décroissante', '🌖'),
            (270, 315, 'Dernier Quartier', '🌗'),
            (315, 360, 'Dernier Croissant', '🌘'),
        ]

        phase_nom = 'Inconnue'
        phase_symbole = '🌑'
        for debut, fin, nom, symbole in phases:
            if debut <= angle < fin:
                phase_nom = nom
                phase_symbole = symbole
                break

        lune_info = degre_en_signe(lune[0])

        return jsonify({
            'success': True,
            'phase': phase_nom,
            'symbole': phase_symbole,
            'illumination': round(illumination, 1),
            'angle': round(angle, 2),
            'signe': lune_info['signe'],
            'glyph': lune_info['glyph'],
            'degre': lune_info['degre'],
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ── ROUTES IA — ZENITHA PARLE ──

@app.route('/portrait', methods=['POST'])
def portrait():
    """Génère le portrait cosmique fusionné complet (5 traditions)"""
    if not IA_DISPONIBLE:
        return jsonify({'success': False, 'error': 'Modules IA non disponibles'}), 503
    try:
        theme_data = request.json
        texte = generer_portrait(theme_data)
        return jsonify({'success': True, 'portrait': texte})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/question', methods=['POST'])
def question():
    """Zenitha répond à une question — utilisé par le chat"""
    if not IA_DISPONIBLE:
        return jsonify({'success': False, 'error': 'Modules IA non disponibles'}), 503
    try:
        data = request.json
        theme_data = data.get('theme', {})
        question_texte = data.get('question', '')
        historique = data.get('historique', [])
        premium = data.get('premium', True)

        reponse = repondre_question(theme_data, question_texte, historique, premium)
        return jsonify({'success': True, 'reponse': reponse})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/reve', methods=['POST'])
def reve():
    """Analyse un rêve à travers le thème natal"""
    if not IA_DISPONIBLE:
        return jsonify({'success': False, 'error': 'Modules IA non disponibles'}), 503
    try:
        data = request.json
        theme_data = data.get('theme', {})
        recit = data.get('recit', '')

        analyse = analyser_reve(theme_data, recit)
        return jsonify({'success': True, 'analyse': analyse})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/horoscope', methods=['POST'])
def horoscope():
    """Horoscope du jour pour un signe (usage public, page d'accueil)"""
    if not IA_DISPONIBLE:
        return jsonify({'success': False, 'error': 'Modules IA non disponibles'}), 503
    try:
        data = request.json
        signe = data.get('signe', '')
        transits_actuels = data.get('transits', None)

        texte = horoscope_du_jour(signe, transits_actuels)
        return jsonify({'success': True, 'horoscope': texte})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
