"""Ortak yardimcilar: repo yolu, durum dosyalari, caption ayristirma, raw URL.

Sadece Python standart kutuphanesi kullanilir (PIL / requests kurulu degil).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Instagram sinirlari
MAX_KARUSEL = 10
MAX_CAPTION = 2200
MAX_HASHTAG = 30
MAX_ALT_TEXT = 1000
MAX_DOSYA_BAYT = 8 * 1024 * 1024

# SaaS sinirlari — yayin yolu artik content-approval-saas uzerinden gittigi icin
# gercekte baglayici olan limit budur, Instagram'inki degil.
# Kaynak: content-approval-saas src/lib/validation.ts > CAPTION_MAX_LENGTH.
# Instagram 2200'e izin verse de 2000'i asan caption SaaS'tan 400 doner; bunu
# gozetimsiz calisan cron'da HTTP hatasi olarak degil, burada yakalamak gerekir.
SAAS_MAX_CAPTION = 2000

# Akis kurallari
GUNLUK_KOTA = 2
ONAY_SURESI_SAAT = 6
YAYIN_ARASI_SAAT = 4
STOK_ESIGI = 6

TR_SAAT = timezone(timedelta(hours=3))

# Repo taranirken atlanacak ust duzey klasorler
ATLANAN_KLASORLER = {".git", ".claude", ".github", "otomasyon", "node_modules", "__pycache__"}


def simdi() -> datetime:
    return datetime.now(TR_SAAT)


def iso(dt: datetime | None) -> str | None:
    return dt.isoformat(timespec="seconds") if dt else None


def iso_oku(metin: str | None) -> datetime | None:
    if not metin:
        return None
    try:
        dt = datetime.fromisoformat(metin)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=TR_SAAT)


# --------------------------------------------------------------------------- repo


def repo_kok(override: str | None = None) -> Path:
    if override:
        return Path(override).resolve()
    ortam = os.environ.get("FURI_REPO")
    if ortam:
        return Path(ortam).resolve()
    # <repo>/.claude/skills/insta-yayinla/scripts/furi_ortak.py
    return Path(__file__).resolve().parents[4]


def ortam_yukle(kok: Path) -> None:
    """.env dosyasindaki degiskenleri ortama al (zaten tanimliysa dokunma).

    Yerelde .env okunur; bulut calismasinda .env yoktur ve degiskenler routine
    secret'i olarak zaten ortamda gelir. Ikisi de ayni kodla calisir.
    """
    yol = kok / ".env"
    if not yol.exists():
        return
    try:
        satirlar = yol.read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        return
    for satir in satirlar:
        satir = satir.strip()
        if not satir or satir.startswith("#") or "=" not in satir:
            continue
        anahtar, _, deger = satir.partition("=")
        anahtar = anahtar.strip()
        deger = deger.strip().strip('"').strip("'")
        if anahtar and anahtar not in os.environ:
            os.environ[anahtar] = deger


def gerekli_ortam(kok: Path, *anahtarlar: str) -> dict[str, str]:
    """Zorunlu ortam degiskenlerini dondur; eksikse anlasilir hatayla dur."""
    ortam_yukle(kok)
    eksik = [a for a in anahtarlar if not os.environ.get(a)]
    if eksik:
        raise SystemExit(
            "HATA: su ortam degiskenleri eksik: "
            + ", ".join(eksik)
            + "\n  Yerelde: repo kokundeki .env dosyasina ekle."
            + "\n  Bulutta: routine secret'i olarak tanimla."
            + "\n  Kurulum: .claude/skills/insta-yayinla/KURULUM.md"
        )
    return {a: os.environ[a] for a in anahtarlar}


def _git(kok: Path, *args: str) -> str:
    try:
        cikti = subprocess.run(
            ["git", *args],
            cwd=str(kok),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return cikti.stdout.strip() if cikti.returncode == 0 else ""


def raw_taban(kok: Path) -> str:
    """Gorsellerin public URL tabani. Instagram API public URL istiyor."""
    ortam = os.environ.get("IG_RAW_BASE")
    if ortam:
        return ortam.rstrip("/")

    uzak = _git(kok, "remote", "get-url", "origin")
    dal = _git(kok, "rev-parse", "--abbrev-ref", "HEAD") or "main"
    if dal == "HEAD":
        dal = "main"

    eslesme = re.search(r"github\.com[:/]+([^/]+)/([^/]+?)(?:\.git)?$", uzak)
    if eslesme:
        sahip, depo = eslesme.group(1), eslesme.group(2)
        return f"https://raw.githubusercontent.com/{sahip}/{depo}/{dal}"

    return "https://raw.githubusercontent.com/enesmemduhoglu/furi/main"


def ilk_commit_zamani(kok: Path, goreli_yol: str) -> int:
    """Klasorun repoya ilk eklendigi unix zaman. Bilinmiyorsa 0."""
    cikti = _git(kok, "log", "--diff-filter=A", "--format=%ct", "--", goreli_yol)
    if not cikti:
        return 0
    satirlar = [s for s in cikti.splitlines() if s.strip().isdigit()]
    return int(satirlar[-1]) if satirlar else 0


# --------------------------------------------------------------------- durum I/O


def durum_yolu(kok: Path) -> Path:
    return kok / "otomasyon" / "durum.json"


def defter_yolu(kok: Path) -> Path:
    return kok / "otomasyon" / "yayinlananlar.json"


def _json_oku(yol: Path, varsayilan: dict) -> dict:
    if not yol.exists():
        return json.loads(json.dumps(varsayilan))
    try:
        with yol.open(encoding="utf-8-sig") as f:
            veri = json.load(f)
    except (OSError, json.JSONDecodeError) as hata:
        raise SystemExit(f"HATA: {yol} okunamadi/bozuk: {hata}")
    if not isinstance(veri, dict):
        raise SystemExit(f"HATA: {yol} beklenen sozluk yapisinda degil.")
    return veri


def durum_oku(kok: Path) -> dict:
    veri = _json_oku(
        durum_yolu(kok),
        {
            "bekleyen": None,
            "yayin_denemesi": None,
            "son_yayin": None,
            "bugun": {"tarih": None, "yayinlanan": 0},
            "son_stok_uyarisi": None,
            "atlananlar": [],
            "sure_dolanlar": {},
        },
    )
    veri.setdefault("bekleyen", None)
    veri.setdefault("yayin_denemesi", None)
    veri.setdefault("son_yayin", None)
    veri.setdefault("son_stok_uyarisi", None)
    veri.setdefault("atlananlar", [])
    # SKILL.md Faz 2 bu sozluge yaziyor; varsayilani burada olmasa cagiran
    # tarafin once var mi diye bakmasi gerekirdi.
    veri.setdefault("sure_dolanlar", {})
    bugun = veri.setdefault("bugun", {"tarih": None, "yayinlanan": 0})
    bugun.setdefault("tarih", None)
    bugun.setdefault("yayinlanan", 0)
    return veri


def defter_oku(kok: Path) -> dict:
    veri = _json_oku(defter_yolu(kok), {"guncelleme": None, "kayitlar": []})
    veri.setdefault("kayitlar", [])
    return veri


def _json_yaz(yol: Path, veri: dict) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    gecici = yol.with_suffix(yol.suffix + ".tmp")
    with gecici.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
        f.write("\n")
    gecici.replace(yol)


def durum_yaz(kok: Path, veri: dict) -> None:
    _json_yaz(durum_yolu(kok), veri)


def defter_yaz(kok: Path, veri: dict) -> None:
    veri["guncelleme"] = iso(simdi())
    _json_yaz(defter_yolu(kok), veri)


def gunluk_sayaci_tazele(durum: dict) -> dict:
    """Takvim gunu degistiyse gunluk sayaci sifirla."""
    bugun = simdi().date().isoformat()
    if durum["bugun"].get("tarih") != bugun:
        durum["bugun"] = {"tarih": bugun, "yayinlanan": 0}
    return durum


# ------------------------------------------------------------------ post tarama


def _slayt_dosyalari(klasor: Path) -> list[Path]:
    """1.jpg, 2.jpg ... N.jpg — numara sirasinda, bosluk varsa kirilir."""
    bulunan: dict[int, Path] = {}
    for yol in klasor.glob("*.jpg"):
        if yol.stem.isdigit():
            bulunan[int(yol.stem)] = yol
    sirali: list[Path] = []
    n = 1
    while n in bulunan:
        sirali.append(bulunan[n])
        n += 1
    return sirali


def postlari_tara(kok: Path) -> list[dict]:
    """Repodaki tum <kategori>/<slug>/ post klasorleri."""
    postlar: list[dict] = []
    for kategori_yolu in sorted(p for p in kok.iterdir() if p.is_dir()):
        kategori = kategori_yolu.name
        if kategori in ATLANAN_KLASORLER or kategori.startswith((".", "_")):
            continue
        for slug_yolu in sorted(p for p in kategori_yolu.iterdir() if p.is_dir()):
            if slug_yolu.name.startswith((".", "_")):
                continue
            slaytlar = _slayt_dosyalari(slug_yolu)
            caption = slug_yolu / "caption.md"
            if not slaytlar or not caption.exists():
                continue
            postlar.append(
                {
                    "slug": f"{kategori}/{slug_yolu.name}",
                    "kategori": kategori,
                    "ad": slug_yolu.name,
                    "yol": slug_yolu,
                    "slaytlar": slaytlar,
                }
            )
    return postlar


# ------------------------------------------------------------- caption.md ayristirma


def _basliksiz(metin: str) -> str:
    """Baslik karsilastirmasi icin: kucuk harf + diakritik yok + sadece harf/rakam."""
    ayrisik = unicodedata.normalize("NFKD", metin.casefold())
    sade = "".join(k for k in ayrisik if not unicodedata.combining(k))
    # Turkce'ye ozgu, NFKD'nin ayirmadigi harfler
    sade = sade.replace("ı", "i").replace("ş", "s").replace("ğ", "g")
    return re.sub(r"[^a-z0-9]", "", sade)


_BOLUM_ADLARI = {
    "aciklama": "aciklama",
    "hashtag": "hashtag",
    "hashtagler": "hashtag",
    "alttext": "alt_text",
    "alternatifmetin": "alt_text",
}


def caption_ayristir(yol: Path) -> dict:
    """caption.md -> {aciklama, hashtag, alt_text: {slayt_no: metin}}"""
    ham = yol.read_text(encoding="utf-8-sig")
    bolumler: dict[str, list[str]] = {}
    aktif: str | None = None
    for satir in ham.splitlines():
        baslik = re.match(r"^#{1,3}\s+(.+?)\s*$", satir)
        if baslik:
            aktif = _BOLUM_ADLARI.get(_basliksiz(baslik.group(1)))
            if aktif:
                bolumler.setdefault(aktif, [])
            continue
        if aktif:
            bolumler[aktif].append(satir)

    aciklama = "\n".join(bolumler.get("aciklama", [])).strip()

    hashtag_ham = " ".join(bolumler.get("hashtag", [])).strip()
    hashtagler = re.findall(r"#[^\s#]+", hashtag_ham)

    alt_text: dict[int, str] = {}
    aktif_no: int | None = None
    for satir in bolumler.get("alt_text", []):
        madde = re.match(r"^\s*(\d+)[.)]\s*(.*)$", satir)
        if madde:
            aktif_no = int(madde.group(1))
            alt_text[aktif_no] = madde.group(2).strip()
        elif aktif_no is not None and satir.strip():
            alt_text[aktif_no] = (alt_text[aktif_no] + " " + satir.strip()).strip()

    return {
        "aciklama": aciklama,
        "hashtagler": hashtagler,
        "hashtag_satiri": " ".join(hashtagler),
        "alt_text": alt_text,
    }


def caption_birlestir(ayristirilmis: dict) -> str:
    parcalar = [ayristirilmis["aciklama"].strip()]
    if ayristirilmis["hashtag_satiri"]:
        parcalar.append(ayristirilmis["hashtag_satiri"])
    return "\n\n".join(p for p in parcalar if p)


# ------------------------------------------------------------------ URL kontrolu


def raw_url(taban: str, slug: str, dosya_adi: str) -> str:
    yol = "/".join(urllib.parse.quote(p) for p in f"{slug}/{dosya_adi}".split("/"))
    return f"{taban}/{yol}"


def url_erisilebilir(url: str, zaman_asimi: int = 20) -> tuple[bool, str]:
    """HEAD ile 200 + image/jpeg dogrulamasi. (tamam_mi, mesaj)"""
    istek = urllib.request.Request(url, method="HEAD")
    istek.add_header("User-Agent", "furi-insta-yayinla/1.0")
    for deneme in (1, 2):
        try:
            with urllib.request.urlopen(istek, timeout=zaman_asimi) as yanit:
                tur = (yanit.headers.get("Content-Type") or "").split(";")[0].strip()
                boyut = int(yanit.headers.get("Content-Length") or 0)
                if yanit.status != 200:
                    return False, f"HTTP {yanit.status}"
                if tur not in ("image/jpeg", "image/jpg"):
                    return False, f"beklenmeyen tur: {tur or 'yok'}"
                if boyut > MAX_DOSYA_BAYT:
                    return False, f"dosya cok buyuk: {boyut} bayt (limit {MAX_DOSYA_BAYT})"
                return True, "ok"
        except urllib.error.HTTPError as hata:
            return False, f"HTTP {hata.code}"
        except (urllib.error.URLError, TimeoutError, OSError) as hata:
            if deneme == 2:
                return False, f"erisilemedi: {hata}"
    return False, "erisilemedi"


# ----------------------------------------------------------------------- cikti


def utf8_cikti() -> None:
    """Windows konsolunda Turkce karakterler bozulmasin."""
    for akis in (sys.stdout, sys.stderr):
        try:
            akis.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def json_bas(veri: dict) -> None:
    sys.stdout.write(json.dumps(veri, ensure_ascii=False, indent=2) + "\n")
