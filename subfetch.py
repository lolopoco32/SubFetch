#!/usr/bin/env python3
"""SubFetch - căutare, descărcare și redare subtitrări."""
import argparse
import gzip
import io
import json
import os
import queue
import re
import shutil
import struct
import subprocess
import threading
import tkinter as tk
import urllib.error
import urllib.parse as up
import urllib.request
import webbrowser
import zipfile
from tkinter import filedialog, messagebox, ttk

APP = "SubFetch"
UA = "Mozilla/5.0 (X11; Linux x86_64) %s/2.0" % APP
TIMEOUT = 20
PER_SOURCE = 40  # maxim rezultate afișate per sursă
RIGHT_W = 270    # lățimea fixă a panoului din dreapta
CONFIG_PATH = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "subfetch.json")
VIDEO_EXT = (".mkv", ".mp4", ".avi", ".mov", ".webm", ".m4v", ".mpg", ".mpeg", ".wmv", ".flv", ".ts")
SUB_EXT = (".srt", ".sub", ".ass", ".ssa", ".vtt")
FIX_RO = str.maketrans({"º": "ș", "ª": "Ș", "þ": "ț", "Þ": "Ț", "\u015f": "ș", "\u015e": "Ș", "\u0163": "ț", "\u0162": "Ț"})

# nume afișat: (cod 2 litere, cod 3 litere, nume englezesc)
SEARCH_LANGS = {
    "Română": ("ro", "rum", "Romanian"), "English": ("en", "eng", "English"),
    "Italiano": ("it", "ita", "Italian"), "Magyar": ("hu", "hun", "Hungarian"),
    "Français": ("fr", "fre", "French"), "Deutsch": ("de", "ger", "German"),
    "Español": ("es", "spa", "Spanish"),
}
UI_LANGS = ["Română", "English", "Italiano"]

STRINGS = {
    "Română": {
        "title": "SubFetch – căutare subtitrări", "drop": "⤓\n\nTrage aici filmul\nsau dă clic pentru a-l alege",
        "drop_unavailable": "Drag & drop indisponibil –\ndă clic aici pentru a alege filmul",
        "search_lbl": "Caută:", "search_lang_lbl": "Limbă căutare:", "ui_lang_lbl": "Interfață:",
        "sources_title": "Sursă subtitrări", "btn_search": "🔍 Caută", "diacritics": "Corectează diacritice", "col_title": "Titlu", "col_release": "Release / fișier", "col_downloads": "Desc.",
        "player": "Player video:", "btn_play": "▶ Descarcă și redă", "btn_download": "📥 Doar descarcă",
        "calc_hash": "Calculez hash-ul și caut…", "no_video_drop": "Ce ai selectat nu este un fișier video.",
        "file_not_found": "Fișier inexistent: %s",
        "searching": "Se caută pe OpenSubtitles…", "results_count": "%d rezultate", "waiting": " – mai aștept…",
        "choose_sub": "Alege mai întâi o subtitrare din listă.", "downloading": "Se descarcă…", "saved": "Salvat: %s",
        "error_dl": "Eroare la descărcare: %s", "error_play": "Eroare la pornirea playerului: %s",
        "no_player": "Nu a fost selectat sau găsit niciun player video.",
        "sub_loaded": "Subtitrare încărcată / redare pornită.", "choose_film": "Alege filmul",
        "imdb_btn": "🎬 Informații IMDB", "imdb_error": "Alege mai întâi un film pentru a căuta pe IMDB."
    },
    "English": {
        "title": "SubFetch – Subtitle Search", "drop": "⤓\n\nDrop movie here\nor click to browse",
        "drop_unavailable": "Drag & drop unavailable –\nclick here to browse movie",
        "search_lbl": "Search:", "search_lang_lbl": "Search lang:", "ui_lang_lbl": "Interface:",
        "sources_title": "Subtitle source", "btn_search": "🔍 Search", "diacritics": "Fix diacritics", "col_title": "Title", "col_release": "Release / file", "col_downloads": "Dl.",
        "player": "Video player:", "btn_play": "▶ Download and play", "btn_download": "📥 Download only",
        "calc_hash": "Calculating hash and searching…", "no_video_drop": "Selected item is not a video file.",
        "file_not_found": "File not found: %s",
        "searching": "Searching OpenSubtitles…", "results_count": "%d results", "waiting": " – still waiting…",
        "choose_sub": "Choose a subtitle from the list first.", "downloading": "Downloading…", "saved": "Saved: %s",
        "error_dl": "Download error: %s", "error_play": "Player launch error: %s",
        "no_player": "No video player selected or found.",
        "sub_loaded": "Subtitle loaded / playback started.", "choose_film": "Choose movie",
        "imdb_btn": "🎬 IMDB Info", "imdb_error": "Choose a movie first to search on IMDB."
    },
    "Italiano": {
        "title": "SubFetch – Ricerca Sottotitoli", "drop": "⤓\n\nTrascina qui il film\no clicca per sfogliare",
        "drop_unavailable": "Trascina e rilascia non disponibile –\nclicca qui per scegliere",
        "search_lbl": "Cerca:", "search_lang_lbl": "Lingua cerca:", "ui_lang_lbl": "Interfaccia:",
        "sources_title": "Fonte sottotitoli", "btn_search": "🔍 Cerca", "diacritics": "Correggi diacritici", "col_title": "Titolo", "col_release": "Release / file", "col_downloads": "Scaric.",
        "player": "Player video:", "btn_play": "▶ Scarica e riproduci", "btn_download": "📥 Scarica solo",
        "calc_hash": "Calcolo hash e ricerca…", "no_video_drop": "Il file selezionato non è un video.",
        "file_not_found": "File non trovato: %s",
        "searching": "Ricerca su OpenSubtitles…", "results_count": "%d risultati", "waiting": " – attendo…",
        "choose_sub": "Scegli prima un sottotitolo.", "downloading": "Download in corso…", "saved": "Salvato: %s",
        "error_dl": "Errore download: %s", "error_play": "Errore avvio player: %s",
        "no_player": "Nessun player video selezionato o trovato.",
        "sub_loaded": "Sottotitolo caricato / riproduzione avviata.", "choose_film": "Scegli film",
        "imdb_btn": "🎬 Informazioni IMDB", "imdb_error": "Scegli prima un film per cercare su IMDB."
    },
}

