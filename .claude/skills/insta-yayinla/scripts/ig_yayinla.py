"""Bir postu Instagram'a yayinlar ve durum dosyalarini gunceller.

NORMAL AKISTA CAGRILMAZ. Yayin content-approval-saas'a tasindi: onay geldigi an
ayni HTTP isteginde Instagram'a basiliyor. Bu script elle teshis ve kurtarma
icin duruyor:

    --kontrol   Instagram token'i / hesabi saglam mi
    --dogrula   Yarida kalmis bir yayin gercekten atilmis mi (emniyet agi)
    --slug      SaaS calismiyorken elle yayin — SON CARE
    --paket     EMEKLI, bkz. ../emekli/README.md

`--slug` ile elle yayin yaparsan SaaS bunu bilmez: o postun SaaS'taki kaydi
`pending`/`idle` kalir. Cift yayin riskini kendin gozetmelisin — once SaaS
tarafindaki postu reddet ya da sil.

Cift yayin korumasi bu script'in en onemli isi. Sira su:

    1. --isaretle   durum.json'a "yayin denemesi" isareti yazilir
       (skill bunu COMMIT + PUSH eder — bulutta calisma yarida kesilirse
        bir sonraki calisma bu isareti gorup korlemesine tekrar denemez)
    2. --slug       gercek yayin yapilir, basarili olunca isaret silinir
                    ve post yayin defterine yazilir
    3. --dogrula    isaret kalmissa: Instagram'a sorup post gercekten
                    atilmis mi diye bakar

Kullanim:
    python ig_yayinla.py --kontrol                   # hesap + limit + token sagligi
    python ig_yayinla.py --onizle dizi/my-bad        # API'ye yazmadan hazirlik testi
    python ig_yayinla.py --isaretle dizi/my-bad      # yayin oncesi isaret
    python ig_yayinla.py --slug dizi/my-bad          # YAYINLA (canli)
    python ig_yayinla.py --dogrula dizi/my-bad       # gercekten atildi mi?
    python ig_yayinla.py --tek-slayt dizi/my-bad     # sadece 1.jpg (en-boy testi, kayit tutmaz)

Cikis kodlari: 0 basarili · 1 hata · 2 zaten yayinlanmis (yapilacak is yok)
"""

from __future__ import annotations

import argparse
import re
import sys

import ig_api
from aday_sec import veri_topla
from furi_ortak import (
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
    raw_taban,
    repo_kok,
    simdi,
    utf8_cikti,
)


def _post_bul(kok, slug: str) -> dict:
    hedef = slug.replace("\\", "/").strip("/")
    for post in postlari_tara(kok):
        if post["slug"] == hedef:
            return post
    raise SystemExit(f"HATA: post bulunamadi: {hedef}")


def _parmak_izi(caption: str) -> str:
    """Caption'in Instagram'daki kopyasiyla eslestirilebilir sade hali."""
    return re.sub(r"\s+", " ", caption).strip()[:80].casefold()


def _defterde_var_mi(defter: dict, slug: str) -> dict | None:
    for kayit in defter.get("kayitlar", []):
        if kayit.get("slug") == slug:
            return kayit
    return None


def _instagramda_bul(ig_id: str, token: str, caption: str, esikten_sonra) -> dict | None:
    """Son postlar arasinda ayni caption'la atilmis bir post var mi?"""
    izi = _parmak_izi(caption)
    for medya in ig_api.son_medyalar(ig_id, token, adet=10):
        uzak_izi = _parmak_izi(medya.get("caption") or "")
        if not uzak_izi or uzak_izi != izi:
            continue
        if esikten_sonra:
            zaman = iso_oku((medya.get("timestamp") or "").replace("+0000", "+00:00"))
            if zaman and zaman < esikten_sonra:
                continue
        return medya
    return None


# ----------------------------------------------------------------------- komutlar


def komut_kontrol(kok, args) -> int:
    ortam = gerekli_ortam(kok, "IG_ACCESS_TOKEN", "IG_USER_ID")
    token, ig_id = ortam["IG_ACCESS_TOKEN"], ortam["IG_USER_ID"]
    try:
        hesap = ig_api.hesap_bilgisi(ig_id, token)
        limit = ig_api.yayin_limiti(ig_id, token)
    except ig_api.IGHatasi as hata:
        json_bas({"durum": "hata", "mesaj": hata.rapor(), "ayrinti": hata.ayrinti})
        return 1
    json_bas(
        {
            "durum": "ok",
            "hesap": hesap,
            "yayin_limiti": limit,
            "api": f"{ig_api._taban()}",
            "raw_taban": raw_taban(kok),
        }
    )
    return 0


