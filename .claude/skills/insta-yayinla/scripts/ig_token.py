"""Long-lived Instagram token'inin omrunu takip eder ve yeniler.

Token 60 gunde oluyor. Yenilenmezse otomasyon bir gun sessizce durur — bu yuzden
her calismada kontrol edilir, 50. gunden sonra otomatik yenilenir, son 10 gunde
uyari verilir.

Son kullanma tarihi `otomasyon/durum.json` icindeki `token` blogunda tutulur.
Orada **token'in kendisi degil, sadece tarih** durur (repo public).

Kullanim:
    python ig_token.py --kaydet          # kurulumdan hemen sonra: 60 gunluk sayaci baslat
    python ig_token.py --kontrol         # kac gun kaldi? (yazma yapmaz)
    python ig_token.py --yenile          # gerekiyorsa yenile (.env'i gunceller)
    python ig_token.py --yenile --zorla  # gun sayisina bakmadan yenile

Cikis kodlari: 0 sorun yok · 1 hata · 3 dikkat gerekiyor (token yakinda oluyor)
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import timedelta
from pathlib import Path

from furi_ortak import (
    durum_oku,
    durum_yaz,
    gerekli_ortam,
    iso,
    iso_oku,
    json_bas,
    repo_kok,
    simdi,
    utf8_cikti,
)

OMUR_GUN = 60
YENILEME_ESIGI_GUN = 50   # bu gunden sonra otomatik yenile
UYARI_ESIGI_GUN = 10      # kalan gun bunun altindaysa uyar


def _yenileme_adresi(token: str) -> str:
    host = os.environ.get("IG_API_HOST") or "graph.instagram.com"
    sorgu = urllib.parse.urlencode(
        {"grant_type": "ig_refresh_token", "access_token": token}
    )
    return f"https://{host}/refresh_access_token?{sorgu}"


def _token_blogu(durum: dict) -> dict:
    blok = durum.get("token")
    if not isinstance(blok, dict):
        blok = {"son_yenileme": None, "gecerlilik_bitis": None}
        durum["token"] = blok
    blok.setdefault("son_yenileme", None)
    blok.setdefault("gecerlilik_bitis", None)
    return blok


def _kalan_gun(durum: dict) -> float | None:
    bitis = iso_oku(_token_blogu(durum).get("gecerlilik_bitis"))
    if not bitis:
        return None
    return (bitis - simdi()).total_seconds() / 86400.0


def _env_guncelle(kok: Path, yeni_token: str) -> bool:
    """`.env` icindeki IG_ACCESS_TOKEN satirini degistir. Basarili mi doner."""
    yol = kok / ".env"
    if not yol.exists():
        return False
    try:
        icerik = yol.read_text(encoding="utf-8-sig")
        if re.search(r"^\s*IG_ACCESS_TOKEN\s*=", icerik, flags=re.MULTILINE):
            yeni = re.sub(
                r"^\s*IG_ACCESS_TOKEN\s*=.*$",
                f"IG_ACCESS_TOKEN={yeni_token}",
                icerik,
                count=1,
                flags=re.MULTILINE,
            )
        else:
            yeni = icerik.rstrip("\n") + f"\nIG_ACCESS_TOKEN={yeni_token}\n"
        yol.write_text(yeni, encoding="utf-8", newline="\n")
        return True
    except OSError:
        return False


def komut_kaydet(kok: Path, args) -> int:
    gerekli_ortam(kok, "IG_ACCESS_TOKEN")
    durum = durum_oku(kok)
    blok = _token_blogu(durum)
    an = simdi()
    blok["son_yenileme"] = iso(an)
    blok["gecerlilik_bitis"] = iso(an + timedelta(days=OMUR_GUN))
    durum_yaz(kok, durum)
    json_bas(
        {
            "durum": "kaydedildi",
            "gecerlilik_bitis": blok["gecerlilik_bitis"],
            "kalan_gun": OMUR_GUN,
        }
    )
    return 0


def komut_kontrol(kok: Path, args) -> int:
    durum = durum_oku(kok)
    kalan = _kalan_gun(durum)
    if kalan is None:
        json_bas(
            {
                "durum": "bilinmiyor",
                "not": "Token son kullanma tarihi kayitli degil. "
                "Bir kez `python ig_token.py --kaydet` calistir.",
            }
        )
        return 3

    yanit = {
        "durum": "ok",
        "kalan_gun": round(kalan, 1),
        "gecerlilik_bitis": _token_blogu(durum)["gecerlilik_bitis"],
        "yenileme_gerekli": kalan <= (OMUR_GUN - YENILEME_ESIGI_GUN),
        "uyari": kalan <= UYARI_ESIGI_GUN,
    }
    if kalan <= 0:
        yanit["durum"] = "suresi_doldu"
    elif yanit["uyari"]:
        yanit["durum"] = "yakinda_doluyor"
    json_bas(yanit)
    return 3 if yanit["durum"] != "ok" else 0


def komut_yenile(kok: Path, args) -> int:
    ortam = gerekli_ortam(kok, "IG_ACCESS_TOKEN")
    token = ortam["IG_ACCESS_TOKEN"]
    durum = durum_oku(kok)
    kalan = _kalan_gun(durum)

    if not args.zorla and kalan is not None and kalan > (OMUR_GUN - YENILEME_ESIGI_GUN):
        json_bas(
            {
                "durum": "gerek_yok",
                "kalan_gun": round(kalan, 1),
                "not": f"Yenileme {OMUR_GUN - YENILEME_ESIGI_GUN} gun kala baslar.",
            }
        )
        return 0

    istek = urllib.request.Request(_yenileme_adresi(token), method="GET")
    istek.add_header("User-Agent", "furi-insta-yayinla/1.0")
    try:
        with urllib.request.urlopen(istek, timeout=60) as yanit:
            import json as _json

            veri = _json.loads(yanit.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as hata:
        govde = hata.read().decode("utf-8", errors="replace")
        json_bas(
            {
                "durum": "hata",
                "http": hata.code,
                "mesaj": "Token yenilenemedi.",
                "yanit": govde[:600],
                "not": "Token 24 saatten yeni veya suresi tamamen dolmus olabilir. "
                "Suresi dolduysa KURULUM.md'deki adimlarla yeni token uret.",
            }
        )
        return 1
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as hata:
        json_bas({"durum": "hata", "mesaj": f"Token yenileme istegi basarisiz: {hata}"})
        return 1

    yeni_token = veri.get("access_token")
    if not yeni_token:
        json_bas({"durum": "hata", "mesaj": "Yanitta access_token yok", "yanit": veri})
        return 1

    saniye = int(veri.get("expires_in") or OMUR_GUN * 86400)
    an = simdi()
    blok = _token_blogu(durum)
    blok["son_yenileme"] = iso(an)
    blok["gecerlilik_bitis"] = iso(an + timedelta(seconds=saniye))
    durum_yaz(kok, durum)

    kalici = _env_guncelle(kok, yeni_token)
    os.environ["IG_ACCESS_TOKEN"] = yeni_token

    # Token hicbir zaman ciktiya basilmaz — cikti loglara ve maillere dusuyor.
    json_bas(
        {
            "durum": "yenilendi" if kalici else "yenilendi_ama_kaydedilemedi",
            "kalan_gun": round(saniye / 86400.0, 1),
            "gecerlilik_bitis": blok["gecerlilik_bitis"],
            "env_guncellendi": kalici,
            "not": (
                "Yeni token .env dosyasina yazildi."
                if kalici
                else "Yeni token uretildi ama kalici olarak saklanamadi (.env yok). "
                "Bu ortamda yenileme ise yaramaz — yenilemeyi token'in tutuldugu yerde "
                "(yerel makine) yap ve secret'i guncelle."
            ),
        }
    )
    return 0 if kalici else 3


def main() -> int:
    utf8_cikti()
    a = argparse.ArgumentParser(description="Instagram token omru takibi.")
    a.add_argument("--repo", help="Repo kok dizini")
    a.add_argument("--kaydet", action="store_true", help="60 gunluk sayaci simdiden baslat")
    a.add_argument("--kontrol", action="store_true", help="Kac gun kaldi?")
    a.add_argument("--yenile", action="store_true", help="Gerekiyorsa yenile")
    a.add_argument("--zorla", action="store_true", help="--yenile ile: gun sayisina bakma")
    args = a.parse_args()

    kok = repo_kok(args.repo)
    if not kok.is_dir():
        sys.stderr.write(f"HATA: repo bulunamadi: {kok}\n")
        return 1

    if args.kaydet:
        return komut_kaydet(kok, args)
    if args.yenile:
        return komut_yenile(kok, args)
    if args.kontrol:
        return komut_kontrol(kok, args)

    a.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