COLS = (("title", 260, True), ("release", 300, True), ("downloads", 60, False))

PLAYERS = {
    "mpv (sistem)": ["mpv"], "mpv (flatpak)": ["flatpak", "run", "io.mpv.Mpv"],
    "VLC": ["vlc"], "VLC (flatpak)": ["flatpak", "run", "org.videolan.VLC"],
    "Celluloid": ["celluloid"], "Celluloid (flatpak)": ["flatpak", "run", "io.github.celluloid_player.Celluloid"],
    "SMPlayer": ["smplayer"], "Totem (GNOME Videos)": ["totem"], "MPlayer": ["mplayer"],
}


# ============================== CONFIGURARE ==============================
def load_config():
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f)
    except Exception:
        pass


# ============================== FURNIZORI ================================
def http_get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def http_text(url, headers=None):
    return http_get(url, headers).decode("utf-8", "replace")


def http_json(url, headers=None):
    return json.loads(http_text(url, headers))


def getter(url, ua=None):
    return lambda: http_get(url, {"User-Agent": ua} if ua else None)


def item(title, release="", downloads="", fetch=None, exact=False):
    return {"title": title, "release": release, "downloads": str(downloads),
            "fetch": fetch, "exact": exact}


# API-ul vechi OpenSubtitles verifică antetul User-Agent; "TemporaryUserAgent" este cel acceptat pentru teste.
OS_AGENTS = ("TemporaryUserAgent", "trailers.to-UA")


def os_api_get(url):
    """Interoghează API-ul; la HTTP 401 încearcă următorul User-Agent. Returnează (json, agent_ok)."""
    last = None
    for ua in OS_AGENTS:
        try:
            return http_json(url, {"User-Agent": ua, "X-User-Agent": ua}), ua
        except urllib.error.HTTPError as e:
            last = e
            if e.code != 401:
                raise
    raise last