def komut_kimlik(kok, args) -> int:
    """Kurulum yardimcisi: sadece token ile IG_USER_ID'yi bulur."""
    ortam = gerekli_ortam(kok, "IG_ACCESS_TOKEN")
    try:
        bilgi = ig_api.kimlik(ortam["IG_ACCESS_TOKEN"])
    except ig_api.IGHatasi as hata:
        json_bas({"durum": "hata", "mesaj": hata.rapor(), "ayrinti": hata.ayrinti})
        return 1
    json_bas(
        {
            "durum": "ok",
            "hesap": bilgi,
            "not": f"IG_USER_ID={bilgi.get('user_id') or bilgi.get('id')} degerini .env'e ekle.",
        }
    )
    return 0


def komut_onizle(kok, args) -> int:
    post = _post_bul(kok, args.onizle)
    veri, sorunlar = veri_topla(kok, post, raw_taban(kok))
    defter = defter_oku(kok)
    mevcut = _defterde_var_mi(defter, veri["slug"])
    veri["durum"] = "hata" if sorunlar else "hazir"
    if sorunlar:
        veri["sorunlar"] = sorunlar
    if mevcut:
        veri["durum"] = "zaten_yayinlandi"
        veri["mevcut_kayit"] = mevcut
    json_bas(veri)
    return 0 if veri["durum"] == "hazir" else 1


def komut_isaretle(kok, args) -> int:
    post = _post_bul(kok, args.isaretle)
    veri, sorunlar = veri_topla(kok, post, raw_taban(kok))
    if sorunlar:
        json_bas({"durum": "hata", "slug": veri["slug"], "sorunlar": sorunlar})
        return 1

    defter = defter_oku(kok)
    if _defterde_var_mi(defter, veri["slug"]):
        json_bas({"durum": "zaten_yayinlandi", "slug": veri["slug"]})
        return 2

    durum = gunluk_sayaci_tazele(durum_oku(kok))
    durum["yayin_denemesi"] = {
        "slug": veri["slug"],
        "kategori": veri["kategori"],
        "slayt": veri["slayt"],
        "caption_izi": _parmak_izi(veri["caption"]),
        "baslangic": iso(simdi()),
    }
    durum_yaz(kok, durum)
    json_bas(
        {
            "durum": "isaretlendi",
            "slug": veri["slug"],
            "not": "Bu degisikligi yayindan ONCE commit + push et.",
        }
    )
    return 0


def komut_dogrula(kok, args) -> int:
    """Yarida kalmis bir yayin denemesi gercekten Instagram'a dusmus mu?"""
    slug = args.dogrula.replace("\\", "/").strip("/")
    ortam = gerekli_ortam(kok, "IG_ACCESS_TOKEN", "IG_USER_ID")
    token, ig_id = ortam["IG_ACCESS_TOKEN"], ortam["IG_USER_ID"]

    defter = defter_oku(kok)
    mevcut = _defterde_var_mi(defter, slug)
    if mevcut:
        json_bas({"durum": "defterde_var", "slug": slug, "kayit": mevcut})
        return 2

    post = _post_bul(kok, slug)
    veri, _ = veri_topla(kok, post, raw_taban(kok), url_kontrol=False)
    durum = durum_oku(kok)
    deneme = durum.get("yayin_denemesi") or {}
    esik = iso_oku(deneme.get("baslangic")) if deneme.get("slug") == slug else None

    try:
        medya = _instagramda_bul(ig_id, token, veri["caption"], esik)
    except ig_api.IGHatasi as hata:
        json_bas({"durum": "hata", "mesaj": hata.rapor(), "ayrinti": hata.ayrinti})
        return 1

    if not medya:
        json_bas(
            {
                "durum": "yayinlanmamis",
                "slug": slug,
                "not": "Instagram'da bulunamadi — yayin tekrar denenebilir.",
            }
        )
        return 0

    _basariyi_kaydet(kok, veri, str(medya["id"]), medya.get("permalink", ""), sayac_artir=True)
    json_bas(
        {
            "durum": "aslinda_yayinlanmis",
            "slug": slug,
            "ig_media_id": medya["id"],
            "permalink": medya.get("permalink"),
            "not": "Deftere islendi, isaret temizlendi. Tekrar yayinlama.",
        }
    )
    return 2


def _basariyi_kaydet(kok, veri: dict, media_id: str, permalink: str, sayac_artir: bool) -> None:
    an = simdi()

    defter = defter_oku(kok)
    defter["kayitlar"].append(
        {
            "slug": veri["slug"],
            "kategori": veri["kategori"],
            "slayt": veri["slayt"],
            "ig_media_id": media_id,
            "permalink": permalink,
            "yayin_zamani": iso(an),
        }
    )
    defter_yaz(kok, defter)

    durum = gunluk_sayaci_tazele(durum_oku(kok))
    durum["yayin_denemesi"] = None
    durum["son_yayin"] = iso(an)
    bekleyen = durum.get("bekleyen") or {}
    if bekleyen.get("slug") == veri["slug"]:
        durum["bekleyen"] = None
    if sayac_artir:
        durum["bugun"]["yayinlanan"] = int(durum["bugun"].get("yayinlanan", 0)) + 1
    durum_yaz(kok, durum)


