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
import json
import re
import sys
import urllib.error
import urllib.request

import ig_api
from furi_ortak import (
    SaasTokenHatasi,
    caption_ayristir,
    caption_birlestir,
    defter_oku,
    defter_yaz,
    durum_oku,
    durum_yaz,
    ig_kimlik,
    ortam_yukle,
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


def _saas_durum(onay_url: str) -> dict | None:
    """Bekleyen postun SaaS'taki durumu. Token yeterli, oturum gerekmiyor.

    Caption eslestirmesi bir cikarim; bu ise kesin bilgi. Ozellikle "yayinlandi
    ama sonra silindi" durumunu ancak buradan ogrenebiliriz — Instagram'a
    bakmak o postu hic yayinlanmamis gibi gosterir.
    """
    if not onay_url:
        return None
    parca = onay_url.rstrip("/").split("/")
    token = parca[-1] if parca else ""
    if not token:
        return None
    taban = onay_url.split("/approve/")[0]
    try:
        istek = urllib.request.Request(f"{taban}/api/approve/{token}", method="GET")
        istek.add_header("User-Agent", "furi-insta-yayinla/2.0")
        with urllib.request.urlopen(istek, timeout=30) as yanit:
            veri = json.loads(yanit.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            OSError, json.JSONDecodeError):
        return None
    return veri.get("post") or veri


def main() -> int:
    utf8_cikti()
    a = argparse.ArgumentParser(description="Yayin defterini Instagram ile esitler.")
    a.add_argument("--repo")
    a.add_argument("--kuru", action="store_true", help="Raporla, dosyaya yazma")
    args = a.parse_args()

    kok = repo_kok(args.repo)
    ortam_yukle(kok)

    # Instagram karsilastirmasi OPSIYONEL: bir emniyet agi, ana mekanizma degil.
    # Bekleyen postun akibetini SaaS'in public onay endpoint'i kesin olarak
    # soyluyor ve o kimlik bilgisi istemiyor. Bu yuzden token alinamazsa
    # esitleme durmaz, sadece Instagram karsilastirmasi atlanir — ama NEDEN
    # atlandigi rapora yazilir, sessiz kalmaz.
    #
    # Token artik ortamdan degil SaaS'tan geliyor (tek dogruluk kaynagi):
    # burada ayri bir IG_ACCESS_TOKEN kopyasi tutulsaydi SaaS'in gunluk
    # yenileme cron'undan sonra bayatlar ve karsilastirma sessizce yanlis
    # sonuc uretirdi.
    medyalar: list[dict] = []
    ig_atlandi = None
    try:
        kimlik = ig_kimlik(kok)
    except SaasTokenHatasi as hata:
        kimlik = None
        ig_atlandi = (
            f"Instagram karsilastirmasi atlandi — SaaS'tan token alinamadi: {hata.mesaj}"
        )

    if kimlik:
        try:
            medyalar = ig_api.get(
                f"{kimlik['ig_user_id']}/media",
                {"fields": "id,permalink,timestamp,media_type,caption", "limit": "50"},
                kimlik["token"],
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
    #    Instagram sorgulanmadiysa BU ADIM ATLANIR. Yoksa canli_kodlar bos olur
    #    ve defterdeki her kayit "silinmis" sayilip topluca dusurulur.
    if ig_atlandi:
        kalan = list(defter["kayitlar"])
    else:
        kalan = []
        for kayit in defter["kayitlar"]:
            if _kod(kayit.get("permalink", "")) in canli_kodlar:
                kalan.append(kayit)
            else:
                dusen.append(kayit)

    # 3) Bekleyen postun SaaS'taki gercek durumu — caption eslestirmesinden once
    #    gelir cunku kesin bilgidir.
    durum_dosyasi = durum_oku(kok)
    bekleyen = durum_dosyasi.get("bekleyen") or {}
    saas = _saas_durum(bekleyen.get("onay_url", "")) if bekleyen else None
    bekleyen_karari = None

    if saas:
        yayin = saas.get("publishStatus")
        onay = saas.get("status")
        link = saas.get("igPermalink") or ""
        if onay == "rejected":
            bekleyen_karari = {"sonuc": "reddedildi", "slug": bekleyen["slug"]}
        elif yayin == "published":
            # Instagram sorgulanmadiysa "silinmis mi" bilinemez; yayinlanmis kabul
            # edilir. Yanlissa bir sonraki tam esitleme kaydi dusurur.
            canli = True if ig_atlandi else (_kod(link) in canli_kodlar)
            bekleyen_karari = {
                "sonuc": "yayinlandi" if canli else "yayinlandi_sonra_silindi",
                "slug": bekleyen["slug"],
                "permalink": link,
            }
            # Yayinlanmis ama silinmisse deftere YAZILMAZ: icerik havuza donsun.
            # Yine de kota sayilir ve bekleyen kapanir.
            if canli and not any(k["slug"] == bekleyen["slug"] for k in eklenen) \
                    and bekleyen["slug"] not in defterdeki:
                eklenen.append({
                    "slug": bekleyen["slug"],
                    "kategori": bekleyen.get("kategori", bekleyen["slug"].split("/")[0]),
                    "slayt": bekleyen.get("slayt", 0),
                    "ig_media_id": None,
                    "permalink": link,
                    "yayin_zamani": iso(simdi()),
                    "not": "SaaS yayinladi (onay endpoint'inden dogrulandi)",
                })
        elif yayin == "failed":
            bekleyen_karari = {"sonuc": "yayin_hatasi", "slug": bekleyen["slug"]}
        elif yayin == "skipped":
            bekleyen_karari = {"sonuc": "atlandi_instagram_bagli_degil",
                               "slug": bekleyen["slug"]}

    fark = bool(eklenen or dusen)
    rapor = {
        "durum": "fark_var" if fark else "esit",
        "instagram_post": len(medyalar),
        "defter_once": len(defter["kayitlar"]),
        "eklenen": [{"slug": k["slug"], "permalink": k["permalink"]} for k in eklenen],
        "dusen": [{"slug": k["slug"], "permalink": k.get("permalink"),
                   "sebep": "Instagram'da bulunamadi (silinmis)"} for k in dusen],
    }
    if bekleyen_karari:
        rapor["bekleyen"] = bekleyen_karari
    if ig_atlandi:
        rapor["instagram"] = ig_atlandi

    yazilacak = fark or bool(bekleyen_karari)
    if yazilacak and not args.kuru:
        if fark:
            defter["kayitlar"] = kalan + eklenen
            defter["kayitlar"].sort(key=lambda k: k.get("yayin_zamani") or "")
            defter_yaz(kok, defter)

        durum = gunluk_sayaci_tazele(durum_oku(kok))
        degisti = False
        sonuc = (bekleyen_karari or {}).get("sonuc")

        if sonuc in ("yayinlandi", "yayinlandi_sonra_silindi"):
            durum["bekleyen"] = None
            durum["son_yayin"] = iso(simdi())
            durum["bugun"]["yayinlanan"] = int(durum["bugun"].get("yayinlanan", 0)) + 1
            degisti = True
        elif sonuc == "reddedildi":
            durum["atlananlar"].append({
                "slug": bekleyen_karari["slug"],
                "tarih": simdi().date().isoformat(),
                "sebep": "onay sayfasinda reddedildi",
            })
            durum["bekleyen"] = None
            degisti = True
        elif sonuc == "atlandi_instagram_bagli_degil":
            # Musteride Instagram bagli degil: onay verildi ama yayin yapilmadi.
            # Post havuzda kalir; asil sorun SaaS tarafinda cozulmeli.
            durum["bekleyen"] = None
            degisti = True
        # sonuc == "yayin_hatasi" -> bekleyen KORUNUR, onay sayfasindan tekrar
        # denenebilir. Skill bunu hata maili ile bildirir.

        sd = durum.get("sure_dolanlar")
        if isinstance(sd, dict):
            for k in eklenen:
                if sd.pop(k["slug"], None) is not None:
                    degisti = True
            if sonuc in ("yayinlandi", "yayinlandi_sonra_silindi") and \
                    sd.pop(bekleyen_karari["slug"], None) is not None:
                degisti = True
        if degisti:
            durum_yaz(kok, durum)

    rapor["defter_sonra"] = (len(kalan) + len(eklenen)) if (fark and not args.kuru) \
        else len(defter["kayitlar"])
    if args.kuru and fark:
        rapor["not"] = "--kuru: hicbir dosya degistirilmedi."
    json_bas(rapor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