def opensubtitles_api(c):
    base = "https://rest.opensubtitles.org/search/"
    paths = []
    if c["vhash"]:
        paths.append(("moviebytesize-%d/moviehash-%s/sublanguageid-%s" % (c["vsize"], c["vhash"], c["l3"]), True))
    paths.append(("query-%s/sublanguageid-%s" % (up.quote(c["query"].lower()), c["l3"]), False))
    out, seen = [], set()
    for path, exact in paths:
        try:
            data, ua = os_api_get(base + path)
        except Exception:
            if not exact:
                raise
            continue
        for it in data:
            sid, link = it.get("IDSubtitleFile"), it.get("SubDownloadLink")
            if sid in seen or not link:
                continue
            seen.add(sid)
            name = it.get("MovieName") or it.get("SubFileName", "")
            out.append(item(("★ " if exact else "") + name,
                            it.get("MovieReleaseName") or it.get("SubFileName", ""),
                            it.get("SubDownloadsCnt", ""), getter(link, ua), exact))
    return out


SOURCES = (opensubtitles_api,)


def imdb_lookup(q):
    """Sugestii IMDb pentru un titlu: listă de intrări cu id 'tt...' (conțin id, titlu, poster în 'i')."""
    q = q.strip().lower()
    first = next((ch for ch in q if ch.isascii() and ch.isalnum()), "a")
    data = http_json("https://v2.sg.media-imdb.com/suggestion/%s/%s.json" % (first, up.quote(q)))
    return [d for d in data.get("d", []) if str(d.get("id", "")).startswith("tt")]


def strip_year(q):
    return re.sub(r"\s+", " ", re.sub(r"[\(\[]?\b(19|20)\d{2}\b[\)\]]?", " ", q)).strip() or q


def poster_urls(query):
    """Generator de URL-uri de poster, în ordinea surselor (IMDb, TVMaze, iTunes). Excepțiile le tratează apelantul."""
    try:
        for d in imdb_lookup(query):
            url = (d.get("i") or {}).get("imageUrl")
            if url:
                yield url, d.get("id")
                break
    except Exception:
        pass
    clean = strip_year(query)
    try:
        for r in http_json("https://api.tvmaze.com/search/shows?q=" + up.quote(clean))[:1]:
            img = (r.get("show") or {}).get("image") or {}
            if img.get("original") or img.get("medium"):
                yield img.get("original") or img.get("medium"), None
    except Exception:
        pass
    try:
        for r in http_json("https://itunes.apple.com/search?media=movie&limit=1&term=" + up.quote(clean)).get("results", []):
            if r.get("artworkUrl100"):
                yield r["artworkUrl100"].replace("100x100bb", "600x600bb"), None
    except Exception:
        pass


# ============================== UTILITARE ================================
def find_players():
    def ok(cmd):
        if not shutil.which(cmd[0]):
            return False
        if cmd[0] != "flatpak":
            return True
        try:
            return subprocess.run(["flatpak", "info", cmd[-1]], capture_output=True, timeout=5).returncode == 0
        except Exception:
            return False
    return {n: c for n, c in PLAYERS.items() if ok(c)}


