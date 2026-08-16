"""Instagram'i tek dogruluk kaynagi kabul edip yayin defterini esitler.

Yayini artik SaaS yapiyor, yani bu repo yayin anini gormuyor. Defterin dogru
kalmasinin yolu Instagram'a bakmak: hesaptaki her postun caption'i repodaki
caption'larla eslestirilir.

Iki yonlu calisir:
  - Instagram'da VAR, defterde YOK  -> deftere eklenir (SaaS yayinlamis)
  - Defterde VAR, Instagram'da YOK  -> defterden dusurulur (post silinmis,
                                        icerik tekrar aday olur)

Ikincisi olmadan silinen bir post sonsuza kadar "yayinlanmis" sayilir ve bir
daha asla onerilmez.

Kullanim:
    python esitle.py            # farklari uygula
    python esitle.py --kuru     # sadece raporla, dosyaya dokunma

Cikis kodlari: 0 (fark olsun olmasin basarili) · 1 hata
"""

from __future__ import annotations

import argparse
import re
import sys

import ig_api
from furi_ortak import (
    caption_ayristir,
    caption_birlestir,
    defter_oku,
    defter_yaz,
    durum_oku,
    durum_yaz,
    gerekli_ortam,
    gunluk_sayaci_tazele,
    iso,
    iso_oku,
    json_bas,
    postlari_tara,
    repo_kok,
    simdi,
    utf8_cikti,
)


def _iz(metin: str) -> str:
    """Caption'in Instagram kopyasiyla eslestirilebilir sade hali."""
    return re.sub(r"\s+", " ", metin or "").strip()[:80].casefold()


def _kod(permalink: str) -> str:
    return (permalink or "").rstrip("/").split("/")[-1]


def main() -> int:
    utf8_cikti()
    a = argparse.ArgumentParser(description="Yayin defterini Instagram ile esitler.")
    a.add_argument("--repo")
    a.add_argument("--kuru", action="store_true", help="Raporla, dosyaya yazma")
    args = a.parse_args()

    kok = repo_kok(args.repo)
    ortam = gerekli_ortam(kok, "IG_ACCESS_TOKEN", "IG_USER_ID")

    try:
        medyalar = ig_api.get(
            f"{ortam['IG_USER_ID']}/media",
            {"fields": "id,permalink,timestamp,media_type,caption", "limit": "50"},
            ortam["IG_ACCESS_TOKEN"],
        )["data"]
    except ig_api.IGHatasi as hata:
        json_bas({"durum": "hata", "mesaj": hata.rapor(), "ayrinti": hata.ayrinti})
        return 1

    # repo caption izi -> post
    repo = {}
    for p in postlari_tara(kok):
        ayr = caption_ayristir(p["yol"] / "caption.md")
        repo[_iz(caption_birlestir(ayr))] = p

    defter = defter_oku(kok)
    defterdeki = {k["slug"]: k for k in defter["kayitlar"]}
    canli_kodlar = {_kod(m["permalink"]) for m in medyalar}

    eklenen, dusen = [], []

    # 1) Instagram'da var, defterde yok -> ekle
    for m in medyalar:
        post = repo.get(_iz(m.get("caption") or ""))
        if not post or post["slug"] in defterdeki:
            continue
        zaman = iso_oku((m.get("timestamp") or "").replace("+0000", "+00:00"))
        kayit = {
            "slug": post["slug"],
            "kategori": post["kategori"],
            "slayt": len(post["slaytlar"]),
            "ig_media_id": m["id"],
            "permalink": m["permalink"],
            "yayin_zamani": iso(zaman) if zaman else None,
            "not": "esitleme ile eklendi (SaaS yayinladi)",
        }
        eklenen.append(kayit)

    # 2) Defterde var, Instagram'da yok -> dusur
    kalan = []
    for kayit in defter["kayitlar"]:
        if _kod(kayit.get("permalink", "")) in canli_kodlar:
            kalan.append(kayit)
        else:
            dusen.append(kayit)

    fark = bool(eklenen or dusen)
    rapor = {
        "durum": "fark_var" if fark else "esit",
        "instagram_post": len(medyalar),
        "defter_once": len(defter["kayitlar"]),
        "eklenen": [{"slug": k["slug"], "permalink": k["permalink"]} for k in eklenen],
        "dusen": [{"slug": k["slug"], "permalink": k.get("permalink"),
                   "sebep": "Instagram'da bulunamadi (silinmis)"} for k in dusen],
    }

    if fark and not args.kuru:
        defter["kayitlar"] = kalan + eklenen
        defter["kayitlar"].sort(key=lambda k: k.get("yayin_zamani") or "")
        defter_yaz(kok, defter)

        durum = gunluk_sayaci_tazele(durum_oku(kok))
        degisti = False
        # Bekleyen post yayinlandiysa bekleyeni kapat, gunluk sayaci artir
        bekleyen = durum.get("bekleyen") or {}
        if bekleyen.get("slug") and any(k["slug"] == bekleyen["slug"] for k in eklenen):
            durum["bekleyen"] = None
            durum["son_yayin"] = iso(simdi())
            durum["bugun"]["yayinlanan"] = int(durum["bugun"].get("yayinlanan", 0)) + 1
            rapor["bekleyen_kapandi"] = bekleyen["slug"]
            degisti = True
        # Yayinlanan postun sure sayaci varsa sifirlanir
        sd = durum.get("sure_dolanlar")
        if isinstance(sd, dict):
            for k in eklenen:
                if sd.pop(k["slug"], None) is not None:
                    degisti = True
        if degisti:
            durum_yaz(kok, durum)

    rapor["defter_sonra"] = len(kalan) + len(eklenen) if not args.kuru else len(defter["kayitlar"])
    if args.kuru and fark:
        rapor["not"] = "--kuru: hicbir dosya degistirilmedi."
    json_bas(rapor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
