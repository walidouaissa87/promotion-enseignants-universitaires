"""Assistant hors ligne pour les dossiers de promotion des enseignants universitaires (Algérie).

Réalisé par : Dr. Aissa Meflah — meflah_aissa@yahoo.fr
"""
import ctypes
import io
import json
import os
import tempfile
import tkinter as tk
import uuid
from datetime import date, datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from xml.sax.saxutils import escape

from engine import CUN_GRADES, HU_GRADES, PUBLICATIONS, evaluate, parse_date
from rules import RULES, SOURCES

try:  # netteté sur écrans haute résolution
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

APP_NAME = "Promotion des enseignants universitaires — Algérie"
APP_VERSION = "2.0"
AUTHOR = "Dr. Aissa Meflah"
EMAIL = "meflah_aissa@yahoo.fr"
DATA_DIR = Path(os.environ.get("APPDATA") or Path.home()) / "Promotion_Enseignants_Universitaires"
DOSSIERS = DATA_DIR / "dossiers"
STATE = DATA_DIR / "dernier_dossier.txt"

# Palette
NAVY, BLUE, TEAL, GREEN = "#12355b", "#1d6fb8", "#0f8f84", "#2e9e5b"
ORANGE, RED, PURPLE, GOLD = "#ef8a17", "#d64550", "#7c4dbd", "#c9951a"
SLATE, BG, CARD, TEXT, MUTED = "#5b6b7c", "#eaf0f7", "#ffffff", "#152638", "#64748b"
TRACKS = {"HU": "Habilitation universitaire  →  MCA", "CUN54": "CUN 54  →  Professeur"}
DOMAINS = {"ST": "ST — Sciences et technologie", "SHS": "SHS — Sciences humaines et sociales"}
POSITIONS = {"Auteur unique": 1, "1er auteur": 1, "2e auteur": 2, "3e auteur": 3, "4e auteur et au-delà": 4}
THEMES = {
    "CUN54": dict(bg="#c08d0c", fg="#2b1d00", g1=NAVY, g2="#8a5a00", title="PROFESSEUR", tcolor="#fff0a8",
                  sub="Promotion au grade de Professeur  ·  conditions et grille CUN 54"),
    "HU": dict(bg="#1f7f74", fg="#ffffff", g1=NAVY, g2="#0f8f84", title="MAÎTRE DE CONFÉRENCES CLASSE A", tcolor="#ffe9b0",
               sub="Habilitation universitaire  ·  MCA  ·  arrêté 804 du 14/07/2021"),
}
K = 1.0  # facteur d'échelle écran (défini au démarrage)


def S(value):
    return int(round(value * K))


def shade(color, amount):
    """Éclaircit (amount > 0) ou assombrit (amount < 0) une couleur #rrggbb."""
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    f = (lambda c: int(c + (255 - c) * amount)) if amount > 0 else (lambda c: int(c * (1 + amount)))
    return "#%02x%02x%02x" % (f(r), f(g), f(b))


def key_of(mapping, text, default):
    return next((k for k, v in mapping.items() if v == text), default)


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        tmp = Path(handle.name)
        handle.write(content)
    os.replace(tmp, path)


def fmt(value):
    return f"{value:g}"


