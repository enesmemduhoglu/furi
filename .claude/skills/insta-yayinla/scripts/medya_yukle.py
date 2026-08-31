"""Reel videosunu Vercel Blob'a yukler ve `reels/<slug>/video.json`'i yazar.

Kullanim:
    python medya_yukle.py <video.mp4> --slug reels/ingilizce-3-ipucu
    python medya_yukle.py <video.mp4> --slug reels/x --kuru   # yalnizca dogrula

─── Video neden repoda DURMUYOR ───────────────────────────────────────────────
`furi1/.git` bugun 96 gorselle 103MB. Her Reel 10-70MB; duzenli commit edilirse
depo ayda ~1GB buyur, klonlama yavaslar ve git gecmisinden geri almak mumkun
olmaz. Dosya Blob'a gidiyor, repoda yalnizca URL ve olcumler kaliyor.

─── Yukleme neden SaaS route'undan GECMIYOR ───────────────────────────────────
Vercel'de serverless istek govdesi 4.5MB ile sinirli. SaaS bize presigned bir
PUT URL'i veriyor (`POST /api/media/upload-url`), dosya dogrudan Blob'a
gidiyor. Tur ve boyut sinirlari imzanin icine gomulu, yani sunucuda zorlaniyor.

Cikis kodlari: 0 basarili · 1 hata
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from furi_ortak import (
    MAX_VIDEO_BAYT,
    MAX_VIDEO_SURE,
    gerekli_ortam,
    iso,
    json_bas,
    repo_kok,
    simdi,
    utf8_cikti,
)

UZANTI_TURU = {".mp4": "video/mp4", ".mov": "video/quicktime"}


def _olc(video: Path) -> dict:
    """ffprobe ile sure/en/boy okur. ffprobe yoksa RuntimeError."""
    if not shutil.which("ffprobe"):
        raise RuntimeError(
            "ffprobe bulunamadi — PATH'te yok. Kurulum: winget install --id Gyan.FFmpeg -e"
        )
    komut = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-show_entries", "format=duration",
        "-of", "json", str(video),
    ]
    sonuc = subprocess.run(komut, capture_output=True, text=True)
    if sonuc.returncode != 0:
        raise RuntimeError(f"ffprobe hatasi: {sonuc.stderr.strip()[:300]}")
    ham = json.loads(sonuc.stdout)
    akis = (ham.get("streams") or [{}])[0]
    return {
        "sure": round(float(ham.get("format", {}).get("duration") or 0.0), 2),
        "genislik": int(akis.get("width") or 0),
        "yukseklik": int(akis.get("height") or 0),
        "bayt": video.stat().st_size,
    }


def _yerel_denetim(olcum: dict, tur: str) -> list[str]:
    """Ucretli/uzak cagridan ONCE maliyetsiz eleme.

    Yukleme basarili olup Instagram'in container asamasinda reddetmesi, hem
    100MB'lik bir transferi hem de teshisi zor bir hatayi bosa harcardi.
    """
    sorunlar: list[str] = []
    if olcum["bayt"] <= 0:
        sorunlar.append("dosya bos")
    if olcum["bayt"] > MAX_VIDEO_BAYT:
        sorunlar.append(f"dosya {olcum['bayt']} bayt — limit {MAX_VIDEO_BAYT}")
    if olcum["sure"] <= 0:
        sorunlar.append("sure okunamadi (video akisi yok?)")
    elif olcum["sure"] > MAX_VIDEO_SURE:
        sorunlar.append(f"video {olcum['sure']:.1f} sn — limit {MAX_VIDEO_SURE:.0f} sn")
    if not olcum["genislik"] or not olcum["yukseklik"]:
        sorunlar.append("cozunurluk okunamadi")
    elif olcum["genislik"] > olcum["yukseklik"]:
        # Uyari degil hata: yatay bir video Reels'te kullanilamaz.
        sorunlar.append(
            f"video yatay ({olcum['genislik']}x{olcum['yukseklik']}) — Reels dikey ister"
        )
    if tur not in UZANTI_TURU.values():
        sorunlar.append(f"desteklenmeyen tur: {tur}")
    return sorunlar


def _yukleme_adresi(ortam: dict, tur: str, bayt: int) -> tuple[int, dict]:
    url = ortam["FURI_SAAS_URL"].rstrip("/") + "/api/media/upload-url"
    govde = json.dumps({"contentType": tur, "size": bayt}).encode("utf-8")
    istek = urllib.request.Request(url, data=govde, method="POST")
    istek.add_header("Authorization", "Bearer " + ortam["FURI_API_KEY"])
    istek.add_header("Content-Type", "application/json")
    istek.add_header("User-Agent", "furi-insta-yayinla/2.0")
    try:
        with urllib.request.urlopen(istek, timeout=60) as yanit:
            return yanit.status, json.loads(yanit.read().decode("utf-8"))
    except urllib.error.HTTPError as hata:
        ham = hata.read().decode("utf-8", errors="replace")
        try:
            return hata.code, json.loads(ham)
        except json.JSONDecodeError:
            return hata.code, {"ham_yanit": ham[:400]}
    except (urllib.error.URLError, TimeoutError, OSError) as hata:
        return 0, {"error": f"SaaS'a ulasilamadi: {hata}"}


def _blob_yukle(adres: str, video: Path, tur: str) -> tuple[int, dict]:
    """Presigned URL'e duz PUT. Ek basliga gerek yok — imza URL'in icinde."""
    veri = video.read_bytes()
    istek = urllib.request.Request(adres, data=veri, method="PUT")
    istek.add_header("Content-Type", tur)
    try:
        # Buyuk dosya + yavas baglanti: zaman asimi comert tutuluyor.
        with urllib.request.urlopen(istek, timeout=600) as yanit:
            return yanit.status, json.loads(yanit.read().decode("utf-8"))
    except urllib.error.HTTPError as hata:
        ham = hata.read().decode("utf-8", errors="replace")
        return hata.code, {"ham_yanit": ham[:400]}
    except (urllib.error.URLError, TimeoutError, OSError) as hata:
        return 0, {"error": f"Blob'a yuklenemedi: {hata}"}


def main() -> int:
    utf8_cikti()
    a = argparse.ArgumentParser(description="Reel videosunu Blob'a yukler.")
    a.add_argument("video", help="Yerel mp4/mov dosyasi")
    a.add_argument("--slug", required=True, help="Post slug'i, orn. reels/otel-ingilizcesi")
    a.add_argument("--repo")
    a.add_argument("--kuru", action="store_true", help="Yukleme, yalnizca yerel denetim")
    args = a.parse_args()

    kok = repo_kok(args.repo)
    video = Path(args.video).expanduser()
    if not video.is_file():
        json_bas({"durum": "hata", "sorunlar": [f"dosya yok: {video}"]})
        return 1

    tur = UZANTI_TURU.get(video.suffix.lower())
    if not tur:
        json_bas({
            "durum": "hata",
            "sorunlar": [f"desteklenmeyen uzanti: {video.suffix} (mp4 ya da mov)"],
        })
        return 1

    try:
        olcum = _olc(video)
    except (RuntimeError, ValueError, json.JSONDecodeError) as hata:
        json_bas({"durum": "hata", "sorunlar": [str(hata)]})
        return 1

    sorunlar = _yerel_denetim(olcum, tur)
    if sorunlar:
        json_bas({"durum": "hata", "olcum": olcum, "sorunlar": sorunlar})
        return 1

    hedef_slug = args.slug.replace("\\", "/").strip("/")
    hedef_klasor = kok / hedef_slug

    if args.kuru:
        json_bas({
            "durum": "kuru",
            "slug": hedef_slug,
            "kaynak": video.name,
            "tur": tur,
            "olcum": olcum,
            "hedef": str(hedef_klasor / "video.json"),
            "not": "Yerel denetim gecti. Yukleme yapilmadi.",
        })
        return 0

    ortam = gerekli_ortam(kok, "FURI_SAAS_URL", "FURI_API_KEY")

    kod, yanit = _yukleme_adresi(ortam, tur, olcum["bayt"])
    if kod != 200 or not yanit.get("uploadUrl"):
        json_bas({"durum": "hata", "asama": "adres_alma", "http": kod, "yanit": yanit})
        return 1

    kod, yukleme = _blob_yukle(yanit["uploadUrl"], video, tur)
    if kod != 200 or not yukleme.get("url"):
        json_bas({"durum": "hata", "asama": "yukleme", "http": kod, "yanit": yukleme})
        return 1

    # Klasor yoksa olusturulur; caption.md'yi bu script YAZMAZ — o
    # `insta-ingilizce` skill'inin isi (WORKFLOW.md Faz 6).
    hedef_klasor.mkdir(parents=True, exist_ok=True)
    kayit = {
        "video_url": yukleme["url"],
        "sure": olcum["sure"],
        "genislik": olcum["genislik"],
        "yukseklik": olcum["yukseklik"],
        "bayt": olcum["bayt"],
        "kaynak": video.name,
        "yuklendi": iso(simdi()),
    }
    (hedef_klasor / "video.json").write_text(
        json.dumps(kayit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    caption_var = (hedef_klasor / "caption.md").exists()
    json_bas({
        "durum": "yuklendi",
        "slug": hedef_slug,
        "video_url": yukleme["url"],
        "olcum": olcum,
        "caption_var": caption_var,
        "not": (
            "video.json yazildi."
            if caption_var
            else "video.json yazildi ama caption.md YOK — post gonderilemez."
        ),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