def opensubtitles_hash(path):
    size = os.path.getsize(path)
    if size < 65536 * 2:
        return None, size
    fmt, h = "<%dQ" % (65536 // 8), size
    with open(path, "rb") as f:
        h += sum(struct.unpack(fmt, f.read(65536)))
        f.seek(size - 65536)
        h += sum(struct.unpack(fmt, f.read(65536)))
    return "%016x" % (h & 0xFFFFFFFFFFFFFFFF), size


def guess_query(path):
    s = re.sub(r"[._]+", " ", os.path.splitext(os.path.basename(path))[0])
    ep = re.search(r"\bS\d{1,2}E\d{1,2}\b", s, re.I)
    if ep:
        return s[:ep.end()].strip()
    return re.split(r"\b(720p|1080p|2160p|WEB|BluRay|BRRip|HDRip|x264|x265|HDTV)\b", s, flags=re.I)[0].strip()


def decode_sub(raw):
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    elif raw[:2] == b"PK":
        z = zipfile.ZipFile(io.BytesIO(raw))
        names = [n for n in z.namelist() if n.lower().endswith(SUB_EXT)]
        if names:
            raw = z.read(names[0])
    for enc in ("utf-8-sig", "cp1250", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1")


# ================================ INTERFAȚA ==============================
class App(tk.Tk):
    def __init__(self, video):
        super().__init__()
        self.cfg = load_config()
        self.video, self.results, self.errors = "", [], []
        self.vhash, self.vsize = None, 0
        self.gen = self.pending = 0
        self.sort = (None, False)
        self.dnd_ok = True
        self.texts = {}
        self.uiq = queue.Queue()
        self.players = find_players()
        self.poster_img = None
        self.poster_gen = 0
        self.imdb_id = None
        self.minsize(1000, 750)
        self.geometry("1060x750")
        try:
            self.icon_img = tk.PhotoImage(file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png"))
            self.iconphoto(True, self.icon_img)
        except Exception:
            pass

        ui = self.cfg.get("ui_lang")
        ui = ui if ui in STRINGS else "Română"
        sl = self.cfg.get("search_lang")
        self.ui_lang_var = tk.StringVar(value=ui)
        self.search_lang_var = tk.StringVar(value=sl if sl in SEARCH_LANGS else ui)
        self.fix_var = tk.BooleanVar(value=self.cfg.get("fix_diacritics", ui == "Română"))

        self.build_ui()
        self.after(100, self.poll)
        if video:
            self.set_video(video)

    @property
    def s(self):
        return STRINGS[self.ui_lang_var.get()]

    def mk(self, cls, parent, key=None, **kw):
        w = cls(parent, **kw)
        if key:
            self.texts[key] = w
        return w

    def style(self):
        st = ttk.Style(self)
        bg = st.lookup("TFrame", "background") or self.cget("bg")
        st.map("Treeview", background=[("selected", "#3d7ab8")], foreground=[("selected", "#ffffff")])
        return bg

    def build_ui(self):
        bg = self.style()
        root = ttk.Frame(self, padding=8)
        root.pack(fill="both", expand=True)
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=0, minsize=RIGHT_W)

        left = ttk.Frame(root)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        right = ttk.Frame(root, width=RIGHT_W)
        right.grid(row=0, column=1, sticky="ns")
        right.pack_propagate(False)

        # --- dreapta ---
        self.mk(ttk.Label, right, "ui_lang_lbl").pack(anchor="w", pady=(0, 2))
        cb = ttk.Combobox(right, textvariable=self.ui_lang_var, values=UI_LANGS, state="readonly")
        cb.pack(fill="x", pady=(0, 8))
        cb.bind("<<ComboboxSelected>>", self.on_ui_lang_changed)

        self.mk(ttk.Label, right, "player").pack(anchor="w", pady=(0, 2))
        self.player_cb = ttk.Combobox(right, values=list(self.players), state="readonly")
        self.player_cb.pack(fill="x", pady=(0, 8))
        if self.players:
            self.player_cb.set(next(iter(self.players)))

        self.dl_btn = self.mk(ttk.Button, right, "btn_download", command=lambda: self.download(False))
        self.dl_btn.pack(fill="x", pady=(0, 4))
        self.play_btn = self.mk(ttk.Button, right, "btn_play", command=lambda: self.download(True))
        self.play_btn.pack(fill="x", pady=(0, 6))
        self.mk(ttk.Checkbutton, right, "diacritics", variable=self.fix_var, command=self.save_cfg).pack(anchor="w", pady=(0, 8))

        # Suprafața mare de Drop / Poster pe verticală
        self.drop_lbl = tk.Label(right, relief="groove", bd=2, cursor="hand2", justify="center", wraplength=RIGHT_W - 30)
        self.drop_lbl.pack(fill="both", expand=True, pady=(4, 8))
        self.drop_lbl.bind("<Button-1>", lambda e: self.pick_file())

        # Elemente împinse jos în dreapta
        self.logo = tk.Canvas(right, height=30, bg=bg, highlightthickness=0)
        self.logo.pack(side="bottom", fill="x")
        self.logo.bind("<Configure>", self.draw_logo)

        box = self.mk(ttk.LabelFrame, right, "sources_title", padding=8, labelanchor="n")
        box.pack(side="bottom", fill="x", pady=(8, 4))
        ttk.Label(box, text="OpenSubtitles", anchor="center", justify="center").pack(fill="x")

        # Buton Informații IMDB fixat deasupra sursei subtitrări
        self.imdb_btn = self.mk(ttk.Button, right, "imdb_btn", command=self.open_imdb)
        self.imdb_btn.pack(side="bottom", fill="x", pady=(0, 4))
        self.imdb_btn.state(["disabled"])  # activ abia după ce este ales un film

        # --- stânga ---
        bar = ttk.Frame(left)
        bar.pack(fill="x", pady=(0, 6))
        self.mk(ttk.Label, bar, "search_lbl").pack(side="left", padx=(0, 4))
        self.q_var = tk.StringVar()
        entry = ttk.Entry(bar, textvariable=self.q_var)
        entry.pack(side="left", fill="x", expand=True, padx=4)
        entry.bind("<Return>", lambda e: self.search())
        entry.bind("<Key>", lambda e: setattr(self, "imdb_id", None) if e.keysym != "Return" else None)
        self.mk(ttk.Label, bar, "search_lang_lbl").pack(side="left", padx=(6, 4))
        lang_cb = ttk.Combobox(bar, textvariable=self.search_lang_var, values=list(SEARCH_LANGS), state="readonly", width=10)
        lang_cb.pack(side="left", padx=4)
        lang_cb.bind("<<ComboboxSelected>>", lambda e: (self.save_cfg(), self.search()))
        self.mk(ttk.Button, bar, "btn_search", command=self.search).pack(side="left", padx=(4, 0))

        holder = ttk.Frame(left)
        holder.pack(fill="both", expand=True, pady=(0, 4))
        self.tree = ttk.Treeview(holder, columns=[c[0] for c in COLS], show="headings", selectmode="browse")
        for col, width, stretch in COLS:
            self.tree.column(col, width=width, minwidth=40, stretch=stretch, anchor="w")
        scroll = ttk.Scrollbar(holder, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda e: self.tree.identify_region(e.x, e.y) == "cell" and self.download(True))
        self.tree.bind("<Return>", lambda e: self.download(True))

        self.status = tk.StringVar()
        ttk.Label(left, textvariable=self.status, anchor="w", padding=(0, 4, 0, 0)).pack(fill="x")

        self.setup_dnd()
        self.update_texts()
        self.update_dl_buttons()

    def draw_logo(self, _=None):
        w = self.logo.winfo_width()
        self.logo.delete("all")
        for dx, y, color in ((2, 16, "#ffffff"), (4, 14, "#808080"), (3, 15, "#505050")):
            self.logo.create_text(w - dx, y, text=APP, font=("Helvetica", 13, "bold"), fill=color, anchor="e")

    def update_dl_buttons(self):
        """Butoanele de descărcare sunt active doar dacă există un film încărcat ȘI cel puțin un rezultat în listă."""
        ready = bool(self.video) and bool(self.tree.get_children())
        for b in (self.dl_btn, self.play_btn):
            b.state(["!disabled"] if ready else ["disabled"])

    def update_texts(self):
        s = self.s
        self.title(s["title"])
        for key, w in self.texts.items():
            w.config(text=s[key])
        if not self.video:
            self.drop_lbl.config(text=s["drop"] if self.dnd_ok else s["drop_unavailable"], image="")
        self.update_headings()

    def update_headings(self):
        col_sorted, desc = self.sort
        for col, _, _ in COLS:
            arrow = (" ▼" if desc else " ▲") if col == col_sorted else ""
            self.tree.heading(col, text=self.s["col_" + col] + arrow, command=lambda c=col: self.sort_by(c))

    def on_ui_lang_changed(self, _=None):
        lang = self.ui_lang_var.get()
        self.search_lang_var.set(lang)
        self.fix_var.set(lang == "Română")
        self.update_texts()
        self.save_cfg()
        if self.video:
            self.search()

    def save_cfg(self):
        self.cfg.update(ui_lang=self.ui_lang_var.get(), search_lang=self.search_lang_var.get(),
                        fix_diacritics=self.fix_var.get())
        save_config(self.cfg)

    # ---- drag & drop / alegere fișier ----
    def setup_dnd(self):
        try:
            try:
                from tkinterdnd2 import TkinterDnD
                TkinterDnD._require(self)
            except ImportError:
                self.tk.call("package", "require", "tkdnd")

            drop = self.register(self.on_drop)
            for w in (self.drop_lbl, self):
                try:
                    self.tk.call("tkdnd::drop_target", "register", w._w, ("DND_Files", "DND_Text"))
                    self.tk.call("bind", w._w, "<<Drop>>", drop + " %D")
                except tk.TclError:
                    pass
        except tk.TclError:
            self.dnd_ok = False

        self.update_idletasks()

    def on_drop(self, *args):
        try:
            paths = [p.strip().strip("'\"") for p in self.tk.splitlist(args[0])] if args else []
            vids = [p for p in paths if os.path.isfile(p) and p.lower().endswith(VIDEO_EXT)]
            if vids:
                self.set_video(vids[0])
            else:
                self.status.set(self.s["no_video_drop"])
        except Exception as e:
            self.status.set("Drag & drop error: %s" % e)
        return "copy"

    def pick_file(self):
        p = filedialog.askopenfilename(title=self.s["choose_film"])
        if p:
            self.set_video(p)

    def set_video(self, path):
        path = path.strip().strip("'\"")
        if not os.path.isfile(path):
            self.status.set(self.s["file_not_found"] % path)
            return
        self.video = path
        base_name = os.path.basename(path)
        if len(base_name) > 28:
            base_name = base_name[:25] + "..."

        self.q_var.set(guess_query(path))
        
        self.imdb_btn.state(["!disabled"])
        self.imdb_id = None
        self.poster_img = None
        self.poster_gen += 1
        self.drop_lbl.config(image="", text="⏳ Se descarcă posterul...")
        threading.Thread(target=self._fetch_poster_worker, args=(self.poster_gen, self.q_var.get(), base_name),
                         daemon=True).start()

        self.status.set(self.s["calc_hash"])
        threading.Thread(target=self._hash_then_search, daemon=True).start()

    def _fetch_poster_worker(self, gen, query, fallback_name):
        raw, imdb_id = None, None
        for url, iid in poster_urls(query):
            imdb_id = imdb_id or iid
            try:
                data = http_get(url)
                if data:
                    raw = data
                    break
            except Exception:
                continue
        self.ui(self._show_poster, gen, raw, imdb_id, fallback_name)

    def _show_poster(self, gen, raw, imdb_id, fallback_name):
        # rulează în firul principal (Tk nu e thread-safe, inclusiv pentru PhotoImage)
        if gen != self.poster_gen:
            return
        self.imdb_id = imdb_id
        if raw:
            try:
                from PIL import Image, ImageTk
                img = Image.open(io.BytesIO(raw)).convert("RGB")
                w = max(self.drop_lbl.winfo_width() - 8, 120)
                h = max(self.drop_lbl.winfo_height() - 8, 160)
                img.thumbnail((w, h), Image.Resampling.LANCZOS)
                self.poster_img = ImageTk.PhotoImage(img)
                self.drop_lbl.config(text="", image=self.poster_img)
                return
            except ImportError:
                self.status.set("Pentru poster instalează Pillow:  pip install pillow")
            except Exception:
                pass
        self.drop_lbl.config(image="", text="🎬\n\n" + fallback_name)

    def open_imdb(self):
        if not self.video:
            return
        q = self.q_var.get().strip() or guess_query(self.video)
        known = self.imdb_id

        def work():
            iid = known
            if not iid:
                try:
                    hits = imdb_lookup(q)
                    iid = hits[0]["id"] if hits else None
                except Exception:
                    iid = None
            url = ("https://www.imdb.com/title/%s/" % iid) if iid else \
                  ("https://www.imdb.com/find/?q=" + up.quote_plus(q) + "&s=tt")
            self.ui(webbrowser.open, url)
        threading.Thread(target=work, daemon=True).start()

    def _hash_then_search(self):
        try:
            self.vhash, self.vsize = opensubtitles_hash(self.video)
        except Exception:
            self.vhash, self.vsize = None, 0
        self.ui(self.search)

    # ---- căutare ----
    def search(self):
        q = self.q_var.get().strip()
        if not q or not self.video:
            return
        self.tree.delete(*self.tree.get_children())
        self.update_dl_buttons()
        self.results, self.errors, self.gen = [], [], self.gen + 1
        l2, l3, lname = SEARCH_LANGS[self.search_lang_var.get()]
        ctx = {"query": q, "l2": l2, "l3": l3, "lname": lname, "vhash": self.vhash, "vsize": self.vsize}
        self.pending = len(SOURCES)
        self.status.set(self.s["searching"])
        for fn in SOURCES:
            threading.Thread(target=self._run_source, args=(self.gen, fn, ctx), daemon=True).start()

    def _run_source(self, gen, fn, ctx):
        res, err = [], None
        try:
            res = fn(ctx)
        except urllib.error.HTTPError as e:
            err = None if e.code == 404 else "OpenSubtitles: HTTP %d" % e.code
        except Exception as e:
            err = str(e)[:80]
        self.ui(self._done_source, gen, res, err)

    def _done_source(self, gen, res, err):
        if gen != self.gen:
            return
        new = []
        for rank, r in enumerate(res[:PER_SOURCE]):
            r["rank"] = rank
            iid = str(len(self.results))
            self.results.append(r)
            self.tree.insert("", "end", iid=iid, values=[r[c[0]] for c in COLS])
            new.append(iid)
        self.resort()
        self.update_dl_buttons()
        kids = self.tree.get_children()
        pick = next((i for i in new if self.results[int(i)]["exact"]), None) or (kids[0] if kids and not self.tree.selection() else None)
        if pick:
            self.tree.selection_set(pick)
            self.tree.see(pick)

        if err:
            self.errors.append(err)
        self.pending -= 1
        msg = self.s["results_count"] % len(self.results)
        msg += self.s["waiting"] if self.pending else "."
        if self.errors:
            msg += "   ⚠ " + " · ".join(self.errors)
        self.status.set(msg)

    # ---- sortare ----
    def sort_by(self, col):
        self.sort = (col, not self.sort[1]) if self.sort[0] == col else (col, col == "downloads")
        self.resort()

    def sort_key(self, iid):
        r, col = self.results[int(iid)], self.sort[0]
        if col == "downloads":
            return int(re.sub(r"\D", "", r["downloads"]) or 0)
        if col:
            return r[col].lower()
        return (not r["exact"], r["rank"])

    def resort(self):
        for i, iid in enumerate(sorted(self.tree.get_children(), key=self.sort_key, reverse=self.sort[1])):
            self.tree.move(iid, "", i)
        self.update_headings()

    # ---- descărcare / redare ----
    def ui(self, fn, *a):
        self.uiq.put((fn, a))

    def poll(self):
        try:
            while True:
                fn, a = self.uiq.get_nowait()
                fn(*a)
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def download(self, play):
        if not self.video or not self.tree.get_children():
            return  # dublu-click / Enter în listă goală: nu e nimic de descărcat
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(APP, self.s["choose_sub"])
            return
        self.status.set(self.s["downloading"])
        threading.Thread(target=self._download_worker, args=(self.results[int(sel[0])], play), daemon=True).start()

    def _download_worker(self, r, play):
        try:
            text = decode_sub(r["fetch"]())
            if self.fix_var.get():
                text = text.translate(FIX_RO)
            dest = "%s.%s.srt" % (os.path.splitext(self.video)[0], SEARCH_LANGS[self.search_lang_var.get()][0])
            with open(dest, "w", encoding="utf-8", newline="") as f:
                f.write(text)
        except Exception as e:
            self.ui(self.status.set, self.s["error_dl"] % e)
            return
        self.ui(self.status.set, self.s["saved"] % dest)
        if play:
            self.ui(self.launch, dest)

    def launch(self, sub):
        name = self.player_cb.get()
        base = self.players.get(name)
        if not base:
            messagebox.showwarning(APP, self.s["no_player"])
            return
        extra = ["-sub", sub] if "mplayer" in name.lower() else ["--sub-file=" + sub]
        try:
            subprocess.Popen(base + [self.video] + extra, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
            self.status.set(self.s["sub_loaded"])
        except Exception as e:
            self.status.set(self.s["error_play"] % e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", nargs="?", default="")
    ap.add_argument("--socket", help=argparse.SUPPRESS)
    App(ap.parse_args().video).mainloop()


if __name__ == "__main__":
    main()