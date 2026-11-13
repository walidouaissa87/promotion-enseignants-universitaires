"""Versioned scoring rules transcribed from the cited MESRS documents."""
from dataclasses import dataclass


SOURCES = {
    "HU": "Arrêté MESRS n° 804 du 14/07/2021, annexe 1 (habilitation universitaire)",
    "CUN54": "MESRS, Conditions et grille d'évaluation CUN 54, mai 2026",
}


@dataclass(frozen=True)
class Rule:
    key: str
    label: str
    group: str
    points: float
    cap: float | None = None
    detail: str = ""


def r(key, label, group, points, cap=None, detail=""):
    return Rule(key, label, group, points, cap, detail)


HU = [
    r("course_year", "Cours dispensés (année)", "Pédagogie", 15, 45),
    r("td_year", "Travaux dirigés (année)", "Pédagogie", 8, 24),
    r("tp_year", "Travaux pratiques (année)", "Pédagogie", 5, 15),
    r("online_course", "Cours en ligne validé", "Pédagogie", 15),
    r("handout", "Polycopié validé", "Pédagogie", 12, 24),
    r("ped_book", "Ouvrage pédagogique édité", "Pédagogie", 30),
    r("tutoring_year", "Tutorat attesté (année)", "Pédagogie", 3, 9),
    r("internship_year", "Suivi de stagiaires (année)", "Pédagogie", 6, 18),
    r("industry_link", "Relation université–milieu socio-économique", "Pédagogie", 5),
    r("ped_animation", "Animation pédagogique", "Pédagogie", 5),
    r("dissertation", "Mémoire encadré", "Pédagogie", 9, 27),
    r("pub_aplus", "Publication rang A+", "Recherche", 100),
    r("pub_a", "Publication rang A", "Recherche", 90),
    r("pub_b", "Publication rang B", "Recherche", 60),
    r("pub_c", "Publication rang C", "Recherche", 40, 80),
    r("patent_pct", "Brevet PCT OMPI", "Recherche", 40),
    r("patent_inapi", "Brevet INAPI", "Recherche", 20),
    r("conf_int", "Communication internationale", "Recherche", 20, 40),
    r("conf_wos_bonus", "Supplément actes WOS/Scopus", "Recherche", 5),
    r("conf_nat", "Communication nationale", "Recherche", 10, 20),
    r("phd_cosupervision", "Co-encadrement doctorat", "Recherche", 20),
    r("scientific_book", "Ouvrage scientifique édité", "Recherche", 20),
    r("doctoral_training", "Formation doctorale attestée", "Recherche", 15),
    r("event_org", "Organisation manifestation scientifique", "Recherche", 5, 10),
    r("intl_cooperation", "Coopération internationale", "Recherche", 5, 10),
    r("expertise", "Expertise scientifique", "Recherche", 5, 15),
    r("research_project", "Activité de recherche PRFU/PNR", "Recherche", 5, 10),
]

CUN54 = [
    r("course_sem", "Cours dispensés (semestre)", "Pédagogie", 6, 60),
    r("course_english_bonus", "Cours enseigné en anglais (supplément)", "Pédagogie", 10),
    r("td_sem", "TD dispensés (semestre)", "Pédagogie", 1.5, 15),
    r("tp_sem", "TP encadrés (semestre)", "Pédagogie", 1.5, 15),
    r("online_subject", "Matière en ligne validée", "Pédagogie", 30),
    r("online_english_bonus", "Matière en ligne en anglais (supplément)", "Pédagogie", 10),
    r("handout", "Polycopié validé et en ligne", "Pédagogie", 12),
    r("handout_english_bonus", "Polycopié en anglais (supplément)", "Pédagogie", 10),
    r("ped_book", "Ouvrage pédagogique", "Pédagogie", 30),
    r("ped_book_english_bonus", "Ouvrage pédagogique en anglais (supplément)", "Pédagogie", 10),
    r("tutoring_year", "Tutorat attesté (année)", "Pédagogie", 3, 15),
    r("internship_year", "Suivi de stagiaires (année)", "Pédagogie", 6, 30),
    r("industry_project", "Projet tutoré université–entreprise", "Pédagogie", 5),
    r("ped_animation", "Animation d'équipe pédagogique", "Pédagogie", 5),
    r("master", "Mémoire Master / Ingénieur", "Pédagogie", 2, 20),
    r("startup_master", "Mémoire diplôme-startup", "Pédagogie", 15, 45),
    r("english_online_year", "Dispositif d'anglais en ligne (année)", "Pédagogie", 6, 30),
    r("pub_aplus", "Publication rang A+", "Recherche", 160),
    r("pub_a", "Publication rang A", "Recherche", 80),
    r("pub_b", "Publication rang B", "Recherche", 40),
    r("pub_c", "Publication rang C", "Recherche", 20, 40),
    r("pub_c_english_bonus", "Publication C en anglais (supplément)", "Recherche", 10),
    r("scientific_book", "Ouvrage scientifique", "Recherche", 40),
    r("scientific_book_english_bonus", "Ouvrage scientifique en anglais (supplément)", "Recherche", 20),
    r("chapter", "Chapitre d'ouvrage scientifique", "Recherche", 10),
    r("chapter_english_bonus", "Chapitre en anglais (supplément)", "Recherche", 5),
    r("conf_int", "Communication internationale", "Recherche", 20, 40),
    r("conf_wos_bonus", "Actes WOS/Scopus (supplément)", "Recherche", 5),
    r("conf_nat", "Communication nationale", "Recherche", 10, 20),
    r("patent_pct_used", "Brevet PCT exploité", "Recherche", 80),
    r("patent_pct_registered", "Brevet PCT enregistré", "Recherche", 60),
    r("patent_inapi", "Brevet INAPI", "Recherche", 55),
    r("doctoral_training", "Formation doctorale attestée", "Recherche", 15),
    r("phd_supervision", "Doctorat soutenu encadré", "Recherche", 40),
    r("phd_supervision_english_bonus", "Thèse encadrée en anglais (supplément)", "Recherche", 10),
    r("phd_cosupervision", "Doctorat soutenu co-encadré", "Recherche", 15),
    r("phd_cosupervision_english_bonus", "Thèse co-encadrée en anglais (supplément)", "Recherche", 10),
    r("magister_supervision", "Magister soutenu encadré", "Recherche", 10),
    r("event_org", "Organisation manifestation scientifique", "Recherche", 5, 10),
    r("expertise", "Expertise scientifique", "Recherche", 5, 10),
    r("intl_cooperation", "Coopération internationale", "Recherche", 5, 10),
    r("research_project", "Recherche PRFU/PNR/laboratoire", "Recherche", 5, 10),
    r("priority_project_bonus", "Projet sécurité alimentaire/santé/énergie (supplément)", "Recherche", 15),
    r("five_star_student", "Formation étudiant 5 étoiles", "Recherche", 5),
    r("study_office", "Bureau d'études ou filiale", "Recherche", 0, 10, "Points à saisir selon attestation : la grille ne donne pas de taux unitaire."),
    r("startup", "Startup labellisée / projet innovant", "Recherche", 20),
    r("university_service", "Apport à la communauté universitaire", "Recherche", 5, 10),
    r("society", "Diffusion culture scientifique", "Recherche", 5, 10),
]

RULES = {"HU": HU, "CUN54": CUN54}