# ----------------------------------------------------------------------------- PDF
def pdf_bytes(profile, items, result):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    track, domain = profile["track"], profile["domain"]
    accent = colors.HexColor(TEAL if track == "HU" else PURPLE)
    navy, text_color = colors.HexColor(NAVY), colors.HexColor(TEXT)
    font, bold = "Helvetica", "Helvetica-Bold"
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    try:
        pdfmetrics.registerFont(TTFont("ArialLocal", str(fonts / "arial.ttf")))
        pdfmetrics.registerFont(TTFont("ArialLocalBd", str(fonts / "arialbd.ttf")))
        pdfmetrics.registerFontFamily("ArialLocal", normal="ArialLocal", bold="ArialLocalBd")
        font, bold = "ArialLocal", "ArialLocalBd"
    except Exception:
        pass

    base = ParagraphStyle("base", fontName=font, fontSize=8.6, leading=11.5, textColor=text_color)
    small = ParagraphStyle("small", parent=base, fontSize=7.6, leading=10)
    cell = ParagraphStyle("cell", parent=base, fontSize=8, leading=10.2)
    cellc = ParagraphStyle("cellc", parent=cell, alignment=1)
    head = ParagraphStyle("head", parent=base, fontName=bold, fontSize=8, leading=10, textColor=colors.white, alignment=1)
    P = lambda value, style=base: Paragraph(escape(str(value)), style)
    PX = lambda markup, style=base: Paragraph(markup, style)

    def section(number, title):
        bar = Table([[PX(f"<font color='white'><b>{number}.  {escape(title)}</b></font>",
                         ParagraphStyle("sec", parent=base, fontSize=10.5, leading=13))]], colWidths=[174 * mm])
        bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), accent), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                                 ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        return bar

    def paint(canvas, doc_):
        width, height = A4
        canvas.saveState()
        canvas.setFillColor(navy)
        canvas.rect(0, height - 14 * mm, width, 14 * mm, stroke=0, fill=1)
        canvas.setFillColor(accent)
        canvas.rect(0, height - 15.6 * mm, width, 1.6 * mm, stroke=0, fill=1)
        canvas.setFillColor(colors.HexColor("#f2b134"))
        canvas.rect(0, height - 16.4 * mm, width, .8 * mm, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont(bold, 9.5)
        canvas.drawString(18 * mm, height - 9 * mm, APP_NAME)
        canvas.setFont(font, 8)
        canvas.drawRightString(width - 18 * mm, height - 9 * mm, "Rapport indicatif")
        canvas.setStrokeColor(accent)
        canvas.setLineWidth(.8)
        canvas.line(18 * mm, 15 * mm, width - 18 * mm, 15 * mm)
        canvas.setFillColor(colors.HexColor(MUTED))
        canvas.setFont(font, 7.4)
        canvas.drawString(18 * mm, 10.5 * mm, f"Réalisé par : {AUTHOR}  |  {EMAIL}")
        canvas.drawString(18 * mm, 6.6 * mm, f"Généré le {datetime.now():%d/%m/%Y à %H:%M}  ·  {SOURCES[track]}")
        canvas.restoreState()

    class Numbered(Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._pages = []

        def showPage(self):
            self._pages.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._pages)
            for state in self._pages:
                self.__dict__.update(state)
                paint(self, None)
                self.setFillColor(colors.HexColor(MUTED))
                self.setFont(bold, 8)
                self.drawRightString(A4[0] - 18 * mm, 10.5 * mm, f"Page {self._pageNumber} / {total}")
                super().showPage()
            super().save()

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=24 * mm,
                            bottomMargin=20 * mm, title="Rapport de promotion universitaire", author=AUTHOR)
    full = 174 * mm
    story = []

    banner = Table([[PX("<font color='white'><b>RAPPORT INDICATIF DE PROMOTION UNIVERSITAIRE</b></font>",
                        ParagraphStyle("t", parent=base, fontSize=14, leading=18)),
                     ], [PX(f"<font color='#ffe9b0'>{escape(TRACKS[track].replace('  ', ' '))}</font>",
                            ParagraphStyle("t2", parent=base, fontSize=9.5, leading=12))]], colWidths=[full])
    banner.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), navy), ("LEFTPADDING", (0, 0), (-1, -1), 12),
                                ("TOPPADDING", (0, 0), (0, 0), 9), ("BOTTOMPADDING", (0, 1), (0, 1), 9),
                                ("LINEBELOW", (0, -1), (-1, -1), 3, accent)]))
    story += [banner, Spacer(1, 9)]

    # 1. Candidat
    grade_label = profile.get("current_grade") or "—"
    rows = [[P("Nom et prénom", cell), P(profile.get("name") or "—", cell), P("Établissement", cell), P(profile.get("institution") or "—", cell)],
            [P("Parcours", cell), P(TRACKS[track].replace("  ", " "), cell), P("Domaine", cell), P(DOMAINS[domain], cell)],
            [P("Grade actuel", cell), P(grade_label, cell), P("Exercice effectif", cell), P(f"{profile.get('effective_years') or '0'} an(s)", cell)]]
    if track == "HU":
        phd = parse_date(profile.get("phd_date"))
        rows.append([P("Date du doctorat", cell), P(phd.strftime("%d/%m/%Y") if phd else "—", cell), P("Même filière", cell),
                     P("Oui" if profile.get("same_field") else "Non", cell)])
    cand = Table(rows, colWidths=[30 * mm, 57 * mm, 30 * mm, 57 * mm])
    cand.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#c7d3e0")),
                              ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e3edf8")),
                              ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#e3edf8")),
                              ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story += [section(1, "Candidat"), Spacer(1, 4), cand, Spacer(1, 10)]

    # 2. Résultat
    ok = result["ok"]
    verdict_color = colors.HexColor(GREEN if ok else RED)
    verdict = Table([[PX(f"<font color='white'><b>{'RECEVABLE' if ok else 'INCOMPLET'}</b></font>",
                         ParagraphStyle("v", parent=base, fontSize=12, leading=15, alignment=1)),
                      PX(f"<font color='white'>{escape(result['decision'])}</font>", ParagraphStyle("v2", parent=base, fontSize=8.8, leading=11.5))]],
                    colWidths=[34 * mm, 140 * mm])
    verdict.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), verdict_color), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                 ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                                 ("LINEAFTER", (0, 0), (0, 0), .8, colors.white)]))

    def tile(label, value, color):
        return [PX(f"<font color='white' size='8'>{label}</font><br/><font color='white' size='17'><b>{value}</b></font><font color='white' size='8'> pts</font>",
                   ParagraphStyle("k", parent=base, alignment=1, leading=20)), color]

    tiles = [tile("PÉDAGOGIE", fmt(result["pedagogy"]), colors.HexColor(BLUE)),
             tile("RECHERCHE", fmt(result["research"]), colors.HexColor(GREEN)),
             tile("TOTAL", fmt(result["total"]), colors.HexColor(PURPLE))]
    kpi = Table([[t[0] for t in tiles]], colWidths=[58 * mm] * 3)
    kpi.setStyle(TableStyle([("BACKGROUND", (i, 0), (i, 0), t[1]) for i, t in enumerate(tiles)] +
                            [("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                             ("LINEAFTER", (0, 0), (1, 0), 3, colors.white)]))
    block = [section(2, "Résultat"), Spacer(1, 4), verdict, Spacer(1, 5), kpi]
    limits = result["thresholds"]
    if limits:
        from reportlab.graphics.shapes import Drawing, Rect, String
        draw = Drawing(174 * mm, 28 * mm)
        for index, (label, value, target, col) in enumerate((("Pédagogie", result["pedagogy"], limits["pedagogy"], BLUE),
                                                              ("Recherche", result["research"], limits["research"], GREEN))):
            y = 17 * mm - index * 12 * mm
            width = 118 * mm
            draw.add(String(0, y + 2, label, fontName=bold, fontSize=8.5, fillColor=text_color))
            draw.add(Rect(24 * mm, y, width, 7 * mm, fillColor=colors.HexColor("#e1e8f0"), strokeColor=None))
            draw.add(Rect(24 * mm, y, width * min(1, value / target), 7 * mm,
                          fillColor=colors.HexColor(GREEN if value >= target else col), strokeColor=None))
            draw.add(String(24 * mm + width + 4 * mm, y + 2, f"{fmt(value)} / {target} pts", fontName=bold, fontSize=8.5,
                            fillColor=colors.HexColor(GREEN if value >= target else RED)))
        block += [Spacer(1, 6), draw]
    else:
        block += [Spacer(1, 5), P("Habilitation universitaire : l'arrêté 804 ne publie aucun seuil de points ; le minimum est fixé par la commission régionale.", small)]
    story += [KeepTogether(block), Spacer(1, 8)]

    # 3. Recevabilité
    gate_rows = [[PX("<b>Condition</b>", head), PX("<b>État</b>", head)]]
    for label, passed in result["gates"].items():
        gate_rows.append([P(label, cell), PX(f"<font color='{GREEN if passed else RED}'><b>{'OUI' if passed else 'NON'}</b></font>", cellc)])
    gates = Table(gate_rows, colWidths=[146 * mm, 28 * mm], repeatRows=1)
    gstyle = [("BACKGROUND", (0, 0), (-1, 0), accent), ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#c7d3e0")),
              ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    for i, passed in enumerate(result["gates"].values(), 1):
        gstyle.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#e6f6ec" if passed else "#fdebed")))
    gates.setStyle(TableStyle(gstyle))
    story += [KeepTogether([section(3, "Recevabilité administrative et scientifique"), Spacer(1, 4), gates]), Spacer(1, 10)]

    # 4. Détail
    rulemap = {rule.key: rule for rule in RULES[track]}
    raw, quantity = {}, {}
    for index, item in enumerate(items):
        if index in result["item_points"]:
            key = item["key"]
            raw[key] = raw.get(key, 0) + result["item_points"][index]
            quantity[key] = quantity.get(key, 0) + int(item.get("count", 1))
    detail = [[PX("<b>Activité</b>", head), PX("<b>Nb</b>", head), PX("<b>Brut</b>", head), PX("<b>Plafond</b>", head), PX("<b>Retenu</b>", head)]]
    dstyle = [("BACKGROUND", (0, 0), (-1, 0), accent), ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#c7d3e0")),
              ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    for group, color in (("Pédagogie", BLUE), ("Recherche", GREEN)):
        keys = [k for k in result["scores"] if rulemap[k].group == group]
        if not keys:
            continue
        detail.append([PX(f"<font color='white'><b>{group}</b></font>", cell), "", "", "", PX(f"<font color='white'><b>{fmt(sum(result['scores'][k] for k in keys))}</b></font>", cellc)])
        row = len(detail) - 1
        dstyle += [("SPAN", (0, row), (3, row)), ("BACKGROUND", (0, row), (-1, row), colors.HexColor(color))]
        for k in keys:
            rule = rulemap[k]
            mark = " *" if k in result["capped"] else ""
            detail.append([P(rule.label, cell), P(quantity.get(k, 0), cellc), P(fmt(raw.get(k, 0)), cellc),
                           P("—" if rule.cap is None else fmt(rule.cap), cellc), PX(f"<b>{fmt(result['scores'][k])}{mark}</b>", cellc)])
            if len(detail) % 2:
                dstyle.append(("BACKGROUND", (0, len(detail) - 1), (-1, len(detail) - 1), colors.HexColor("#f3f7fb")))
    if len(detail) == 1:
        detail.append([P("Aucune activité retenue pour le moment.", cell), "", "", "", ""])
        dstyle.append(("SPAN", (0, 1), (-1, 1)))
    else:
        detail.append([PX("<b>TOTAL</b>", cell), "", "", "", PX(f"<b>{fmt(result['total'])}</b>", cellc)])
        dstyle += [("SPAN", (0, -1), (3, -1)), ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ffe9b0"))]
    table = Table(detail, colWidths=[104 * mm, 14 * mm, 18 * mm, 20 * mm, 18 * mm], repeatRows=1)
    table.setStyle(TableStyle(dstyle))
    story += [section(4, "Détail des activités retenues"), Spacer(1, 4), table]
    if result["capped"]:
        story.append(P("* plafond de la grille atteint : les points excédentaires ne sont pas retenus.", small))
    story.append(Spacer(1, 8))

    if result["issues"]:
        issue_rows = [[P("• " + issue, cell)] for issue in result["issues"]]
        issues = Table(issue_rows, colWidths=[full])
        issues.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff4e0")),
                                    ("BOX", (0, 0), (-1, -1), .8, colors.HexColor(ORANGE))]))
        story += [KeepTogether([section(5, "Points à vérifier"), Spacer(1, 4), issues]), Spacer(1, 8)]

    note = Table([[P("Simulation indicative établie à partir des textes officiels du MESRS. Les justificatifs, le classement des revues "
                     "(DGRSDT) et la décision finale relèvent exclusivement des instances compétentes.", small)]], colWidths=[full])
    note.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef3f9")),
                              ("LINEBEFORE", (0, 0), (0, -1), 3, accent), ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
    story.append(note)
    doc.build(story, canvasmaker=Numbered)
    return output.getvalue()


# ----------------------------------------------------------------------------- widgets
def make_button(parent, text, color, command, size=10, padx=16, pady=8, fg="white"):
    button = tk.Button(parent, text=text, command=command, bg=color, fg=fg, activebackground=shade(color, -.18),
                       activeforeground=fg, relief="flat", bd=0, cursor="hand2", font=("Segoe UI", size, "bold"),
                       padx=S(padx), pady=S(pady))
    button.bind("<Enter>", lambda _e: button.configure(bg=shade(color, -.12)))
    button.bind("<Leave>", lambda _e: button.configure(bg=color))
    return button


def make_card(parent, title, color):
    outer = tk.Frame(parent, bg=CARD, highlightbackground="#d3dde9", highlightthickness=1)
    tk.Frame(outer, bg=color, width=S(6)).pack(side="left", fill="y")
    inner = tk.Frame(outer, bg=CARD, padx=S(10), pady=S(4))
    inner.pack(side="left", fill="both", expand=True)
    tk.Label(inner, text=title, bg=CARD, fg=color, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, S(1)))
    content = tk.Frame(inner, bg=CARD)
    content.pack(fill="both", expand=True)
    return outer, content


MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def open_calendar(parent, variable, anchor):
    """Agenda : choix d'une date par clic ; écrit JJ/MM/AAAA dans la variable."""
    import calendar
    current = parse_date(variable.get()) or date.today()
    win = tk.Toplevel(parent)
    win.title("Choisir une date")
    win.configure(bg=CARD)
    win.transient(parent)
    win.resizable(False, False)
    win.geometry(f"+{anchor.winfo_rootx()}+{anchor.winfo_rooty() + anchor.winfo_height() + S(4)}")
    month, year = tk.StringVar(value=MONTHS[current.month - 1]), tk.StringVar(value=str(current.year))
    head = tk.Frame(win, bg=BLUE, padx=S(8), pady=S(6))
    head.pack(fill="x")
    grid = tk.Frame(win, bg=CARD, padx=S(8), pady=S(6))
    grid.pack()

    def draw(*_):
        for child in grid.winfo_children():
            child.destroy()
        try:
            y, m = int(year.get()), MONTHS.index(month.get()) + 1
        except ValueError:
            return
        for col, name in enumerate(("Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di")):
            tk.Label(grid, text=name, bg=CARD, fg=BLUE, font=("Segoe UI", 9, "bold"), width=4).grid(row=0, column=col)
        selected = parse_date(variable.get())
        for r, week in enumerate(calendar.Calendar(0).monthdayscalendar(y, m), 1):
            for col, day in enumerate(week):
                if not day:
                    continue
                chosen = selected == date(y, m, day)
                today = date.today() == date(y, m, day)
                color = GREEN if chosen else ("#fde9b8" if today else "#eef3f9")
                tk.Button(grid, text=str(day), width=4, relief="flat", bd=0, cursor="hand2", bg=color, fg="white" if chosen else TEXT,
                          font=("Segoe UI", 9, "bold" if chosen or today else "normal"),
                          command=lambda d=day: choose(date(y, m, d))).grid(row=r, column=col, padx=1, pady=1)

    def choose(value):
        variable.set(value.strftime("%d/%m/%Y"))
        win.destroy()

    def shift(delta):
        index = MONTHS.index(month.get()) + delta
        if index < 0:
            index, year_value = 11, int(year.get()) - 1
        elif index > 11:
            index, year_value = 0, int(year.get()) + 1
        else:
            year_value = int(year.get())
        month.set(MONTHS[index])
        year.set(str(min(2100, max(1940, year_value))))

    tk.Button(head, text="◀", command=lambda: shift(-1), bg=BLUE, fg="white", relief="flat", bd=0, font=("Segoe UI", 10, "bold")).pack(side="left")
    ttk.Combobox(head, textvariable=month, values=MONTHS, state="readonly", width=10).pack(side="left", padx=S(4))
    ttk.Combobox(head, textvariable=year, values=[str(y) for y in range(1940, 2101)], state="readonly", width=6).pack(side="left")
    tk.Button(head, text="▶", command=lambda: shift(1), bg=BLUE, fg="white", relief="flat", bd=0, font=("Segoe UI", 10, "bold")).pack(side="left", padx=S(4))
    month_trace, year_trace = month.trace_add("write", draw), year.trace_add("write", draw)
    foot = tk.Frame(win, bg=CARD, pady=S(6))
    foot.pack()
    make_button(foot, "Aujourd'hui", GREEN, lambda: choose(date.today()), size=9, padx=10, pady=3).pack(side="left", padx=S(4))
    make_button(foot, "Effacer", ORANGE, lambda: (variable.set(""), win.destroy()), size=9, padx=10, pady=3).pack(side="left", padx=S(4))
    make_button(foot, "Fermer", SLATE, win.destroy, size=9, padx=10, pady=3).pack(side="left", padx=S(4))
    win.bind("<Escape>", lambda _e: win.destroy())
    draw()
    win.update_idletasks()
    win.grab_set()


class GradientBar(tk.Canvas):
    def __init__(self, parent, height, left, right, **kw):
        super().__init__(parent, height=height, highlightthickness=0, bd=0, **kw)
        self.left, self.right = left, right
        self.bind("<Configure>", self.redraw)

    def redraw(self, _event=None):
        self.delete("grad")
        width, height = self.winfo_width(), self.winfo_height()
        a = [int(self.left[i:i + 2], 16) for i in (1, 3, 5)]
        b = [int(self.right[i:i + 2], 16) for i in (1, 3, 5)]
        step = max(2, S(3))
        for x in range(0, width, step):
            t = x / max(1, width)
            color = "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
            self.create_rectangle(x, 0, x + step, height, fill=color, outline=color, tags="grad")
        self.tag_lower("grad")


# ----------------------------------------------------------------------------- application
class App(tk.Tk):
    def __init__(self):
        global K
        super().__init__()
        K = max(1.0, self.winfo_fpixels("1i") / 96)
        self.title(f"{APP_NAME} — v{APP_VERSION}")
        width = min(S(1500), int(self.winfo_screenwidth() * .95))
        height = min(S(900), int(self.winfo_screenheight() * .9))
        self.geometry(f"{width}x{height}+{(self.winfo_screenwidth() - width) // 2}+{max(0, (self.winfo_screenheight() - height) // 3)}")
        self.minsize(min(S(1150), width), min(S(700), height))
        self.configure(bg=BG)
        self.dossier_id = uuid.uuid4().hex
        self.items = []
        self.vars = {key: tk.StringVar() for key in ("name", "institution", "phd_date", "effective_years", "identifier")}
        self.track, self.domain, self.grade = tk.StringVar(value="HU"), tk.StringVar(value="ST"), tk.StringVar(value="MCB")
        self.track_text, self.domain_text = tk.StringVar(value=TRACKS["HU"]), tk.StringVar(value=DOMAINS["ST"])
        self.same_field = tk.BooleanVar(value=True)
        self.rule_label, self.count = tk.StringVar(), tk.StringVar(value="1")
        self.author_text = tk.StringVar(value="1er auteur")
        self.principal, self.after_phd = tk.BooleanVar(value=True), tk.BooleanVar(value=True)
        self.outside_thesis, self.confirmed = tk.BooleanVar(value=True), tk.BooleanVar(value=False)
        self.alphabetical = tk.BooleanVar(value=False)
        self.custom_points = tk.StringVar(value="0")
        self.saved_choice = tk.StringVar()
        self.saved_paths = {}
        self._save_job = None
        self.result = None
        self._build()
        self.restore_last()
        self.apply_theme()
        self.list_dossiers()
        self.refresh()
        self.protocol("WM_DELETE_WINDOW", self.close)

    # ---------------------------------------------------------------- interface
    def _build(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", background=CARD, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("TCheckbutton", background=CARD, foreground=TEXT, font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[("disabled", CARD), ("active", CARD)], foreground=[("disabled", "#a3afbd")])
        style.map("TLabel", background=[("disabled", CARD)], foreground=[("disabled", "#a3afbd")])
        style.configure("TCombobox", padding=S(1))
        style.configure("TEntry", padding=S(1))
        style.configure("Treeview", rowheight=S(30), font=("Segoe UI", 10), background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background=NAVY, foreground="white", padding=S(5))
        style.map("Treeview.Heading", background=[("active", BLUE)])
        style.map("Treeview", background=[("selected", "#bcd8f2")], foreground=[("selected", TEXT)])

        # bas de fenêtre d'abord (réserve sa place)
        footer = tk.Frame(self, bg="#0b2a46")
        footer.pack(side="bottom", fill="x")
        tk.Label(footer, text=f" ©  Réalisé par : {AUTHOR}   |   {EMAIL}", bg="#0b2a46", fg="#e0f2fe",
                 font=("Segoe UI", 9, "bold"), pady=S(3)).pack(side="left")
        tk.Label(footer, text=f"Version {APP_VERSION}  ·  Sources : arrêté 804/2021, décret 21-50, CUN 54  ", bg="#0b2a46",
                 fg="#9fc4e4", font=("Segoe UI", 9)).pack(side="right")
        bar = tk.Frame(self, bg=NAVY, padx=S(12), pady=S(5))
        bar.pack(side="bottom", fill="x")
        buttons = (("Importer JSON", TEAL, self.import_json),
                   ("Exporter JSON", ORANGE, self.export_json),
                   ("Rapport PDF", RED, self.export_pdf), ("Guide & barèmes", GREEN, self.show_guide))
        center = tk.Frame(bar, bg=NAVY)
        center.pack()  # boutons centrés
        for text, color, command in buttons + (("Quitter", SLATE, self.close),):
            make_button(center, text, color, command, size=9, padx=14, pady=4).pack(side="left", padx=S(4))

        header = self.header = GradientBar(self, S(62), NAVY, PURPLE, bg=NAVY)
        header.pack(fill="x")
        header.create_text(S(22), S(13), text="Promotion des enseignants universitaires — Algérie", anchor="w", fill="#dbe8f5", font=("Segoe UI", 10, "bold"))
        self.hd_shadow = header.create_text(S(23), S(41), text="", anchor="w", fill="#1b1200", font=("Segoe UI", 20, "bold"))
        self.hd_grade = header.create_text(S(22), S(40), text="", anchor="w", fill="#fff0a8", font=("Segoe UI", 20, "bold"))
        self.hd_sub = header.create_text(0, S(42), text="", anchor="e", fill="#ffe9b0", font=("Segoe UI", 10, "bold"))
        badge = header.create_text(0, S(13), text=AUTHOR + "   |   " + EMAIL, anchor="e", fill="white", font=("Segoe UI", 10, "bold"))

        def place(e):
            header.redraw()
            header.coords(badge, e.width - S(22), S(13))
            header.coords(self.hd_sub, e.width - S(22), S(42))
        header.bind("<Configure>", place, add="+")
        tk.Frame(self, bg="#f2b134", height=S(4)).pack(fill="x")

        body = self.body = tk.Frame(self, bg=BG, padx=S(12), pady=S(8))
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3, uniform="c")
        body.columnconfigure(1, weight=2, uniform="c")
        body.rowconfigure(2, weight=1)

        # barre des dossiers
        strip = self.strip = tk.Frame(body, bg=BG)
        strip.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, S(6)))
        self.strip_label = tk.Label(strip, text="Dossier enregistré :", bg=BG, fg=NAVY, font=("Segoe UI", 10, "bold"))
        self.strip_label.pack(side="left")
        self.saved_combo = ttk.Combobox(strip, textvariable=self.saved_choice, width=34, state="readonly", postcommand=self.list_dossiers)
        self.saved_combo.pack(side="left", padx=S(6))
        make_button(strip, "Ouvrir", TEAL, self.open_selected, size=9, padx=12, pady=3).pack(side="left")
        make_button(strip, "＋  Nouveau dossier", BLUE, self.new_dossier, size=9, padx=12, pady=3).pack(side="left", padx=S(8))
        make_button(strip, "Aperçu PDF", PURPLE, self.preview_pdf, size=9, padx=12, pady=3).pack(side="left")
        self.status = tk.Label(strip, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9, "italic"))
        self.status.pack(side="right")

        profile_holder = self.profile_holder = tk.Frame(body, bg=BG)
        profile_holder.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, S(6)))
        left = self.left = tk.Frame(body, bg=BG)
        left.grid(row=2, column=0, sticky="nsew", padx=(0, S(10)))
        right = self.right = tk.Frame(body, bg=BG)
        right.grid(row=2, column=1, sticky="nsew")
        self._build_profile(profile_holder)
        self._build_entry(left)
        self._build_table(left)
        self._build_dashboard(right)
        self.rebuild_rules()
        for name, var in self.vars.items():
            var.trace_add("write", lambda *_: self.schedule_save())
        self.same_field.trace_add("write", lambda *_: self.schedule_save())

    def _field(self, parent, label, variable, width, row, column, span=1):
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", padx=(0, S(5)), pady=S(1))
        entry = ttk.Entry(parent, textvariable=variable, width=width)
        entry.grid(row=row, column=column + 1, columnspan=span, sticky="w", padx=(0, S(12)), pady=S(1))
        return entry

    def _build_profile(self, parent):
        card, inner = make_card(parent, "①  Profil du candidat", BLUE)
        card.pack(fill="x")
        label = lambda text, r, c: ttk.Label(inner, text=text).grid(row=r, column=c, sticky="w", padx=(0, S(5)), pady=S(1))
        self._field(inner, "Nom et prénom", self.vars["name"], 24, 0, 0)
        self._field(inner, "Établissement", self.vars["institution"], 24, 0, 2)
        label("Parcours", 0, 4)
        self.track_combo = ttk.Combobox(inner, textvariable=self.track_text, values=list(TRACKS.values()), state="readonly", width=30)
        self.track_combo.grid(row=0, column=5, sticky="w", padx=(0, S(12)), pady=S(1))
        self.track_combo.bind("<<ComboboxSelected>>", self.switch_track)
        label("Domaine", 0, 6)
        self.domain_combo = ttk.Combobox(inner, textvariable=self.domain_text, values=list(DOMAINS.values()), state="readonly", width=22)
        self.domain_combo.grid(row=0, column=7, sticky="w", pady=S(1))
        self.domain_combo.bind("<<ComboboxSelected>>", self.change_domain)
        label("Grade actuel", 1, 0)
        self.grade_combo = ttk.Combobox(inner, textvariable=self.grade, state="readonly", width=8)
        self.grade_combo.grid(row=1, column=1, sticky="w", pady=S(1))
        self.grade_combo.bind("<<ComboboxSelected>>", lambda _e: self.schedule_save())
        ttk.Label(inner, text="Exercice effectif (années)").grid(row=1, column=2, sticky="w", padx=(0, S(5)))
        years = tk.Frame(inner, bg=CARD)
        years.grid(row=1, column=3, sticky="w")
        ttk.Entry(years, textvariable=self.vars["effective_years"], width=7).pack(side="left")
        self.years_hint = tk.Label(years, text="", bg=CARD, font=("Segoe UI", 9, "bold"))
        self.years_hint.pack(side="left", padx=S(6))
        self.phd_label = tk.Label(inner, text="Date du doctorat", bg=CARD, fg=TEXT, font=("Segoe UI", 10))
        self.phd_label.grid(row=1, column=4, sticky="w", padx=(0, S(5)), pady=S(1))
        phd = tk.Frame(inner, bg=CARD)
        phd.grid(row=1, column=5, sticky="w")
        self.phd_entry = ttk.Entry(phd, textvariable=self.vars["phd_date"], width=14)
        self.phd_entry.pack(side="left")
        self.phd_button = make_button(phd, "▦ Agenda", BLUE, lambda: open_calendar(self, self.vars["phd_date"], self.phd_entry), size=9, padx=8, pady=1)
        self.phd_button.pack(side="left", padx=(S(6), 0))
        self.phd_hint = tk.Label(phd, text="", bg=CARD, font=("Segoe UI", 9, "bold"))
        self.phd_hint.pack(side="left", padx=S(6))
        self.same_check = tk.Checkbutton(inner, text="Même filière que le doctorat", variable=self.same_field, command=self.refresh,
                                         bg=CARD, activebackground=CARD, disabledforeground="#a3afbd", font=("Segoe UI", 10), bd=0, highlightthickness=0)
        self.same_check.grid(row=1, column=6, columnspan=2, sticky="w")

    def _build_entry(self, parent):
        card, inner = make_card(parent, "②  Ajouter une activité", ORANGE)
        card.pack(fill="x", pady=(0, S(8)))
        line = tk.Frame(inner, bg=CARD)
        line.pack(fill="x")
        ttk.Label(line, text="Rubrique").pack(side="left", padx=(0, S(3)))
        self.rule_combo = ttk.Combobox(line, textvariable=self.rule_label, state="readonly", width=30)
        self.rule_combo.pack(side="left", padx=(0, S(5)))
        self.rule_combo.bind("<<ComboboxSelected>>", lambda _e: self.update_publication_fields())
        ttk.Label(line, text="Qté").pack(side="left", padx=(0, S(2)))
        ttk.Entry(line, textvariable=self.count, width=4).pack(side="left", padx=(0, S(5)))
        ttk.Label(line, text="Réf. / DOI").pack(side="left", padx=(0, S(2)))
        ttk.Entry(line, textvariable=self.vars["identifier"], width=11).pack(side="left", padx=(0, S(6)))
        for text, color, command in (("＋ Ajouter", GREEN, self.add_item), ("✕ Supprimer", RED, self.remove_item)):
            button = make_button(line, text, color, command, size=9, padx=8, pady=3)
            button.configure(width=11)
            button.pack(side="left", padx=(0, S(4)))
        self.rule_hint = tk.Label(inner, text="", bg=CARD, fg=BLUE, font=("Segoe UI", 9, "bold"), anchor="w", justify="left")
        self.rule_hint.pack(fill="x", pady=(S(4), 0))
        pubs = tk.Frame(inner, bg=CARD)
        pubs.pack(fill="x", pady=(S(4), 0))
        self.pub_widgets = []
        label = tk.Label(pubs, text="Position", bg=CARD, fg=TEXT, font=("Segoe UI", 10))
        label.pack(side="left", padx=(0, S(4)))
        self.author_combo = ttk.Combobox(pubs, textvariable=self.author_text, values=list(POSITIONS), state="readonly", width=17)
        self.author_combo.pack(side="left", padx=(0, S(10)))
        self.pub_widgets += [label, self.author_combo]
        for text, var in (("Auteur principal", self.principal), ("Après doctorat", self.after_phd), ("Hors thèse", self.outside_thesis),
                          ("Classement confirmé", self.confirmed), ("Alphabétique", self.alphabetical)):
            widget = tk.Checkbutton(pubs, text=text, variable=var, bg=CARD, activebackground=CARD, disabledforeground="#a3afbd",
                                    font=("Segoe UI", 9), bd=0, highlightthickness=0)
            widget.pack(side="left", padx=(0, S(4)))
            self.pub_widgets.append(widget)
        self.points_frame = tk.Frame(inner, bg=CARD)
        ttk.Label(self.points_frame, text="Points attestés (0 à 10)").pack(side="left", padx=(0, S(5)))
        ttk.Entry(self.points_frame, textvariable=self.custom_points, width=6).pack(side="left")

    def _build_table(self, parent):
        card, inner = make_card(parent, "③  Activités saisies", GREEN)
        card.pack(fill="both", expand=True)
        wrap = tk.Frame(inner, bg=CARD)
        wrap.pack(fill="both", expand=True)
        cols = ("group", "activity", "count", "points", "note")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings", selectmode="browse")
        for col, text, width, stretch in (("group", "Type", 90, False), ("activity", "Activité", 230, True), ("count", "Qté", 48, False),
                                          ("points", "Points", 70, False), ("note", "Précisions", 230, True)):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=S(width), minwidth=S(40), stretch=stretch, anchor="center" if col in ("count", "points", "group") else "w")
        scroll = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.tag_configure("ped", background="#e8f1fb")
        self.tree.tag_configure("res", background="#e7f6ee")
        self.tree.tag_configure("bad", background="#fde8ea", foreground=RED)
        self.tree.bind("<Delete>", lambda _e: self.remove_item())
        row = tk.Frame(inner, bg=CARD)
        row.pack(fill="x", pady=(S(6), 0))
        self.count_label = tk.Label(row, text="", bg=CARD, fg=MUTED, font=("Segoe UI", 9))
        self.count_label.pack(side="left")
        make_button(row, "Supprimer la ligne", RED, self.remove_item, size=9, padx=10, pady=2).pack(side="right")

    def _build_dashboard(self, parent):
        card, inner = make_card(parent, "④  Bilan et recevabilité", PURPLE)
        card.pack(fill="both", expand=True)
        self.verdict = tk.Label(inner, text="", bg=SLATE, fg="white", font=("Segoe UI", 11, "bold"), wraplength=S(400), justify="left",
                                padx=S(10), pady=S(5), anchor="w")
        self.verdict.pack(fill="x")
        tiles = tk.Frame(inner, bg=CARD)
        tiles.pack(fill="x", pady=S(3))
        self.tile_values = {}
        for column, (key, label, color) in enumerate((("pedagogy", "PÉDAGOGIE", BLUE), ("research", "RECHERCHE", GREEN), ("total", "TOTAL", PURPLE))):
            tiles.columnconfigure(column, weight=1, uniform="t")
            box = tk.Frame(tiles, bg=color, padx=S(6), pady=S(2))
            box.grid(row=0, column=column, sticky="ew", padx=S(3))
            tk.Label(box, text=label, bg=color, fg="#e8f0fa", font=("Segoe UI", 8, "bold")).pack()
            value = tk.Label(box, text="0", bg=color, fg="white", font=("Segoe UI", 14, "bold"))
            value.pack()
            self.tile_values[key] = value
        self.bars = tk.Canvas(inner, height=S(54), bg=CARD, highlightthickness=0)
        self.bars.pack(fill="x")
        self.bars.bind("<Configure>", lambda _e: self.draw_bars())
        tk.Label(inner, text="Conditions de recevabilité", bg=CARD, fg=NAVY, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(S(4), S(3)))
        self.gate_frame = tk.Frame(inner, bg=CARD)
        self.gate_frame.pack(fill="x")
        tk.Label(inner, text="Points à vérifier", bg=CARD, fg=ORANGE, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(S(8), S(3)))
        self.issue_text = tk.Text(inner, height=4, wrap="word", state="disabled", relief="flat", bg="#fff6e8", fg=TEXT,
                                  font=("Segoe UI", 9), padx=S(8), pady=S(6))
        self.issue_text.pack(fill="both", expand=True)

    # ---------------------------------------------------------------- données
    def profile(self):
        data = {key: var.get().strip() for key, var in self.vars.items() if key != "identifier"}
        data.update(track=self.track.get(), domain=self.domain.get(), current_grade=self.grade.get(), same_field=self.same_field.get())
        return data

    def payload(self):
        return {"schema": 1, "id": self.dossier_id, "profile": self.profile(), "items": self.items,
                "updated_at": datetime.now().isoformat(timespec="seconds"), "app_version": APP_VERSION}

    def save(self):
        self._save_job = None
        atomic_write(DOSSIERS / f"{self.dossier_id}.json", json.dumps(self.payload(), ensure_ascii=False, indent=2))
        atomic_write(STATE, self.dossier_id)

    def schedule_save(self):
        if self._save_job is not None:
            self.after_cancel(self._save_job)
        self._save_job = self.after(600, self.save)
        self.refresh(rebuild_table=False)

    def list_dossiers(self):
        paths, current = {}, ""
        for path in sorted(DOSSIERS.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                stamp = str(data.get("updated_at", ""))[:16].replace("T", " ")
                label = f"{data.get('profile', {}).get('name') or 'Sans nom'} · {stamp} · {path.stem[:6]}"
                paths[label] = path
                if path.stem == self.dossier_id:
                    current = label
            except (OSError, ValueError, TypeError, AttributeError):
                pass
        self.saved_paths = paths
        self.saved_combo.configure(values=list(paths))
        self.saved_choice.set(current)

    def load(self, data):
        if not isinstance(data, dict) or data.get("schema") != 1 or not isinstance(data.get("items"), list):
            raise ValueError("Format de dossier invalide")
        profile = data.get("profile") if isinstance(data.get("profile"), dict) else {}
        self.dossier_id = str(data.get("id") or uuid.uuid4().hex)
        self.items = [item for item in data["items"] if isinstance(item, dict)]
        for key, var in self.vars.items():
            if key != "identifier":
                var.set(str(profile.get(key) or ""))
        track = profile.get("track") if profile.get("track") in RULES else "HU"
        domain = profile.get("domain") if profile.get("domain") in DOMAINS else "ST"
        self.track.set(track)
        self.track_text.set(TRACKS[track])
        self.domain.set(domain)
        self.domain_text.set(DOMAINS[domain])
        self.same_field.set(bool(profile.get("same_field", True)))
        self.rebuild_rules(profile.get("current_grade"))
        self.apply_theme()
        self.refresh()

    def restore_last(self):
        try:
            path = DOSSIERS / f"{STATE.read_text(encoding='utf-8').strip()}.json"
            self.load(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError):
            self.save()

    def blank(self, track="HU"):
        return {"schema": 1, "id": uuid.uuid4().hex, "profile": {"track": track, "domain": self.domain.get()}, "items": []}

    def new_dossier(self):
        self.save()
        self.load(self.blank(self.track.get()))
        self.save()
        self.set_status("Nouveau dossier vierge créé ; le précédent est conservé.")

    def open_selected(self):
        path = self.saved_paths.get(self.saved_choice.get())
        if not path:
            messagebox.showinfo(APP_NAME, "Aucun dossier sélectionné.")
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.save()
            self.load(data)
            self.save()
            self.set_status("Dossier ouvert.")
        except (OSError, ValueError, TypeError) as exc:
            messagebox.showerror(APP_NAME, f"Impossible d'ouvrir ce dossier : {exc}")

    def import_json(self):
        source = filedialog.askopenfilename(filetypes=[("Dossier JSON", "*.json")])
        if not source:
            return
        try:
            data = json.loads(Path(source).read_text(encoding="utf-8"))
            self.save()
            data["id"] = uuid.uuid4().hex  # un import ne remplace jamais un dossier existant
            self.load(data)
            self.save()
            self.set_status(f"Dossier importé : {Path(source).name}")
        except (OSError, ValueError, TypeError) as exc:
            messagebox.showerror(APP_NAME, f"Fichier invalide : {exc}")

    def export_json(self):
        stub = (self.vars["name"].get().strip().replace(" ", "_") or "dossier")
        target = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")],
                                               initialfile=f"promotion_{stub}_{datetime.now():%Y%m%d}.json")
        if target:
            try:
                atomic_write(Path(target), json.dumps(self.payload(), ensure_ascii=False, indent=2))
                self.set_status(f"JSON exporté : {Path(target).name}")
            except OSError as exc:
                messagebox.showerror(APP_NAME, f"Export impossible : {exc}")

    def set_status(self, text):
        self.status.configure(text=text)

    # ---------------------------------------------------------------- règles / saisie
    def apply_theme(self):
        """Couleur de toute l'interface et titre du grade visé selon le parcours."""
        theme = THEMES[self.track.get()]
        for widget in (self, self.body, self.strip, self.left, self.right, self.profile_holder):
            widget.configure(bg=theme["bg"])
        self.strip_label.configure(bg=theme["bg"], fg=theme["fg"])
        self.status.configure(bg=theme["bg"], fg=theme["fg"])
        self.header.left, self.header.right = theme["g1"], theme["g2"]
        self.header.itemconfigure(self.hd_grade, text=theme["title"], fill=theme["tcolor"])
        self.header.itemconfigure(self.hd_shadow, text=theme["title"])
        self.header.itemconfigure(self.hd_sub, text=theme["sub"])
        self.header.redraw()

    def rule_text(self, rule):
        return f"{rule.group} · {rule.label}"

    def rebuild_rules(self, grade=None):
        track = self.track.get()
        self.rule_combo.configure(values=[self.rule_text(rule) for rule in RULES[track]])
        self.rule_label.set(self.rule_text(RULES[track][0]))
        grades = HU_GRADES if track == "HU" else CUN_GRADES
        self.grade_combo.configure(values=grades)
        self.grade.set(grade if grade in grades else grades[0])
        state = "normal" if track == "HU" else "disabled"
        self.phd_entry.configure(state=state)
        self.phd_button.configure(state=state)
        self.same_check.configure(state=state)
        self.phd_label.configure(fg=TEXT if track == "HU" else "#a3afbd")
        self.update_publication_fields()

    def switch_track(self, _event=None):
        new = key_of(TRACKS, self.track_text.get(), self.track.get())
        old = self.track.get()
        if new == old:
            return
        if self.items and not messagebox.askyesno(APP_NAME, "Changer de parcours ouvre un nouveau dossier vierge ; le dossier actuel est conservé. Continuer ?"):
            self.track_text.set(TRACKS[old])
            return
        self.save()  # le dossier courant est enregistré avec son ancien parcours
        self.load(self.blank(new))
        self.save()

    def change_domain(self, _event=None):
        self.domain.set(key_of(DOMAINS, self.domain_text.get(), "ST"))
        self.schedule_save()

    def selected_rule(self):
        return next((rule for rule in RULES[self.track.get()] if self.rule_text(rule) == self.rule_label.get()), None)

    def update_publication_fields(self):
        rule = self.selected_rule()
        is_pub = bool(rule and rule.key in PUBLICATIONS)
        for widget in self.pub_widgets:
            try:
                widget.configure(state=("readonly" if isinstance(widget, ttk.Combobox) else "normal") if is_pub else "disabled")
            except tk.TclError:
                pass
        if rule and rule.key == "study_office":
            self.points_frame.pack(fill="x", pady=(S(4), 0))
        else:
            self.points_frame.pack_forget()
        if rule:
            cap = f" · plafond {fmt(rule.cap)} pts" if rule.cap is not None else ""
            unit = "points à saisir selon attestation" if rule.key == "study_office" else f"{fmt(rule.points)} pt(s) par unité"
            extra = "  ⚠ supplément : exige l'activité de base correspondante" if "supplément" in rule.label.lower() else ""
            self.rule_hint.configure(text=f"{unit}{cap}{extra}" + (f"\n{rule.detail}" if rule.detail else "")
                                     + ("\nChaque publication se saisit séparément (position d'auteur et classement confirmé obligatoires)." if is_pub else ""))

    def add_item(self):
        rule = self.selected_rule()
        if rule is None:
            return
        try:
            count = int(self.count.get())
            if not 1 <= count <= 1000 or (rule.key in PUBLICATIONS and count != 1):
                raise ValueError
        except ValueError:
            messagebox.showerror(APP_NAME, "Quantité invalide (entier de 1 à 1000). Chaque publication doit être saisie séparément (quantité 1).")
            return
        item = {"key": rule.key, "count": count, "identifier": self.vars["identifier"].get().strip()}
        if rule.key in PUBLICATIONS:
            if not self.confirmed.get():
                if not messagebox.askyesno(APP_NAME, "Le classement de la revue n'est pas confirmé : la publication ne sera pas comptée tant que vous ne l'aurez pas vérifié. L'ajouter quand même ?"):
                    return
            sole = self.author_text.get() == "Auteur unique"
            item.update(author_position=POSITIONS[self.author_text.get()], principal=True if sole else self.principal.get(), sole=sole,
                        after_phd=self.after_phd.get(), outside_thesis=self.outside_thesis.get(), confirmed=self.confirmed.get(),
                        alphabetical=self.alphabetical.get())
        if rule.key == "study_office":
            try:
                item["points"] = float(self.custom_points.get().replace(",", "."))
                if not 0 <= item["points"] <= 10:
                    raise ValueError
            except ValueError:
                messagebox.showerror(APP_NAME, "Saisissez les points attestés (nombre entre 0 et 10).")
                return
        self.items.append(item)
        self.vars["identifier"].set("")
        self.count.set("1")
        self.save()
        self.refresh()
        self.set_status(f"Ajouté : {rule.label}")

    def remove_item(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(APP_NAME, "Sélectionnez d'abord une ligne dans le tableau.")
            return
        self.items.pop(int(selection[0]))
        self.save()
        self.refresh()

    # ---------------------------------------------------------------- affichage
    def refresh(self, rebuild_table=True):
        try:
            self.result = result = evaluate(self.profile(), self.items)
        except (ValueError, TypeError):
            return
        track = self.track.get()
        rulemap = {rule.key: rule for rule in RULES[track]}
        if rebuild_table:
            self.tree.delete(*self.tree.get_children())
            for index, item in enumerate(self.items):
                rule = rulemap.get(item.get("key"))
                if not rule:
                    continue
                note = item.get("identifier") or ""
                if rule.key in PUBLICATIONS:
                    position = "Auteur unique" if item.get("sole") else next((k for k, v in POSITIONS.items() if v == item.get("author_position") and k != "Auteur unique"), "?")
                    note = f"{position}" + (f" · {note}" if note else "")
                if index in result["rejected"]:
                    tag, points, note = "bad", "✘", result["rejected"][index]
                else:
                    tag, points = ("ped" if rule.group == "Pédagogie" else "res"), fmt(result["item_points"].get(index, 0))
                self.tree.insert("", "end", iid=str(index), tags=(tag,),
                                 values=(rule.group, rule.label, item.get("count", 1), points, note))
            self.count_label.configure(text=f"{len(self.items)} activité(s) saisie(s)")
        for key, label in self.tile_values.items():
            label.configure(text=fmt(result[key]))
        empty = not self.items and not self.vars["name"].get().strip()
        if empty:
            color, text = SLATE, "●  Dossier vide — renseignez le profil puis ajoutez vos activités."
        elif result["ok"]:
            color, text = GREEN, "✔  " + result["decision"]
        else:
            color, text = "#e0572a", "✘  " + result["decision"]
        self.verdict.configure(bg=color, text=text)
        for child in self.gate_frame.winfo_children():
            child.destroy()
        for label, passed in result["gates"].items():
            tk.Label(self.gate_frame, text=f"  {'✔' if passed else '✘'}   {label}", anchor="w", bg="#e3f5ea" if passed else "#fde8ea",
                     fg=GREEN if passed else RED, font=("Segoe UI", 9, "bold"), pady=0).pack(fill="x", pady=1)
        notes = list(result["issues"])
        if result["capped"]:
            notes += [f"Plafond atteint : {rulemap[k].label}" for k in result["capped"]]
        if result.get("mandatory") is not None:
            notes.append(f"Ligne {result['mandatory'] + 1} : publication obligatoire créditée à 100 % (exception de l'annexe 804).")
        if track == "CUN54":
            notes.append("Rappel : articles de rang C dans des revues et des numéros différents ; revues prédatrices ou non reconnues par la DGRSDT refusées.")
        else:
            notes.append("Rappel : publications dans une revue de rang A ou B (S&T) ; revues prédatrices refusées.")
        self.issue_text.configure(state="normal")
        self.issue_text.delete("1.0", "end")
        self.issue_text.insert("end", "\n".join(f"• {n}" for n in notes))
        self.issue_text.configure(state="disabled")
        self.update_hints()
        self.draw_bars()
        self.set_status(f"Dossier {self.dossier_id[:6]} · enregistrement automatique")

    def update_hints(self):
        text = self.vars["phd_date"].get().strip()
        if self.track.get() != "HU" or not text:
            self.phd_hint.configure(text="JJ/MM/AAAA" if self.track.get() == "HU" else "", fg=MUTED)
        elif parse_date(text):
            self.phd_hint.configure(text="✔ date valide", fg=GREEN)
        else:
            self.phd_hint.configure(text="✘ format invalide", fg=RED)
        years = self.vars["effective_years"].get().strip().replace(",", ".")
        try:
            ok = bool(years) and float(years) >= 0
        except ValueError:
            ok = False
        self.years_hint.configure(text="" if not years else ("✔" if ok else "✘ nombre attendu"), fg=GREEN if ok else RED)

    def draw_bars(self):
        canvas = self.bars
        canvas.delete("all")
        if not self.result:
            return
        limits = self.result["thresholds"]
        width = max(canvas.winfo_width(), S(200))
        if not limits:
            canvas.create_text(S(4), S(26), anchor="w", width=width - S(8), fill=MUTED, font=("Segoe UI", 9, "italic"),
                               text="Habilitation : aucun seuil de points n'est publié par l'arrêté 804 ; le minimum est fixé par la commission régionale.")
            return
        for row, (label, value, target, color) in enumerate((("Pédagogie", self.result["pedagogy"], limits["pedagogy"], BLUE),
                                                              ("Recherche", self.result["research"], limits["research"], GREEN))):
            y = S(3) + row * S(26)
            left, right = S(84), width - S(112)
            canvas.create_text(S(2), y + S(9), anchor="w", text=label, fill=TEXT, font=("Segoe UI", 10, "bold"))
            canvas.create_rectangle(left, y, right, y + S(18), fill="#e1e8f0", outline="")
            done = value >= target
            canvas.create_rectangle(left, y, left + (right - left) * min(1, value / target), y + S(18), fill=GREEN if done else color, outline="")
            canvas.create_text(right + S(8), y + S(9), anchor="w", text=f"{fmt(value)} / {target}", fill=GREEN if done else RED, font=("Segoe UI", 10, "bold"))

    # ---------------------------------------------------------------- guide
    def show_guide(self):
        win = tk.Toplevel(self)
        win.title("Guide et barèmes")
        win.geometry(f"{S(900)}x{S(700)}")
        win.configure(bg=BG)
        GradientBar(win, S(8), BLUE, PURPLE).pack(fill="x")
        box = tk.Text(win, wrap="word", font=("Segoe UI", 11), bg="white", relief="flat", padx=S(18), pady=S(14))
        box.pack(fill="both", expand=True, padx=S(10), pady=S(10))
        box.tag_configure("h1", font=("Segoe UI", 15, "bold"), foreground=PURPLE, spacing3=S(6))
        box.tag_configure("h2", font=("Segoe UI", 12, "bold"), foreground=BLUE, spacing1=S(10), spacing3=S(3))
        box.tag_configure("b", font=("Segoe UI", 11, "bold"))
        rows = [("h1", "Guide d'utilisation\n"),
                ("h2", "Comment procéder\n"),
                ("", "1. Choisissez le parcours (habilitation ou CUN 54) et renseignez le profil.\n2. Ajoutez chaque activité (les publications une par une, avec position d'auteur et classement confirmé).\n3. Lisez le bilan à droite : conditions de recevabilité, points et rappels.\n4. « Aperçu PDF » affiche le rapport avant export ; « Rapport PDF » l'enregistre. Tout est sauvegardé automatiquement.\n"),
                ("h2", "Habilitation universitaire — arrêté 804 du 14/07/2021, art. 7\n"),
                ("", "• Être maître de conférences classe B.\n• Trois (3) ans d'activité effective au minimum.\n• Doctorat depuis au moins un (1) an.\n• Dossier déposé dans la filière du doctorat.\n• Auteur principal d'au moins une (1) publication hors thèse, soumise et publiée après la soutenance (rang A ou B en S&T ; A, B ou C en SHS).\n• Aucun seuil de points n'est publié : la commission régionale fixe le minimum après délibération.\n"),
                ("h2", "Professeur — conditions et grille CUN 54 (mai 2026)\n"),
                ("", "• Cinq (5) ans d'exercice effectif comme maître de conférences A.\n• S&T : 1 publication A+ (principal ou 2e), ou 1 A + 2 B (principal ou 2e).\n• SHS : 1 A, ou 1 B + 1 C (principal ou 2e), ou 2 C (auteur principal).\n• Encadrement : 1 thèse de doctorat soutenue (ou co-encadrée), ou 2 magisters, ou 4 masters.\n• Pédagogie ≥ 80 pts ; recherche ≥ 230 pts (S&T) ou ≥ 120 pts (SHS).\n"),
                ("h2", "Rangs des co-auteurs\n"),
                ("", "1er auteur ou auteur unique : 100 % · 2e auteur : 50 % · 3e auteur et au-delà : 25 % (100 % pour tous si l'ordre alphabétique est de règle, à justifier). Habilitation : la publication obligatoire (auteur principal, après la thèse, hors thèse) est exceptée et créditée à 100 %.\n"),
                ("h2", "Précautions\n"),
                ("", "Les revues prédatrices ou non reconnues par la DGRSDT ne sont pas acceptées. Le programme ne consulte aucune base externe : « Classement confirmé » engage l'utilisateur. Le bilan est indicatif ; la décision appartient aux instances compétentes.\n"),
                ("h2", "Sources officielles (dossier « references »)\n"),
                ("", "Arrêté MESRS n° 804 du 14/07/2021 (annexe 1) · Décret exécutif n° 21-50 du 28/01/2021 · Conditions et grille CUN 54, mai 2026.\n\n"),
                ("b", f"Réalisé par : {AUTHOR}  |  {EMAIL}\n")]
        for tag, text in rows:
            box.insert("end", text, tag)
        box.configure(state="disabled")
        make_button(win, "Fermer", SLATE, win.destroy, size=10, padx=24, pady=6).pack(pady=(0, S(10)))

    # ---------------------------------------------------------------- PDF
    def report_data(self):
        profile = self.profile()
        return profile, evaluate(profile, self.items)

    def export_pdf(self):
        stub = (self.vars["name"].get().strip().replace(" ", "_") or "candidat")
        target = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                                               initialfile=f"Rapport_promotion_{stub}_{datetime.now():%Y%m%d_%H%M}.pdf")
        if not target:
            return
        try:
            profile, result = self.report_data()
            Path(target).write_bytes(pdf_bytes(profile, self.items, result))
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"Erreur lors de la création du PDF : {exc}")
            return
        self.set_status(f"Rapport enregistré : {Path(target).name}")
        if messagebox.askyesno(APP_NAME, "Rapport PDF créé. Voulez-vous l'ouvrir maintenant ?"):
            os.startfile(target)

    def preview_pdf(self):
        try:
            profile, result = self.report_data()
            data = pdf_bytes(profile, self.items, result)
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"Aperçu indisponible : {exc}")
            return
        try:
            import fitz
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception:  # sans PyMuPDF : lecteur PDF par défaut
            path = Path(tempfile.gettempdir()) / "apercu_promotion.pdf"
            path.write_bytes(data)
            os.startfile(path)
            return
        win = tk.Toplevel(self)
        win.title("Aperçu du rapport PDF")
        win.geometry(f"{min(S(1000), self.winfo_screenwidth() - 60)}x{int(self.winfo_screenheight() * .9)}+40+20")
        win.configure(bg=NAVY)
        toolbar = tk.Frame(win, bg=NAVY, padx=S(8), pady=S(6))
        toolbar.pack(fill="x")
        holder = tk.Frame(win, bg="#5d6d7e")
        holder.pack(fill="both", expand=True)
        canvas = tk.Canvas(holder, bg="#5d6d7e", highlightthickness=0)
        scroll = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        state = {"zoom": 1.0, "job": None}
        info = tk.Label(toolbar, bg=NAVY, fg="white", font=("Segoe UI", 10, "bold"))
        info.pack(side="right", padx=S(8))
        win.images = []

        def render():
            canvas.delete("all")
            win.images.clear()
            width = max(S(300), canvas.winfo_width() - S(40))
            y = S(14)
            for page in doc:
                factor = width / page.rect.width * state["zoom"]
                pix = page.get_pixmap(matrix=fitz.Matrix(factor, factor), alpha=False)
                image = tk.PhotoImage(data=pix.tobytes("ppm"))
                win.images.append(image)
                x = max(S(14), (canvas.winfo_width() - pix.width) // 2)
                canvas.create_rectangle(x + S(4), y + S(4), x + pix.width + S(4), y + pix.height + S(4), fill="#3f4b58", outline="")
                canvas.create_image(x, y, image=image, anchor="nw")
                y += pix.height + S(14)
            canvas.configure(scrollregion=(0, 0, max(canvas.winfo_width(), int(width * state["zoom"]) + S(40)), y))
            info.configure(text=f"{len(doc)} page(s) · zoom {state['zoom']:.0%}")

        def zoom(delta):
            state["zoom"] = min(2.5, max(.5, state["zoom"] + delta))
            render()

        def open_external():
            path = Path(tempfile.gettempdir()) / "apercu_promotion.pdf"
            path.write_bytes(data)
            os.startfile(path)

        def close():
            doc.close()
            win.destroy()

        for text, color, action in (("−  Zoom", BLUE, lambda: zoom(-.25)), ("＋  Zoom", BLUE, lambda: zoom(.25)),
                                    ("Actualiser", GREEN, lambda: (close(), self.preview_pdf())),
                                    ("Ouvrir dans le lecteur", ORANGE, open_external),
                                    ("Enregistrer le PDF", RED, lambda: (close(), self.export_pdf())),
                                    ("Fermer", SLATE, close)):
            make_button(toolbar, text, color, action, size=10, padx=14, pady=5).pack(side="left", padx=(0, S(6)))
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120) * 3, "units"))
        win.bind("<Configure>", lambda _e: (state["job"] and win.after_cancel(state["job"]), state.update(job=win.after(250, render))))
        win.protocol("WM_DELETE_WINDOW", close)
        win.update_idletasks()
        render()

    def close(self):
        if self._save_job is not None:
            self.after_cancel(self._save_job)
        try:
            self.save()
        finally:
            self.destroy()


if __name__ == "__main__":
    App().mainloop()
