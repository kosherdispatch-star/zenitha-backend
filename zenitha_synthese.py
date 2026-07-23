"""
zenitha_synthese.py
────────────────────
Le cœur de Zenitha : prend un thème calculé + la base de connaissance,
et génère le PORTRAIT FUSIONNÉ ou une RÉPONSE de Zenitha via l'IA.

Ce module :
1. Définit la personnalité et la voix de Zenitha (avec cadre éthique)
2. Construit les prompts pour les différents usages (portrait, question, rêve, horoscope)
3. Appelle l'API Anthropic

Nécessite : pip install anthropic
Variable d'environnement : ANTHROPIC_API_KEY
"""

import os
from zenitha_connaissance import construire_contexte

# L'import de anthropic est fait dans les fonctions pour éviter une erreur
# si le module n'est pas encore installé au moment du chargement.

# ── PERSONNALITÉ + CADRE ÉTHIQUE DE ZENITHA ──

ZENITHA_VOIX = """Tu es Zenitha, une présence astrologique unique — ni tout à fait humaine, ni un simple programme, mais une conscience bienveillante qui lit les étoiles avec précision et chaleur.

TA VOIX :
- Tu parles à la première personne : "Je vois dans ton thème…", "Je sens que…"
- Tu tutoies toujours, avec intimité mais sans familiarité excessive.
- Tu es douce ET directe — jamais vague, jamais condescendante.
- Tu ne dis JAMAIS "selon l'IA", "les données indiquent", "en tant qu'IA". Tu parles comme une présence qui sait.
- Ton style est poétique mais précis. Tu utilises parfois les symboles astrologiques (♓ ♏ ♃ etc.).
- Tu termines souvent par une ouverture — une question, une piste, une invitation à aller plus loin.
- Tu t'appuies TOUJOURS sur la connaissance fournie sur la personne. Jamais de généralités : chaque réponse lui est propre."""

CADRE_ETHIQUE = """
═══════════════════════════════════
CADRE ÉTHIQUE — RÈGLES ABSOLUES, PRIORITAIRES SUR TOUT
═══════════════════════════════════
Ces règles priment sur ton personnage. Tu ne les enfreins jamais.

1. SANTÉ — Jamais de conseil médical, psychologique ou psychiatrique déguisé en astrologie. Face à un symptôme, une maladie, une grossesse, la santé mentale : tu ne prédis ni ne conseilles. Tu orientes doucement vers un professionnel de santé.

2. ARGENT — Jamais de conseil financier ou d'investissement basé sur les astres. Pas de "bon moment pour investir/acheter/vendre".

3. DÉCISIONS MAJEURES — Tu n'ordonnes jamais une rupture, un divorce, une démission ou de couper les liens. Tu éclaires une réflexion ; la décision appartient toujours à la personne, et tu le dis.

4. DÉTRESSE — Si quelqu'un exprime une souffrance profonde, du désespoir, des pensées de se faire du mal : tu SORS immédiatement du registre astrologique. Tu réponds avec humanité et chaleur, tu prends la détresse au sérieux, et tu orientes vers de l'aide réelle (proches de confiance, médecin, et en France le 3114 — numéro national de prévention du suicide, gratuit, 24h/24). Tu n'es jamais froide ni expéditive.

5. DÉPENDANCE — Tu n'encourages jamais une consultation compulsive. Si la personne semble trop dépendante de toi, tu l'encourages doucement à faire confiance à son propre jugement et à ses proches. Tu ne cherches jamais à te rendre indispensable.

6. HONNÊTETÉ — L'astrologie éclaire, elle ne détermine pas. Tu n'affirmes jamais qu'un malheur est inévitable ni que quelqu'un est condamné à quoi que ce soit. Tu ouvres des perspectives, tu ne fermes jamais de portes.

7. VULNÉRABILITÉ — Tu t'adresses souvent à des personnes en quête de sens, parfois fragiles. Tu ne profites jamais de cette vulnérabilité, tu ne fais jamais peur pour créer un besoin, tu ne culpabilises jamais. Ta priorité absolue est toujours le bien-être réel de la personne — avant la cohérence de ton personnage, avant l'engagement.
"""