def komut_yayinla(kok, args) -> int:
    slug = args.slug.replace("\\", "/").strip("/")
    ortam = gerekli_ortam(kok, "IG_ACCESS_TOKEN", "IG_USER_ID")
    token, ig_id = ortam["IG_ACCESS_TOKEN"], ortam["IG_USER_ID"]

    defter = defter_oku(kok)
    mevcut = _defterde_var_mi(defter, slug)
    if mevcut:
        json_bas(
            {
                "durum": "zaten_yayinlandi",
                "slug": slug,
                "kayit": mevcut,
                "not": "Yayin defterinde kayitli. Tekrar yayinlanmadi.",
            }
        )
        return 2

    durum = durum_oku(kok)
    deneme = durum.get("yayin_denemesi") or {}
    if not args.zorla and deneme.get("slug") != slug:
        json_bas(
            {
                "durum": "isaret_yok",
                "slug": slug,
                "mevcut_isaret": deneme.get("slug"),
                "not": "Once `--isaretle` calistir ve commit+push et. (Zorlamak icin --zorla)",
            }
        )
        return 1

    post = _post_bul(kok, slug)
    veri, sorunlar = veri_topla(kok, post, raw_taban(kok))
    if sorunlar:
        json_bas({"durum": "hata", "slug": slug, "sorunlar": sorunlar})
        return 1

    gorseller = veri["gorseller"]
    if args.tek_slayt:
        gorseller = gorseller[:1]

    try:
        # Yarida kalmis bir denemenin ayni postu ikinci kez atmasini engelle
        esik = iso_oku(deneme.get("baslangic")) if deneme.get("slug") == slug else None
        if esik:
            onceki = _instagramda_bul(ig_id, token, veri["caption"], esik)
            if onceki:
                _basariyi_kaydet(
                    kok, veri, str(onceki["id"]), onceki.get("permalink", ""), sayac_artir=True
                )
                json_bas(
                    {
                        "durum": "zaten_yayinlandi",
                        "slug": slug,
                        "ig_media_id": onceki["id"],
                        "permalink": onceki.get("permalink"),
                        "not": "Onceki deneme aslinda basarili olmus. Tekrar atilmadi.",
                    }
                )
                return 2

        adimlar: list[str] = []

        if len(gorseller) == 1:
            g = gorseller[0]
            container = ig_api.container_olustur(
                ig_id, token, image_url=g["url"], caption=veri["caption"], alt_text=g["alt_text"]
            )
            adimlar.append(f"tekli container {container}")
        else:
            cocuklar = []
            for g in gorseller:
                cocuk = ig_api.container_olustur(
                    ig_id,
                    token,
                    image_url=g["url"],
                    is_carousel_item="true",
                    alt_text=g["alt_text"],
                )
                cocuklar.append(cocuk)
                adimlar.append(f"slayt {g['no']} -> {cocuk}")
            for cocuk in cocuklar:
                ig_api.container_bekle(cocuk, token)
            container = ig_api.container_olustur(
                ig_id,
                token,
                media_type="CAROUSEL",
                children=",".join(cocuklar),
                caption=veri["caption"],
            )
            adimlar.append(f"karusel container {container}")

        ig_api.container_bekle(container, token)
        media_id = ig_api.yayinla(ig_id, container, token)
        adimlar.append(f"yayinlandi -> {media_id}")

        bilgi = {}
        try:
            bilgi = ig_api.medya_bilgisi(media_id, token)
        except ig_api.IGHatasi:
            pass  # permalink alinamadiysa yayin yine de basarili

    except ig_api.IGHatasi as hata:
        json_bas(
            {
                "durum": "hata",
                "slug": slug,
                "mesaj": hata.rapor(),
                "http": hata.http,
                "ayrinti": hata.ayrinti,
                "not": "Durum dosyalarina dokunulmadi. Isaret duruyor, --dogrula ile kontrol et.",
            }
        )
        return 1

    permalink = bilgi.get("permalink", "")

    if args.tek_slayt:
        json_bas(
            {
                "durum": "test_yayinlandi",
                "slug": slug,
                "ig_media_id": media_id,
                "permalink": permalink,
                "not": "TEST postu — yayin defterine YAZILMADI. Instagram'dan elle sil, "
                "sonra `--temizle-isaret` calistir.",
            }
        )
        return 0

    _basariyi_kaydet(kok, veri, media_id, permalink, sayac_artir=True)
    json_bas(
        {
            "durum": "yayinlandi",
            "slug": slug,
            "kategori": veri["kategori"],
            "slayt": len(gorseller),
            "ig_media_id": media_id,
            "permalink": permalink,
            "adimlar": adimlar,
        }
    )
    return 0


