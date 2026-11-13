"""Pure calculations for HU and CUN 54. No user files or UI dependencies."""
from collections import defaultdict
from datetime import date, datetime
from rules import RULES


PUBLICATIONS = {"pub_aplus", "pub_a", "pub_b", "pub_c"}
PATENTS = {"patent_pct_used", "patent_pct_registered", "patent_inapi", "patent_pct"}
HU_GRADES = ("MCB",)            # art. 7 de l'arrêté 804 : maître de conférences classe B
CUN_GRADES = ("MCA",)           # conditions CUN 54 : maître de conférences classe A
BONUS_BASE = {
    "course_english_bonus": "course_sem", "online_english_bonus": "online_subject",
    "handout_english_bonus": "handout", "ped_book_english_bonus": "ped_book",
    "pub_c_english_bonus": "pub_c", "scientific_book_english_bonus": "scientific_book",
    "chapter_english_bonus": "chapter", "conf_wos_bonus": "conf_int",
    "phd_supervision_english_bonus": "phd_supervision",
    "phd_cosupervision_english_bonus": "phd_cosupervision",
    "priority_project_bonus": "research_project",
}


def parse_date(text):
    """Accepte AAAA-MM-JJ, JJ/MM/AAAA, JJ-MM-AAAA ou JJ.MM.AAAA ; None si invalide."""
    text = str(text or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def years_as_of(start, end):
    return end.year - start.year - ((end.month, end.day) < (start.month, start.day))


def effective_years(profile):
    try:
        return max(0.0, float(str(profile.get("effective_years") or 0).replace(",", ".")))
    except (ValueError, TypeError):
        return 0.0


def thresholds(track, domain):
    """Minima chiffrés publiés (CUN 54 uniquement ; l'habilitation n'en publie pas)."""
    if track == "CUN54":
        return {"pedagogy": 80, "research": 230 if domain == "ST" else 120}
    return {}


def evaluate(profile, items, as_of=None):
    """Return score details, eligibility gates and transparent issues.

    Each publication is one item with rank, author_position, principal,
    after_phd, outside_thesis and confirmed flags. Other items may have count.
    """
    as_of = as_of or date.today()
    track = profile.get("track", "HU")
    if track not in RULES:
        raise ValueError("Parcours inconnu")
    domain = profile.get("domain", "ST")
    if domain not in ("ST", "SHS"):
        raise ValueError("Domaine inconnu")
    rules = {rule.key: rule for rule in RULES[track]}
    by_key = defaultdict(float)
    counts = defaultdict(int)
    issues = []
    rejected = {}
    item_points = {}
    seen_ids = set()

    # Annexe 804 : « Excepté la publication obligatoire, le classement des co-auteurs est pris en considération… ».
    # La publication obligatoire (auteur principal, après la thèse, hors thèse) est donc créditée à 100 %.
    mandatory = None
    if track == "HU":
        eligible = {"pub_aplus", "pub_a", "pub_b"} if domain == "ST" else PUBLICATIONS
        best = -1
        for i, it in enumerate(items):
            key = it.get("key")
            if (key in eligible and it.get("principal") and it.get("after_phd") and it.get("outside_thesis")
                    and it.get("confirmed") and it.get("author_position") in (1, 2, 3, 4) and it.get("count", 1) == 1
                    and rules[key].points > best):
                best, mandatory = rules[key].points, i
    accepted_items = []

    def reject(index, message):
        issues.append(f"Ligne {index + 1} : {message}")
        rejected[index] = message

    for index, item in enumerate(items):
        key = item.get("key")
        if key not in rules:
            reject(index, "rubrique inconnue")
            continue
        rule = rules[key]
        try:
            count = int(item.get("count", 1))
        except (TypeError, ValueError):
            count = 0
        if count < 1 or count > 1000:
            reject(index, "quantité invalide")
            continue
        if key in PUBLICATIONS and count != 1:
            reject(index, "chaque publication doit être saisie séparément")
            continue
        identifier = str(item.get("identifier") or "").strip().casefold()
        if identifier:
            # Un même article (ou brevet) ne se compte qu'une fois, quel que soit le rang saisi.
            family = "pub" if key in PUBLICATIONS else "patent" if key in PATENTS else key
            if (family, identifier) in seen_ids:
                reject(index, "référence déjà saisie")
                continue
            seen_ids.add((family, identifier))
        if key in BONUS_BASE and not any(x.get("key") == BONUS_BASE[key] for x in items):
            reject(index, "supplément sans activité de base")
            continue
        if key in PUBLICATIONS:
            if not item.get("confirmed", False):
                reject(index, "classement de la revue non confirmé")
                continue
            position = item.get("author_position")
            if position not in (1, 2, 3, 4):
                reject(index, "position d'auteur manquante")
                continue
            factor = 1 if (item.get("alphabetical", False) or index == mandatory) else (1 if position == 1 else .5 if position == 2 else .25)
            points = rule.points * factor
        elif key == "study_office":
            try:
                points = float(str(item.get("points", 0)).replace(",", "."))
            except (TypeError, ValueError):
                points = -1
            if not 0 <= points <= 10:
                reject(index, "points du bureau d'études invalides")
                continue
        else:
            points = rule.points * count
        by_key[key] += points
        counts[key] += count
        item_points[index] = points
        accepted_items.append(item)

    # A bonus is valid only up to the number of corresponding base activities.
    for bonus, base in BONUS_BASE.items():
        if bonus not in by_key:
            continue
        # Le supplément s'ajoute aux seules activités effectivement retenues (plafond de la base compris).
        base_rule = rules[base]
        effective = counts[base]
        if base_rule.cap is not None and base_rule.points > 0:
            effective = min(effective, int(base_rule.cap // base_rule.points))
        if counts[bonus] > effective:
            allowed = rules[bonus].points * effective
            by_key[bonus] = min(by_key[bonus], allowed)
            issues.append(f"{rules[bonus].label} : supplément limité aux activités de base")

    scores = {key: min(points, rules[key].cap) if rules[key].cap is not None else points
              for key, points in by_key.items()}
    capped = sorted(key for key, points in by_key.items() if rules[key].cap is not None and points > rules[key].cap)
    pedagogy = sum(value for key, value in scores.items() if rules[key].group == "Pédagogie")
    research = sum(value for key, value in scores.items() if rules[key].group == "Recherche")
    gates = {}

    if track == "HU":
        gates["grade maître de conférences classe B"] = profile.get("current_grade") in HU_GRADES
        gates["3 ans d'activité effective"] = effective_years(profile) >= 3
        phd_date = parse_date(profile.get("phd_date"))
        gates["doctorat depuis 1 an"] = bool(phd_date) and years_as_of(phd_date, as_of) >= 1
        eligible_ranks = {"pub_aplus", "pub_a", "pub_b"} if domain == "ST" else PUBLICATIONS
        gates["publication principale après thèse, hors thèse"] = any(
            x.get("key") in eligible_ranks and x.get("principal") and x.get("after_phd")
            and x.get("outside_thesis") for x in accepted_items)
        gates["même filière que le doctorat"] = bool(profile.get("same_field"))
        # The commission fixes its minimum after deliberation: no invented pass threshold.
        decision = ("Critères déclarés satisfaits ; seuil de points et décision réservés à la commission"
                    if all(gates.values()) else "Conditions de recevabilité incomplètes")
    else:
        gates["grade maître de conférences A"] = profile.get("current_grade") in CUN_GRADES
        gates["5 ans d'exercice effectif"] = effective_years(profile) >= 5
        qualifying = [x for x in accepted_items if x.get("key") in PUBLICATIONS
                      and (x.get("author_position") in (1, 2) or x.get("principal"))]
        q = defaultdict(int)
        for x in qualifying:
            q[x["key"]] += 1
        if domain == "ST":
            publication_ok = q["pub_aplus"] >= 1 or (q["pub_a"] >= 1 and q["pub_b"] >= 2)
        else:
            # Variante « deux rang C » : auteur principal exigé (la 2e position ne suffit pas).
            publication_ok = (q["pub_a"] >= 1 or (q["pub_b"] >= 1 and q["pub_c"] >= 1)
                              or sum(x.get("key") == "pub_c" and x.get("principal") for x in qualifying) >= 2)
        gates["publications minimales du domaine"] = publication_ok
        gates["encadrement soutenu requis"] = (counts["phd_supervision"] + counts["phd_cosupervision"] >= 1
                                                 or counts["magister_supervision"] >= 2
                                                 or counts["master"] + counts["startup_master"] >= 4)
        gates["80 points pédagogiques"] = pedagogy >= 80
        threshold = 230 if domain == "ST" else 120
        gates[f"{threshold} points de recherche"] = research >= threshold
        decision = ("Critères calculés satisfaits, sous réserve de vérification par la CUN"
                    if all(gates.values()) else "Critères de candidature incomplets")

    return {"track": track, "domain": domain, "pedagogy": pedagogy, "research": research,
            "total": pedagogy + research, "scores": scores, "gates": gates, "issues": issues,
            "decision": decision, "item_points": item_points, "rejected": rejected,
            "capped": capped, "mandatory": mandatory, "thresholds": thresholds(track, domain), "ok": all(gates.values())}
