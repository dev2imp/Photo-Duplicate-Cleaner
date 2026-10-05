#!/usr/bin/env python3
"""Foto/Video ayirici + duplicate bulucu + HTML rapor.

Akis:
  1) Girdi klasorunu tara -> resim / video / diger olarak ayir
  2) Resimlerin SHA-256 (birebir) ve gorsel hash'ini (dHash, 256 bit) hesapla
  3) Benzer resimleri gruplara ayir, her gruptan EN KALITELIYI birak
  4) Dosyalari tasi/kopyala:  UniqueImages / Duplicates / Videos / Unreadable
  5) report.html olustur
Hicbir dosya SILINMEZ. Duplicate'ler Duplicates klasorune tasinir.
"""
import argparse
import hashlib
import html
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image, ImageOps

try:  # iPhone .heic destegi (opsiyonel)
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass

Image.MAX_IMAGE_PIXELS = None

IMG_EXT = {".jpg", ".jpeg", ".jpe", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff", ".heic", ".heif"}
VID_EXT = {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v", ".3gp", ".mpg", ".mpeg", ".mts", ".m2ts"}
HASH_BITS = 16  # 16x16 = 256 bit


# ------------------------------------------------------------------ analiz
def analyze(path):
    """Tek bir resmi analiz eder (alt surecte calisir)."""
    res = {"path": path, "size": 0, "w": 0, "h": 0, "sha": "", "hash": 0, "err": ""}
    try:
        res["size"] = os.path.getsize(path)
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        res["sha"] = h.hexdigest()

        with Image.open(path) as im:
            w, h0 = im.size
            try:
                orient = im.getexif().get(0x0112, 1)
            except Exception:
                orient = 1
            if orient in (5, 6, 7, 8):
                w, h0 = h0, w
            res["w"], res["h"] = w, h0
            try:
                im.draft("RGB", (256, 256))  # JPEG'i kucuk okuyarak hizlandir
            except Exception:
                pass
            im = ImageOps.exif_transpose(im)
            g = im.convert("L").resize((HASH_BITS + 1, HASH_BITS), Image.LANCZOS)
            data = g.tobytes()
        bits = 0
        for y in range(HASH_BITS):
            row = data[y * (HASH_BITS + 1):(y + 1) * (HASH_BITS + 1)]
            for x in range(HASH_BITS):
                bits = (bits << 1) | (1 if row[x] > row[x + 1] else 0)
        res["hash"] = bits
    except Exception as e:  # bozuk dosya
        res["err"] = f"{type(e).__name__}: {e}"
    return res


def make_thumb(src, dst):
    try:
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im)
            im.thumbnail((240, 240))
            im.convert("RGB").save(dst, "JPEG", quality=75)
        return True
    except Exception:
        return False


# ------------------------------------------------------------------ gruplama
class DSU:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, a):
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def cluster(items, threshold):
    n = len(items)
    dsu = DSU(n)
    hs = [it["hash"] for it in items]
    for i in range(n):
        hi = hs[i]
        for j in range(i + 1, n):
            if (hi ^ hs[j]).bit_count() <= threshold:
                dsu.union(i, j)
    groups = {}
    for i in range(n):
        groups.setdefault(dsu.find(i), []).append(items[i])
    return list(groups.values())


def quality_key(it):
    # once cozunurluk, sonra dosya boyutu, sonra kisa isim, sonra alfabetik
    return (-(it["w"] * it["h"]), -it["size"], len(it["name"]), it["name"].lower())


# ------------------------------------------------------------------ dosya islemleri
class Mover:
    def __init__(self, mode):
        self.mode = mode
        self.used = set()

    def dest(self, folder, name):
        folder = Path(folder)
        stem, ext = os.path.splitext(name)
        cand = folder / name
        k = 1
        while str(cand).lower() in self.used or (self.mode != "dry" and cand.exists()):
            cand = folder / f"{stem}_{k}{ext}"
            k += 1
        self.used.add(str(cand).lower())
        return cand

    def do(self, src, folder, name):
        d = self.dest(folder, name)
        if self.mode == "dry":
            return d
        d.parent.mkdir(parents=True, exist_ok=True)
        if self.mode == "copy":
            shutil.copy2(src, d)
        else:
            shutil.move(src, d)
        return d