def komut_paket(kok, args) -> int:
    """EMEKLI — Apps Script'in yayin yapabilmesi icin hazir paket yazardi.

    Ciktisini yalnizca Gmail/Apps Script zinciri tuketiyordu; o zincir emekliye
    ayrildi (bkz. ../emekli/README.md). Yayini artik SaaS yapiyor ve gerekli
    veriyi `saas_gonder.py` dogrudan POST ediyor — araya dosya girmiyor.

    Komut calisir halde birakildi (geri donus yolu acik kalsin diye) ama
    cagirani uyarir.
    """
    sys.stderr.write(
        "UYARI: --paket emekli. Ciktisini tuketen Apps Script zinciri artik yok;\n"
        "       yayin verisi SaaS'a saas_gonder.py ile dogrudan gidiyor.\n"
        "       Ayrinti: .claude/skills/insta-yayinla/emekli/README.md\n"
    )
    post = _post_bul(kok, args.paket)
    veri, sorunlar = veri_topla(kok, post, raw_taban(kok))
    if sorunlar:
        json_bas({"durum": "hata", "slug": veri["slug"], "sorunlar": sorunlar})
        return 1

    paket = {
        "slug": veri["slug"],
        "kategori": veri["kategori"],
        "slayt": veri["slayt"],
        "caption": veri["caption"],
        "gorseller": [
            {"no": g["no"], "url": g["url"], "alt_text": g["alt_text"]}
            for g in veri["gorseller"]
        ],
        "hazirlanma": iso(simdi()),
    }
    yol = kok / "otomasyon" / "bekleyen-yayin.json"
    yol.parent.mkdir(parents=True, exist_ok=True)
    with yol.open("w", encoding="utf-8", newline="\n") as f:
        import json as _json

        _json.dump(paket, f, ensure_ascii=False, indent=2)
        f.write("\n")

    json_bas({"durum": "paket_yazildi", "dosya": str(yol), "slug": veri["slug"],
              "slayt": veri["slayt"]})
    return 0


def komut_temizle_isaret(kok, args) -> int:
    durum = durum_oku(kok)
    onceki = durum.get("yayin_denemesi")
    durum["yayin_denemesi"] = None
    durum_yaz(kok, durum)
    json_bas({"durum": "temizlendi", "onceki_isaret": onceki})
    return 0


def main() -> int:
    utf8_cikti()
    a = argparse.ArgumentParser(description="Instagram'a post yayinlar.")
    a.add_argument("--repo", help="Repo kok dizini")
    a.add_argument("--kimlik", action="store_true", help="Sadece token ile IG_USER_ID'yi bul (kurulum)")
    a.add_argument("--kontrol", action="store_true", help="Hesap + yayin limiti + token saglik testi")
    a.add_argument("--onizle", metavar="SLUG", help="API'ye yazmadan hazirlik testi")
    a.add_argument("--isaretle", metavar="SLUG", help="Yayin oncesi isaret yaz")
    a.add_argument("--slug", metavar="SLUG", help="YAYINLA (canli)")
    a.add_argument("--dogrula", metavar="SLUG", help="Yarida kalan deneme gercekten atilmis mi?")
    a.add_argument("--paket", metavar="SLUG",
                   help="[EMEKLI] Apps Script icin hazir yayin paketi yaz")
    a.add_argument("--temizle-isaret", action="store_true", help="Yayin denemesi isaretini sil")
    a.add_argument("--tek-slayt", action="store_true", help="--slug ile: sadece 1.jpg, kayit tutmaz")
    a.add_argument("--zorla", action="store_true", help="--slug ile: isaret sarti aranmasin")
    args = a.parse_args()

    kok = repo_kok(args.repo)
    if not kok.is_dir():
        sys.stderr.write(f"HATA: repo bulunamadi: {kok}\n")
        return 1

    if args.kimlik:
        return komut_kimlik(kok, args)
    if args.kontrol:
        return komut_kontrol(kok, args)
    if args.onizle:
        return komut_onizle(kok, args)
    if args.isaretle:
        return komut_isaretle(kok, args)
    if args.dogrula:
        return komut_dogrula(kok, args)
    if args.temizle_isaret:
        return komut_temizle_isaret(kok, args)
    if args.slug:
        return komut_yayinla(kok, args)

    a.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
