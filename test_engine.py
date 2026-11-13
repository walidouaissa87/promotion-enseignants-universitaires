import unittest
from datetime import date

from engine import evaluate


class PromotionRulesTests(unittest.TestCase):
    def test_hu_requirements_and_publication_position(self):
        profile = {"track": "HU", "domain": "ST", "current_grade": "MCB",
                   "effective_years": "3", "phd_date": "2023-01-01", "same_field": True}
        item = {"key": "pub_a", "count": 1, "author_position": 2, "principal": True,
                "after_phd": True, "outside_thesis": True, "confirmed": True}
        result = evaluate(profile, [item], date(2026, 11, 13))
        self.assertEqual(result["research"], 90)  # publication obligatoire : 100 %
        self.assertEqual(result["mandatory"], 0)
        self.assertTrue(all(result["gates"].values()))
        self.assertIn("commission", result["decision"])

    def test_cun_gates_cannot_be_replaced_by_total(self):
        profile = {"track": "CUN54", "domain": "ST", "current_grade": "MCA",
                   "effective_years": "5"}
        items = [{"key": "pub_aplus", "count": 1, "author_position": 1,
                  "principal": True, "confirmed": True},
                 {"key": "course_sem", "count": 10},
                 {"key": "phd_supervision", "count": 1}]
        result = evaluate(profile, items)
        self.assertEqual(result["pedagogy"], 60)
        self.assertFalse(result["gates"]["80 points pédagogiques"])
        self.assertFalse(result["gates"]["230 points de recherche"])

    def test_shs_c_publications_and_duplicate_patent(self):
        profile = {"track": "CUN54", "domain": "SHS", "current_grade": "MCA",
                   "effective_years": "5"}
        pubs = [{"key": "pub_c", "count": 1, "author_position": 1,
                 "principal": True, "confirmed": True, "identifier": f"doi:{i}"} for i in range(2)]
        patents = [{"key": "patent_pct_registered", "identifier": "P1"},
                   {"key": "patent_inapi", "identifier": "P1"}]
        result = evaluate(profile, pubs + patents)
        self.assertTrue(result["gates"]["publications minimales du domaine"])
        self.assertEqual(result["scores"]["pub_c"], 40)
        self.assertEqual(result["scores"]["patent_pct_registered"], 60)
        self.assertNotIn("patent_inapi", result["scores"])
        self.assertTrue(any("déjà" in issue for issue in result["issues"]))

    def test_same_article_not_counted_twice_across_ranks(self):
        profile = {"track": "HU", "domain": "ST", "current_grade": "MCB", "effective_years": "3,5",
                   "phd_date": "01/01/2020", "same_field": True}
        base = {"count": 1, "author_position": 1, "principal": True, "after_phd": True,
                "outside_thesis": True, "confirmed": True, "identifier": "10.1/abc"}
        result = evaluate(profile, [dict(base, key="pub_a"), dict(base, key="pub_b")], date(2026, 11, 13))
        self.assertEqual(result["research"], 90)
        self.assertIn(1, result["rejected"])
        self.assertTrue(all(result["gates"].values()))  # MCB, 3,5 ans, date JJ/MM/AAAA acceptés

    def test_hu_caps_and_unconfirmed_publication(self):
        profile = {"track": "HU", "domain": "ST", "current_grade": "MCB"}
        items = [{"key": "course_year", "count": 5}, {"key": "pub_a", "author_position": 1, "principal": True}]
        result = evaluate(profile, items)
        self.assertEqual(result["pedagogy"], 45)       # 5 x 15 plafonné à 45
        self.assertEqual(result["research"], 0)        # classement non confirmé
        self.assertEqual(result["capped"], ["course_year"])

    def test_hu_only_mandatory_publication_is_exempt_from_coauthor_rank(self):
        profile = {"track": "HU", "domain": "ST", "current_grade": "MCB"}
        base = {"count": 1, "after_phd": True, "outside_thesis": True, "confirmed": True, "principal": True}
        items = [dict(base, key="pub_b", author_position=2, identifier="a"),
                 dict(base, key="pub_a", author_position=2, identifier="b")]
        result = evaluate(profile, items)
        self.assertEqual(result["mandatory"], 1)       # la mieux notée (rang A)
        self.assertEqual(result["research"], 90 + 30)  # A à 100 % + B à 50 %

    def test_english_bonus_limited_to_counted_activities(self):
        profile = {"track": "CUN54", "domain": "SHS", "current_grade": "MCA"}
        pubs = [{"key": "pub_c", "author_position": 1, "principal": True, "confirmed": True, "identifier": f"d{i}"} for i in range(3)]
        result = evaluate(profile, pubs + [{"key": "pub_c_english_bonus", "count": 3}])
        self.assertEqual(result["scores"]["pub_c"], 40)                # plafond 2 x 20
        self.assertEqual(result["scores"]["pub_c_english_bonus"], 20)  # 2 publications retenues x 10


if __name__ == "__main__":
    unittest.main()
