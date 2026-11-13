import unittest
from datetime import date

from engine import evaluate, parse_years


def hu_pub(key="pub_a", position=1, **extra):
    item = {"key": key, "count": 1, "author_position": position, "principal": True, "after_phd": True,
            "outside_thesis": True, "confirmed": True}
    item.update(extra)
    return item


HU_PROFILE = {"track": "HU", "domain": "ST", "current_grade": "MCB", "effective_years": "3",
              "phd_date": "2023-01-01", "same_field": True}
TEACHING = {"key": "course_year", "count": 1}


class PromotionRulesTests(unittest.TestCase):
    def test_hu_requirements_and_mandatory_publication(self):
        result = evaluate(HU_PROFILE, [hu_pub(position=2), TEACHING], date(2026, 11, 13))
        self.assertEqual(result["research"], 90)      # publication obligatoire : 100 %
        self.assertEqual(result["mandatory"], 0)
        self.assertTrue(all(result["gates"].values()))
        self.assertIn("commission", result["decision"])
        self.assertIn("vérification officielle", result["decision"])

    def test_hu_requires_declared_teaching_experience(self):
        result = evaluate(HU_PROFILE, [hu_pub()], date(2026, 11, 13))
        self.assertFalse(result["ok"])
        self.assertFalse(result["gates"]["expérience d'enseignement déclarée (cours, polycopié, encadrement)"])

    def test_cun_gates_cannot_be_replaced_by_total(self):
        profile = {"track": "CUN54", "domain": "ST", "current_grade": "MCA", "effective_years": "5"}
        items = [{"key": "pub_aplus", "count": 1, "author_position": 1, "principal": True, "confirmed": True},
                 {"key": "course_sem", "count": 10}, {"key": "phd_supervision", "count": 1}]
        result = evaluate(profile, items)
        self.assertEqual(result["pedagogy"], 60)
        self.assertFalse(result["gates"]["80 points pédagogiques"])
        self.assertFalse(result["gates"]["230 points de recherche"])

    def test_shs_c_publications_and_duplicate_patent(self):
        profile = {"track": "CUN54", "domain": "SHS", "current_grade": "MCA", "effective_years": "5"}
        pubs = [{"key": "pub_c", "count": 1, "author_position": 1, "principal": True, "confirmed": True,
                 "identifier": f"doi:{i}", "journal": f"Revue {i}", "issue": f"N°{i}"} for i in range(2)]
        patents = [{"key": "patent_pct_registered", "identifier": "P1"}, {"key": "patent_inapi", "identifier": "P1"}]
        result = evaluate(profile, pubs + patents)
        self.assertTrue(result["gates"]["publications minimales du domaine"])
        self.assertEqual(result["scores"]["pub_c"], 40)
        self.assertEqual(result["scores"]["patent_pct_registered"], 60)
        self.assertNotIn("patent_inapi", result["scores"])
        self.assertTrue(any("déjà" in issue for issue in result["issues"]))

    def test_shs_two_c_same_journal_rejected(self):
        profile = {"track": "CUN54", "domain": "SHS", "current_grade": "MCA", "effective_years": "5"}
        pubs = [{"key": "pub_c", "count": 1, "author_position": 1, "principal": True, "confirmed": True,
                 "identifier": f"doi:{i}", "journal": "Même Revue", "issue": "N°1"} for i in range(2)]
        result = evaluate(profile, pubs)
        self.assertFalse(result["gates"]["publications minimales du domaine"])
        self.assertEqual(result["scores"]["pub_c"], 20)
        self.assertIn(1, result["rejected"])

    def test_shs_two_c_without_journal_not_enough(self):
        profile = {"track": "CUN54", "domain": "SHS", "current_grade": "MCA", "effective_years": "5"}
        pubs = [{"key": "pub_c", "count": 1, "author_position": 1, "principal": True, "confirmed": True,
                 "identifier": f"doi:{i}"} for i in range(2)]
        self.assertFalse(evaluate(profile, pubs)["gates"]["publications minimales du domaine"])

    def test_duplicate_article_does_not_steal_mandatory_status(self):
        base = {"identifier": "10.1/abc"}
        items = [hu_pub("pub_b", 2, **base), hu_pub("pub_a", 1, **base), TEACHING]
        result = evaluate(HU_PROFILE, items, date(2026, 11, 13))
        self.assertEqual(result["mandatory"], 0)      # la ligne B acceptée, pas le doublon A rejeté
        self.assertEqual(result["research"], 60)      # B à 100 % (publication obligatoire)
        self.assertIn(1, result["rejected"])

    def test_effective_years_rejects_inf_nan_and_huge(self):
        for bad in ("inf", "-inf", "nan", "1e309", "99999", "-3", "abc"):
            self.assertIsNone(parse_years(bad), bad)
        profile = {"track": "CUN54", "domain": "ST", "current_grade": "MCA", "effective_years": "inf"}
        result = evaluate(profile, [])
        self.assertFalse(result["gates"]["5 ans d'exercice effectif comme MCA"])
        self.assertTrue(any("invalide" in issue for issue in result["issues"]))
        self.assertEqual(parse_years("3,5"), 3.5)

    def test_cun_seniority_uses_grade_date_and_closing_date(self):
        profile = {"track": "CUN54", "domain": "ST", "current_grade": "MCA", "effective_years": "6",
                   "grade_date": "2021-09-01", "closing_date": "2026-06-18"}
        self.assertFalse(evaluate(profile, [])["gates"]["5 ans d'exercice effectif comme MCA"])  # 4 ans 9 mois
        profile["closing_date"] = "2026-09-01"
        self.assertTrue(evaluate(profile, [])["gates"]["5 ans d'exercice effectif comme MCA"])

    def test_hu_alphabetical_order_is_not_automatic_100_percent(self):
        items = [hu_pub("pub_a", 1, identifier="m"), hu_pub("pub_b", 3, identifier="x", alphabetical=True, principal=False), TEACHING]
        result = evaluate(HU_PROFILE, items, date(2026, 11, 13))
        self.assertEqual(result["scores"]["pub_b"], 15)   # 60 x 25 %, position à justifier
        self.assertTrue(any("alphabétique" in i for i in result["issues"]))
        cun = {"track": "CUN54", "domain": "ST", "current_grade": "MCA"}
        item = {"key": "pub_b", "count": 1, "author_position": 3, "confirmed": True, "alphabetical": True}
        self.assertEqual(evaluate(cun, [item])["scores"]["pub_b"], 40)  # CUN 54 : 100 % pour tous

    def test_same_article_not_counted_twice_across_ranks(self):
        profile = dict(HU_PROFILE, effective_years="3,5", phd_date="01/01/2020")
        base = {"identifier": "10.1/abc"}
        result = evaluate(profile, [hu_pub("pub_a", **base), hu_pub("pub_b", **base), TEACHING], date(2026, 11, 13))
        self.assertEqual(result["research"], 90)
        self.assertIn(1, result["rejected"])
        self.assertTrue(all(result["gates"].values()))

    def test_hu_caps_and_unconfirmed_publication(self):
        profile = {"track": "HU", "domain": "ST", "current_grade": "MCB"}
        items = [{"key": "course_year", "count": 5}, {"key": "pub_a", "author_position": 1, "principal": True}]
        result = evaluate(profile, items)
        self.assertEqual(result["pedagogy"], 45)
        self.assertEqual(result["research"], 0)
        self.assertEqual(result["capped"], ["course_year"])

    def test_hu_only_mandatory_publication_is_exempt_from_coauthor_rank(self):
        items = [hu_pub("pub_b", 2, identifier="a"), hu_pub("pub_a", 2, identifier="b")]
        result = evaluate({"track": "HU", "domain": "ST", "current_grade": "MCB"}, items)
        self.assertEqual(result["mandatory"], 1)
        self.assertEqual(result["research"], 90 + 30)

    def test_english_bonus_limited_to_counted_activities(self):
        profile = {"track": "CUN54", "domain": "SHS", "current_grade": "MCA"}
        pubs = [{"key": "pub_c", "author_position": 1, "principal": True, "confirmed": True,
                 "identifier": f"d{i}", "journal": f"R{i}"} for i in range(3)]
        result = evaluate(profile, pubs + [{"key": "pub_c_english_bonus", "count": 3}])
        self.assertEqual(result["scores"]["pub_c"], 40)
        self.assertEqual(result["scores"]["pub_c_english_bonus"], 20)


if __name__ == "__main__":
    unittest.main()