def human(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}"
        n /= 1024


# ------------------------------------------------------------------ rapor
CSS = """
body{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f4f6f9;color:#222}
header{background:#1f3864;color:#fff;padding:20px 28px}
header h1{margin:0 0 4px;font-size:22px}
.wrap{padding:20px 28px;max-width:1300px;margin:auto}
.cards{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:18px}
.stat{background:#fff;border-radius:8px;padding:12px 18px;box-shadow:0 1px 3px #0002;min-width:150px}
.stat b{display:block;font-size:24px;color:#1f3864}
.banner{background:#fff3cd;border:1px solid #e0c36a;padding:10px 14px;border-radius:6px;margin-bottom:16px}
input#q{width:100%;padding:10px;font-size:15px;border:1px solid #bbb;border-radius:6px;margin-bottom:16px;box-sizing:border-box}
.group{background:#fff;border-radius:8px;box-shadow:0 1px 3px #0002;margin-bottom:16px;padding:14px}
.group h3{margin:0 0 10px;font-size:16px}
.tag{font-size:12px;padding:2px 8px;border-radius:10px;color:#fff;margin-left:6px}
.t-exact{background:#c0392b}.t-sim{background:#e67e22}
.row{display:flex;flex-wrap:wrap;gap:12px}
.item{width:260px;border:2px solid #ddd;border-radius:8px;padding:8px;font-size:12.5px;word-break:break-all}
.item.keep{border-color:#27ae60;background:#f0fbf4}
.item.moved{border-color:#e67e22;background:#fff8f0}
.item img{width:100%;height:170px;object-fit:contain;background:#eee;border-radius:4px}
.badge{display:inline-block;font-weight:600;margin:6px 0 4px}
.keep .badge{color:#1e8449}.moved .badge{color:#b9680f}
.muted{color:#666}
details{background:#fff;border-radius:8px;box-shadow:0 1px 3px #0002;margin-bottom:12px;padding:10px 14px}
summary{cursor:pointer;font-weight:600}
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:8px}
th,td{border-bottom:1px solid #e5e5e5;padding:5px 8px;text-align:left;word-break:break-all}
th{background:#eef1f6}
"""

JS = """
document.getElementById('q').addEventListener('input',function(){
  var t=this.value.toLowerCase();
  document.querySelectorAll('.group').forEach(function(g){
    g.style.display=g.textContent.toLowerCase().indexOf(t)>-1?'':'none';});
});
"""