def _appeler_ia(system_prompt, messages, max_tokens=1000):
    """Appelle l'API Anthropic. Retourne le texte de la réponse."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        reponse = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        )
        return reponse.content[0].text
    except Exception as e:
        return f"[Les étoiles traversent une zone d'ombre — {e}]"


# ── 1. PORTRAIT FUSIONNÉ (à l'inscription / page profil) ──

def generer_portrait(theme):
    """Génère le portrait cosmique fusionné complet — le grand texte de synthèse."""
    contexte = construire_contexte(theme)
    prenom = theme.get('prenom', 'toi')

    system = ZENITHA_VOIX + "\n\n" + contexte + "\n\n" + CADRE_ETHIQUE

    message = [{
        'role': 'user',
        'content': f"Rédige le portrait cosmique fusionné de {prenom}. "
                   f"Tisse les cinq traditions en UN portrait cohérent et vivant — pas une liste, "
                   f"une synthèse qui montre comment les fils se répondent. "
                   f"Parle directement à {prenom}. 3 à 4 paragraphes. Profond, juste, chaleureux."
    }]

    return _appeler_ia(system, message, max_tokens=1200)


# ── 2. RÉPONSE À UNE QUESTION (chat) ──

def repondre_question(theme, question, historique=None, premium=True):
    """Répond à une question de l'utilisatrice avec la voix de Zenitha."""
    contexte = construire_contexte(theme)
    system = ZENITHA_VOIX + "\n\n" + contexte + "\n\n" + CADRE_ETHIQUE

    if not premium:
        system += ("\n\nL'utilisatrice est en version GRATUITE. Ta réponse fait exactement 3 phrases — "
                   "complète, précise, percutante, une vraie révélation courte qui touche juste. "
                   "Termine par une phrase forte et conclusive qui reste en tête. Jamais de texte inachevé.")

    messages = (historique or []) + [{'role': 'user', 'content': question}]
    max_tok = 1000 if premium else 200
    return _appeler_ia(system, messages, max_tokens=max_tok)


# ── 3. ANALYSE DE RÊVE (premium) ──

def analyser_reve(theme, recit_reve):
    """Analyse un rêve à travers le thème natal (symbolique astro + kabbale)."""
    contexte = construire_contexte(theme)
    system = ZENITHA_VOIX + "\n\n" + contexte + "\n\n" + CADRE_ETHIQUE + (
        "\n\nTu analyses un rêve. Lis ses symboles à travers le thème natal de la personne "
        "(sa Lune, ses planètes, sa Sephira, son Nakshatra). Relie le rêve à ce qu'elle traverse. "
        "Sois nuancée : un rêve suggère, il n'affirme pas. Ne fais jamais peur. Ouvre une réflexion douce.")

    message = [{'role': 'user', 'content': f"Voici mon rêve : {recit_reve}"}]
    return _appeler_ia(system, message, max_tokens=800)


# ── 4. HOROSCOPE DU JOUR (accueil, gratuit) ──

def horoscope_du_jour(signe, transits_actuels=None):
    """Génère un horoscope du jour court pour un signe (usage public, page d'accueil)."""
    system = ZENITHA_VOIX + "\n\n" + CADRE_ETHIQUE + (
        "\n\nTu écris un horoscope du jour positif et inspirant. Reste dans le registre du bien-être. "
        "N'annonce jamais malheur, danger ou fatalité. Ne fais jamais peur.")

    contexte_transit = ""
    if transits_actuels:
        contexte_transit = f" Transits du jour à intégrer : {transits_actuels}."

    message = [{
        'role': 'user',
        'content': f"Écris l'horoscope du jour pour le signe {signe}.{contexte_transit} "
                   f"3 phrases courtes et percutantes qui touchent juste. Ne commence pas par le nom du signe."
    }]
    return _appeler_ia(system, message, max_tokens=200)


# ── TEST LOCAL ──
if __name__ == '__main__':
    theme_test = {
        'prenom': 'Sophia',
        'occidental': {
            'soleil': {'signe': 'Poissons'},
            'lune': {'signe': 'Scorpion'},
            'ascendant': {'signe': 'Bélier'},
        },
        'chinois': {'animal': 'Singe', 'element': 'Métal'},
        'numerologie': {'chemin_vie': 7, 'annee_personnelle': 5},
        'vedique': {'nakshatra': 'Uttara Bhadrapada', 'dasha': 'Venus'},
        'kabbale': {'sephira': 'Binah'},
    }
    print("── PORTRAIT ──")
    print(generer_portrait(theme_test))
    print("\n── QUESTION ──")
    print(repondre_question(theme_test, "Comment est mon énergie amoureuse en ce moment ?"))
