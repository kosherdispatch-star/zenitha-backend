"""
zenitha_connaissance.py
────────────────────────
Charge la base de connaissance des 5 systèmes astrologiques et construit
le contexte que reçoit l'IA Zenitha pour interpréter un thème donné.

C'est la "colle" entre les calculs (Swiss Ephemeris) et l'IA :
1. Les fichiers JSON de connaissance sont chargés en mémoire
2. À partir d'un thème calculé, on extrait les fiches pertinentes
3. On assemble un contexte texte que l'IA utilise pour rédiger des réponses justes

Place les fichiers JSON de connaissance dans un dossier /connaissance/ à côté de ce fichier.
"""

import json
import os

# ── CHARGEMENT DE LA BASE ──

DOSSIER_BASE = os.path.dirname(os.path.abspath(__file__))

def _charger(nom_fichier):
    """Cherche le fichier à côté du module, ou dans un sous-dossier /connaissance/."""
    chemins = [
        os.path.join(DOSSIER_BASE, nom_fichier),
        os.path.join(DOSSIER_BASE, 'connaissance', nom_fichier),
    ]
    for chemin in chemins:
        try:
            with open(chemin, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            continue
    print(f"⚠ Fichier de connaissance introuvable : {nom_fichier}")
    return {}

# On charge tout une fois au démarrage (en mémoire)
BASE = {
    'signes':      _charger('zenitha-connaissance-occidental-signes.json'),
    'planetes':    _charger('zenitha-connaissance-occidental-planetes.json'),
    'maisons':     _charger('zenitha-connaissance-occidental-maisons.json'),
    'aspects':     _charger('zenitha-connaissance-occidental-aspects.json'),
    'numerologie': _charger('zenitha-connaissance-numerologie.json'),
    'chinoise':    _charger('zenitha-connaissance-chinoise.json'),
    'vedique':     _charger('zenitha-connaissance-vedique.json'),
    'kabbale':     _charger('zenitha-connaissance-kabbale.json'),
}

# ── HELPERS D'ACCÈS ──

def _normaliser(nom):
    """Normalise un nom de signe/nombre pour correspondre aux clés JSON."""
    if nom is None:
        return None
    return (str(nom).lower()
            .replace('é', 'e').replace('è', 'e').replace('ê', 'e')
            .replace('œ', 'oe').replace('ç', 'c').replace('â', 'a')
            .replace('î', 'i').replace('ï', 'i').replace('û', 'u')
            .replace(' ', '_').strip())

def fiche_signe(nom_signe):
    """Retourne la fiche complète d'un signe occidental."""
    cle = _normaliser(nom_signe)
    return BASE['signes'].get('signes', {}).get(cle)

def fiche_planete(nom_planete):
    cle = _normaliser(nom_planete)
    return BASE['planetes'].get('planetes', {}).get(cle)

def fiche_maison(numero):
    return BASE['maisons'].get('maisons', {}).get(str(numero))

def fiche_nombre(nombre):
    return BASE['numerologie'].get('nombres', {}).get(str(nombre))

def fiche_animal_chinois(nom_animal):
    cle = _normaliser(nom_animal)
    return BASE['chinoise'].get('signes', {}).get(cle)

def fiche_nakshatra(nom_nakshatra):
    cle = _normaliser(nom_nakshatra)
    return BASE['vedique'].get('nakshatras', {}).get('liste', {}).get(cle)

def fiche_dasha(nom_planete):
    cle = _normaliser(nom_planete)
    return BASE['vedique'].get('dashas_vimshottari', {}).get('periodes', {}).get(cle)

def fiche_sephira(nom_sephira):
    cle = _normaliser(nom_sephira)
    return BASE['kabbale'].get('sephirot', {}).get('liste', {}).get(cle)

# ── CONSTRUCTION DU CONTEXTE POUR L'IA ──

def construire_contexte(theme):
    """
    À partir d'un thème calculé (dict issu du backend Swiss Ephemeris),
    construit un contexte texte riche que l'IA Zenitha utilisera.

    'theme' attendu (exemple de structure) :
    {
      'prenom': 'Sophia',
      'occidental': {
         'soleil': {'signe': 'Poissons', ...},
         'lune': {'signe': 'Scorpion', ...},
         'ascendant': {'signe': 'Bélier', ...},
         ...
      },
      'chinois': {'animal': 'Singe', 'element': 'Métal', ...},
      'numerologie': {'chemin_vie': 7, 'annee_personnelle': 5, ...},
      'vedique': {'nakshatra': 'Uttara Bhadrapada', 'dasha': 'Venus', ...},
      'kabbale': {'sephira': 'Binah'}
    }
    """
    lignes = []
    prenom = theme.get('prenom', 'cette personne')

    lignes.append(f"═══ CONNAISSANCE ASTROLOGIQUE POUR {prenom.upper()} ═══")
    lignes.append("Utilise ces fiches pour interpréter avec justesse. Ne récite pas les fiches — intègre-les dans une lecture vivante et personnelle.\n")

    occ = theme.get('occidental', {})

    # ── SOLEIL ──
    if 'soleil' in occ:
        s = fiche_signe(occ['soleil'].get('signe'))
        if s:
            lignes.append(f"◉ SOLEIL en {s['nom']} — {s['identite_rapide']}")
            lignes.append(f"   Fond : {s['texte_fond']}")
            lignes.append(f"   Mots-clés : {', '.join(s['mots_cles_synthese'])}\n")

    # ── LUNE ──
    if 'lune' in occ:
        s = fiche_signe(occ['lune'].get('signe'))
        if s:
            lignes.append(f"☽ LUNE en {s['nom']} (monde émotionnel) — {s['identite_rapide']}")
            lignes.append(f"   En amour : {s['en_amour']}")
            lignes.append(f"   Mots-clés : {', '.join(s['mots_cles_synthese'])}\n")

    # ── ASCENDANT ──
    if 'ascendant' in occ:
        s = fiche_signe(occ['ascendant'].get('signe'))
        if s:
            lignes.append(f"↑ ASCENDANT en {s['nom']} (image extérieure) — {s['identite_rapide']}\n")

    # ── AUTRES PLANÈTES ──
    for planete in ['mercure', 'venus', 'mars', 'jupiter', 'saturne']:
        if planete in occ:
            fp = fiche_planete(planete)
            fs = fiche_signe(occ[planete].get('signe'))
            if fp and fs:
                lignes.append(f"{fp['glyph']} {fp['nom']} en {fs['nom']} — {fp['fonction']}, coloré par : {', '.join(fs['mots_cles_synthese'])}")
    lignes.append("")

    # ── CHINOIS ──
    ch = theme.get('chinois', {})
    if ch.get('animal'):
        fa = fiche_animal_chinois(ch['animal'])
        if fa:
            lignes.append(f"龍 CHINOIS : {fa['nom']} de {ch.get('element','?')} — {fa['identite_rapide']}")
            lignes.append(f"   {fa['texte_fond']}\n")

    # ── NUMÉROLOGIE ──
    num = theme.get('numerologie', {})
    if num.get('chemin_vie'):
        fn = fiche_nombre(num['chemin_vie'])
        if fn:
            lignes.append(f"∞ CHEMIN DE VIE {num['chemin_vie']} — {fn['titre']} : {fn['chemin_de_vie']}")
    if num.get('annee_personnelle'):
        fa = fiche_nombre(num['annee_personnelle'])
        if fa:
            lignes.append(f"   Année personnelle {num['annee_personnelle']} ({fa['titre']}) : tonalité de l'année en cours — {fa['mot_cle']}\n")

    # ── VÉDIQUE ──
    ved = theme.get('vedique', {})
    if ved.get('nakshatra'):
        fnak = fiche_nakshatra(ved['nakshatra'])
        if fnak:
            lignes.append(f"ॐ NAKSHATRA : {ved['nakshatra']} — {fnak['essence']} (planète : {fnak['planete']})")
    if ved.get('dasha'):
        fd = fiche_dasha(ved['dasha'])
        if fd:
            lignes.append(f"   Dasha en cours : {ved['dasha']} — période de {fd['duree_ans']} ans axée sur : {fd['theme']}\n")

    # ── KABBALE ──
    kab = theme.get('kabbale', {})
    if kab.get('sephira'):
        fsep = fiche_sephira(kab['sephira'])
        if fsep:
            lignes.append(f"✡ SEPHIRA : {fsep['nom']} ({fsep['sens']}) — {fsep['essence']}")
            lignes.append(f"   Chemin de l'âme : {fsep['chemin_ame']}\n")

    # ── RECETTE DE SYNTHÈSE ──
    lignes.append("═══ COMMENT FUSIONNER ═══")
    lignes.append("Occidental = la personnalité. Védique = le karma et le destin. "
                  "Chinois = le tempérament de fond. Numérologie = le rythme et les cycles de vie. "
                  "Kabbale = le chemin de l'âme et la vocation profonde. "
                  "Une bonne synthèse tisse ces fils en UN portrait cohérent, sans lister — en montrant comment ils se répondent et parfois se complètent ou se tendent.")

    return "\n".join(lignes)


# ── TEST LOCAL ──
if __name__ == '__main__':
    theme_test = {
        'prenom': 'Sophia',
        'occidental': {
            'soleil': {'signe': 'Poissons'},
            'lune': {'signe': 'Scorpion'},
            'ascendant': {'signe': 'Bélier'},
            'venus': {'signe': 'Bélier'},
            'mars': {'signe': 'Capricorne'},
        },
        'chinois': {'animal': 'Singe', 'element': 'Métal'},
        'numerologie': {'chemin_vie': 7, 'annee_personnelle': 5},
        'vedique': {'nakshatra': 'Uttara Bhadrapada', 'dasha': 'Venus'},
        'kabbale': {'sephira': 'Binah'},
    }
    print(construire_contexte(theme_test))
