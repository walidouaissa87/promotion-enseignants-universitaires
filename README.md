# Promotion des enseignants universitaires — Algérie
### ترقية الأساتذة الجامعيين — الجزائر

> ⚠ **Outil d'aide non officiel.** Les résultats sont **indicatifs uniquement** ; la décision relève des instances compétentes (commissions régionales, CUN).
> ⚠ **أداة مساعدة غير رسمية.** النتائج **استرشادية فقط**، والقرار النهائي من اختصاص الهيئات المعنية.

Application Windows gratuite et hors ligne pour estimer et préparer un dossier de promotion :
تطبيق مجاني يعمل بدون إنترنت لتقدير وتحضير ملف الترقية:

| Parcours · المسار | Texte de référence · المرجع |
|---|---|
| Habilitation universitaire (MCB → MCA) · التأهيل الجامعي | Arrêté n° 804 du 14/07/2021 (annexe 1) · Décret exécutif n° 21-50 |
| Professeur (CUN 54) · الترقية إلى أستاذ | Conditions et grille d'évaluation CUN 54, mai 2026 |

## Fonctionnalités · المميزات
- Points, plafonds, rangs des co-auteurs (100 / 50 / 25 %), suppléments, exception de la publication obligatoire (habilitation).
- Recevabilité administrative et scientifique (ST / SHS) : ✔ / ✘ instantané.
- Aperçu puis rapport PDF coloré ; sauvegarde automatique ; import / export JSON ; agenda de dates.
- Aucune donnée n'est envoyée sur Internet. · لا تُرسل أي بيانات عبر الإنترنت.

## Vérifications intégrées · ما يتحقق منه البرنامج
- Publication obligatoire (habilitation) à 100 % ; rang C (CUN 54) : revues différentes exigées ; doublons de publications exclus.
- Ancienneté MCA à la date de clôture des candidatures ; exercice effectif borné (0–60 ans).
- Expérience d'enseignement exigée pour l'habilitation (décret 21-50, art. 3).
- Aucun seuil de points n'est inventé pour l'habilitation ; les verdicts parlent de « critères satisfaits — vérification officielle nécessaire ».

## Confidentialité · الخصوصية
Les dossiers sont enregistrés localement (`%APPDATA%\Promotion_Enseignants_Universitaires`) en JSON non chiffré ; rien n'est envoyé sur Internet. Bouton « Supprimer le dossier » + copies de sécurité (30).
تُحفظ الملفات محليًا بصيغة JSON غير مشفّرة ولا يُرسل شيء عبر الإنترنت.

## Téléchargement · التحميل
Dernière version : onglet **Releases** (fichier `.exe`, Windows).
أحدث نسخة: صفحة **Releases** (ملف exe لنظام ويندوز).

## Lancer depuis le code · التشغيل من الشيفرة
```bash
pip install -r requirements.txt
python app.py
python -m unittest -v test_engine.py   # tests
```

## Sources officielles · المراجع
Les trois documents officiels consultés sont dans [`references/`](references/).

- <https://www.mesrs.dz/wp-content/uploads/2022/02/Arrete-n-804-du-14-juil-2021-habilitation-universitaire-fr.pdf>
- <https://www.mesrs.dz/wp-content/uploads/2022/02/decres-21-50-28-01-2021-modalite-habilitation-fr.pdf>
- <https://www.mesrs.dz/wp-content/uploads/2026/05/Condition-et-Grille-devaluation-CUN-54.pdf>

L'arrêté 804 ne publie pas de seuil minimal de points pour l'habilitation : le programme n'en invente pas.
لا يحدد القرار 804 حدًا أدنى للنقاط في التأهيل، والبرنامج لا يخترع حدًا.

---
© Dr. Aissa Meflah · meflah_aissa@yahoo.fr