def build_report(out_dir, ctx):
    e = html.escape
    parts = []
    parts.append(f"<!doctype html><html lang='tr'><head><meta charset='utf-8'><title>Foto Rapor</title><style>{CSS}</style></head><body>")
    parts.append(f"<header><h1>Fotoğraf / Video Düzenleme Raporu</h1><div>{e(ctx['date'])} &middot; Mod: <b>{e(ctx['mode_label'])}</b> &middot; Benzerlik eşiği: {ctx['threshold']}/256 bit</div></header><div class='wrap'>")
    if ctx["mode"] == "dry":
        parts.append("<div class='banner'><b>TEST MODU:</b> Hiçbir dosyaya dokunulmadı. Aşağıda yazanlar, gerçek çalıştırmada yapılacak işlemlerdir.</div>")

    s = ctx["stats"]
    stats = [
        ("Taranan dosya", s["total"]), ("Resim", s["images"]), ("Video", s["videos"]),
        ("Benzer grup sayısı", s["groups"]), ("Duplicate (taşınan)", s["dups"]),
        ("UniqueImages'e giden", s["unique"]), ("Diğer dosya (dokunulmadı)", s["other"]),
        ("Okunamayan resim", s["unreadable"]),
    ]
    parts.append("<div class='cards'>" + "".join(f"<div class='stat'><b>{v}</b>{e(k)}</div>" for k, v in stats) + "</div>")

    parts.append("<h2>Benzer / Duplicate Gruplar</h2>")
    if not ctx["groups"]:
        parts.append("<p class='muted'>Hiç benzer resim bulunmadı.</p>")
    else:
        parts.append("<input id='q' placeholder='Dosya adı veya klasör ara...'>")
    for g in ctx["groups"]:
        kind = "Birebir aynı" if g["exact"] else "Benzer"
        cls = "t-exact" if g["exact"] else "t-sim"
        parts.append(f"<div class='group'><h3>Grup {g['id']:04d} &mdash; {len(g['members'])} dosya <span class='tag {cls}'>{kind}</span></h3><div class='row'>")
        for m in g["members"]:
            if m["keep"]:
                badge = f"✔ KALDI &rarr; UniqueImages/{e(m['dest_name'])}"
                cls_i = "keep"
                sim = "<span class='muted'>(en kaliteli olan)</span>"
            else:
                badge = f"➜ TAŞINDI &rarr; Duplicates/{e(g['folder'])}/{e(m['dest_name'])}"
                cls_i = "moved"
                sim = f"<span class='muted'>Benzerlik: %{m['sim']:.1f}" + (" (birebir aynı dosya)" if m["same_sha"] else "") + "</span>"
            img = f"<img loading='lazy' src='report_files/thumbs/{m['id']}.jpg' alt=''>" if m["thumb"] else ""
            parts.append(
                f"<div class='item {cls_i}'>{img}<div class='badge'>{badge}</div>"
                f"<div><b>{e(m['name'])}</b></div>"
                f"<div class='muted'>{m['w']}×{m['h']} &middot; {human(m['size'])}</div>"
                f"<div class='muted'>Eski yol: {e(m['rel'])}</div>{sim}</div>"
            )
        parts.append("</div></div>")

    def table(title, head, rows, open_=False):
        o = " open" if open_ else ""
        t = f"<details{o}><summary>{e(title)} ({len(rows)})</summary><table><tr>" + "".join(f"<th>{e(h)}</th>" for h in head) + "</tr>"
        for r in rows:
            t += "<tr>" + "".join(f"<td>{e(str(c))}</td>" for c in r) + "</tr>"
        return t + "</table></details>"

    parts.append("<h2>Diğer Listeler</h2>")
    parts.append(table("UniqueImages klasörüne giden resimler", ["Yeni ad", "Eski yol", "Not"], ctx["unique_rows"]))
    parts.append(table("Videolar (Videos klasörüne)", ["Yeni ad", "Eski yol", "Boyut"], ctx["video_rows"]))
    if ctx["bad_rows"]:
        parts.append(table("Okunamayan / bozuk resimler (Unreadable klasörüne)", ["Yeni ad", "Eski yol", "Hata"], ctx["bad_rows"], True))
    parts.append(f"</div><script>{JS}</script></body></html>")
    (out_dir / "report.html").write_text("".join(parts), encoding="utf-8")


# ------------------------------------------------------------------ ana akis
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="/data/input")
    ap.add_argument("--output", default="/data/output")
    ap.add_argument("--mode", choices=["dry", "copy", "move"], default=os.environ.get("MODE", "dry"))
    ap.add_argument("--threshold", type=int, default=int(os.environ.get("THRESHOLD", "8")))
    a = ap.parse_args()

    inp, out = Path(a.input), Path(a.output)
    if not inp.is_dir():
        sys.exit(f"Girdi klasoru bulunamadi: {inp}")
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    # 1) tara
    images, videos, others = [], [], 0
    for root, _, files in os.walk(inp):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            p = os.path.join(root, f)
            if ext in IMG_EXT:
                images.append(p)
            elif ext in VID_EXT:
                videos.append(p)
            else:
                others += 1
    print(f"[1/4] Tarandi: {len(images)} resim, {len(videos)} video, {others} diger dosya", flush=True)

    # 2) analiz
    results = []
    with ProcessPoolExecutor() as ex:
        for i, r in enumerate(ex.map(analyze, images, chunksize=8), 1):
            results.append(r)
            if i % 200 == 0 or i == len(images):
                print(f"[2/4] Resim analizi: {i}/{len(images)}", flush=True)

    good, bad = [], []
    for idx, r in enumerate(results):
        r["id"] = idx
        r["name"] = os.path.basename(r["path"])
        r["rel"] = os.path.relpath(r["path"], inp)
        (bad if r["err"] else good).append(r)

    # 3) grupla
    print("[3/4] Benzerlik karsilastirmasi...", flush=True)
    groups = cluster(good, a.threshold)
    thumbs_dir = out / "report_files" / "thumbs"
    thumbs_dir.mkdir(parents=True, exist_ok=True)

    mover = Mover(a.mode)
    uniq_dir, dup_dir = out / "UniqueImages", out / "Duplicates"
    unique_rows, rep_groups = [], []
    gid = 0
    n_dups = 0
    singles = sorted([g[0] for g in groups if len(g) == 1], key=lambda x: x["rel"].lower())
    multi = sorted([g for g in groups if len(g) > 1], key=lambda g: min(m["rel"].lower() for m in g))

    # 4) tasi + rapor verisi
    print("[4/4] Dosyalar duzenleniyor ve rapor hazirlaniyor...", flush=True)
    for g in multi:
        gid += 1
        g.sort(key=quality_key)
        keeper = g[0]
        folder = f"group_{gid:04d}"
        members = []
        exact = all(m["sha"] == keeper["sha"] for m in g)
        for k, m in enumerate(g):
            thumb = make_thumb(m["path"], thumbs_dir / f"{m['id']}.jpg")
            d = (mover.do(m["path"], uniq_dir, m["name"]) if k == 0
                 else mover.do(m["path"], dup_dir / folder, m["name"]))
            dist = (keeper["hash"] ^ m["hash"]).bit_count()
            members.append({
                "id": m["id"], "name": m["name"], "rel": m["rel"], "w": m["w"], "h": m["h"],
                "size": m["size"], "keep": k == 0, "dest_name": d.name, "thumb": thumb,
                "sim": 100 * (1 - dist / (HASH_BITS * HASH_BITS)), "same_sha": m["sha"] == keeper["sha"],
            })
            if k == 0:
                unique_rows.append((d.name, m["rel"], f"Grup {gid:04d} temsilcisi (en kaliteli, {len(g)-1} benzeri taşındı)"))
            else:
                n_dups += 1
        rep_groups.append({"id": gid, "folder": folder, "exact": exact, "members": members})

    for m in singles:
        d = mover.do(m["path"], uniq_dir, m["name"])
        unique_rows.append((d.name, m["rel"], "Benzeri yok"))

    video_rows = []
    for v in sorted(videos, key=str.lower):
        d = mover.do(v, out / "Videos", os.path.basename(v))
        video_rows.append((d.name, os.path.relpath(v, inp), human(os.path.getsize(v)) if os.path.exists(v) else ""))

    bad_rows = []
    for b in bad:
        d = mover.do(b["path"], out / "Unreadable", b["name"])
        bad_rows.append((d.name, b["rel"], b["err"]))

    labels = {"dry": "TEST (dosyalar taşınmadı)", "copy": "KOPYALA (orijinaller yerinde)", "move": "TAŞI"}
    ctx = {
        "date": time.strftime("%d.%m.%Y %H:%M"), "mode": a.mode, "mode_label": labels[a.mode],
        "threshold": a.threshold, "groups": rep_groups, "unique_rows": unique_rows,
        "video_rows": video_rows, "bad_rows": bad_rows,
        "stats": {"total": len(images) + len(videos) + others, "images": len(images), "videos": len(videos),
                  "groups": len(multi), "dups": n_dups, "unique": len(unique_rows), "other": others,
                  "unreadable": len(bad)},
    }
    build_report(out, ctx)
    print(f"\nBitti ({time.time()-t0:.0f} sn): {len(multi)} benzer grup, {n_dups} duplicate, "
          f"{len(unique_rows)} unique resim, {len(videos)} video.")
    print(f"Rapor: {out / 'report.html'}")


if __name__ == "__main__":
    main()
