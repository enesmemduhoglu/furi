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

Instagram'a ulasilamazsa bu iki yonlu karsilastirma ATLANIR, script durmaz:
bekleyen postun akibeti zaten SaaS'in onay endpoint'inden ogreniliyor. Atlandigi
zaman raporda `instagram` alani sebebiyle birlikte cikar — sessiz kalmaz.

Kullanim:
    python esitle.py            # farklari uygula
    python esitle.py --kuru     # sadece raporla, dosyaya dokunma

Cikis kodu her zaman 0: fark bulunsa da bulunmasa da, Instagram karsilastirmasi
yapilsa da atlansa da esitleme kendi isini yapmis sayilir. Bu script'in
basarisizligi cagiran akisi durdurmaz.
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
    TR_SAAT,
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


def _saas_durum(onay_url: str) -> tuple[dict | None, str | None]:
    """Bekleyen postun SaaS'taki durumu. Token yeterli, oturum gerekmiyor.

    Caption eslestirmesi bir cikarim; bu ise kesin bilgi. Ozellikle "yayinlandi
    ama sonra silindi" durumunu ancak buradan ogrenebiliriz — Instagram'a
    bakmak o postu hic yayinlanmamis gibi gosterir.

    `(veri, hata)` doner. Hatanin sebebi ayrica dondurulur cunku "SaaS bir sey
    soylemedi" ile "SaaS'a hic sorulamadi" ayni sey degil: ikincisinde bekleyen
    postun akibeti hakkinda ELIMIZDE BILGI YOK, sessizce "onaylanmadi" varsaymak
    yanlis olur. Ozellikle onay linki 7 gunluk omrunu doldurunca (410) bu cagri
    kalici olarak susar ve defter bir daha asla gercegi ogrenemez.
    """
    if not onay_url:
        return None, "onay_url bos"
    parca = onay_url.rstrip("/").split("/")
    token = parca[-1] if parca else ""
    if not token:
        return None, "onay_url'de token yok"
    taban = onay_url.split("/approve/")[0]
    try:
        istek = urllib.request.Request(f"{taban}/api/approve/{token}", method="GET")
        istek.add_header("User-Agent", "furi-insta-yayinla/2.0")
        with urllib.request.urlopen(istek, timeout=30) as yanit:
            veri = json.loads(yanit.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # 410 = onay linkinin 7 gunluk omru doldu (tokens.ts). Token'i hicbir
        # sey diriltmiyor; bu kayit artik yalnizca SaaS panelinden okunabilir.
        sebep = "onay linkinin suresi doldu (410)" if e.code == 410 else f"HTTP {e.code}"
        return None, sebep
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return None, f"SaaS'a ulasilamadi ({type(e).__name__})"
    except json.JSONDecodeError:
        return None, "SaaS yaniti JSON degil"
    return (veri.get("post") or veri), None


def _saas_zaman(metin):
    """SaaS'in `publishedAt` damgasini TR saatine cevirir.

    Prisma tarihi `...Z` ile bitiriyor; `fromisoformat` bunu Python 3.11'den
    once okuyamaz, o yuzden ofset elle yazilir. Alan yoksa None doner ve cagiran
    "tespit ani"na duser.
    """
    if not metin:
        return None
    dt = iso_oku(str(metin).replace("Z", "+00:00"))
    return dt.astimezone(TR_SAAT) if dt else None


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
    # soyluyor ve o kimlik bilgisi istemiyor. Bu yuzden Instagram'a bakilamadigi
    # HICBIR durumda esitleme durmaz — ne token alinamadiginda (asagida) ne de
    # cagri basarisiz oldugunda (bir sonraki blok). Sadece karsilastirma atlanir
    # ve NEDEN atlandigi rapora yazilir, sessiz kalmaz.
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
            # Token alindi ama cagri basarisiz. Sonuc token hic alinamamasiyla
            # ayni: karsilastirma yapilamiyor. Bu yuzden tepki de ayni olmali.
            #
            # Burasi eskiden tum calismayi dusuruyordu ve bir kez gercekten
            # dusurdu: bulut oturumunun cikis proxy'si graph.instagram.com'a
            # CONNECT'i 403 ile kesince Faz 1 hata verdi, Faz 2 hic calismadi,
            # o gun 15:07 yuvasina post konmadi. Halbuki Faz 1'in asil isi olan
            # "bekleyen postun akibeti" bilgisi SaaS'in public onay
            # endpoint'inden geliyor ve o cagri Instagram'a hic dokunmuyor.
            # Emniyet agi koptu diye ana mekanizma durmasin.
            medyalar = []
            ig_atlandi = (
                "Instagram karsilastirmasi atlandi — "
                + " ".join(hata.rapor().split())
            )

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
            "tur": post.get("tur", "gorsel"),
            # Video postunda repoda hic jpg yok; "0 slayt" yaniltici olurdu.
            "slayt": 1 if post.get("tur") == "video" else len(post["slaytlar"]),
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
    saas, saas_hatasi = _saas_durum(bekleyen.get("onay_url", "")) if bekleyen \
        else (None, None)
    bekleyen_karari = None

    if bekleyen and saas is None:
        # Cevap alinamadi: KARAR YOK. Bekleyen korunur, defter degismez —
        # akibeti bilinmeyen bir postu "onaylanmadi" sayip sessizce havuza
        # geri koymak, SaaS onu yayinlamissa mukerrer gonderime yol acar.
        bekleyen_karari = {"sonuc": "saas_okunamadi", "slug": bekleyen["slug"],
                           "sebep": saas_hatasi}

    if saas:
        yayin = saas.get("publishStatus")
        onay = saas.get("status")
        link = saas.get("igPermalink") or ""
        if onay == "rejected":
            bekleyen_karari = {"sonuc": "reddedildi", "slug": bekleyen["slug"]}
        elif yayin == "duplicate" and not link:
            # Damga var ama kardesin linki yok: icerigin yayinda oldugunu
            # biliyoruz, NEREDE oldugunu bilmiyoruz. Deftere linksiz kayit
            # yazmak bir sonraki tam esitlemede dusurulur; karar vermek yerine
            # bekleyeni koruyup bildiriyoruz.
            bekleyen_karari = {"sonuc": "mukerrer_link_yok", "slug": bekleyen["slug"]}
        elif yayin in ("published", "duplicate"):
            # duplicate = SaaS'in mukerrer korumasi: ayni externalRef'li BASKA
            # bir kayit canlida bulundugu icin bu kayit yayinlanmadi
            # (publish-post.ts > markDuplicate). Damga yalnizca Graph API
            # medyayi "live" dogruladiginda yaziliyor — yani icerik Instagram'da
            # ve `igPermalink` o canli kardesin linki. Repo acisindan sonuc
            # `published` ile ayni: icerik yayinda, deftere girmeli, havuzdan
            # cikmali. Ayrim `mukerrer` bayragiyla raporda korunur.
            mukerrer = yayin == "duplicate"
            # Instagram sorgulanmadiysa "silinmis mi" bilinemez; yayinlanmis kabul
            # edilir. Yanlissa bir sonraki tam esitleme kaydi dusurur.
            canli = True if ig_atlandi else (_kod(link) in canli_kodlar)
            # Yayin ani SaaS'in kaydi; bu esitlemenin kostugu an DEGIL. Eslesme
            # cogu zaman ertesi gunun cron'unda kuruldugu icin "simdi" yazmak
            # her kaydi bir gun ileri kaydiriyordu.
            #
            # duplicate'te bu kayit hic yayinlanmadigi icin `publishedAt` bos
            # gelir; yayin ani kardes kaydin verisi ve token'la okunamiyor, o
            # yuzden tespit anina dusuluyor (kayitta `zaman_kaynagi: tespit`).
            yayin_ani = _saas_zaman(saas.get("publishedAt"))
            bekleyen_karari = {
                "sonuc": "yayinlandi" if canli else "yayinlandi_sonra_silindi",
                "slug": bekleyen["slug"],
                "permalink": link,
                "yayin_zamani": iso(yayin_ani or simdi()),
                "zaman_kaynagi": "saas" if yayin_ani else "tespit",
            }
            if mukerrer:
                bekleyen_karari["mukerrer"] = True
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
                    "yayin_zamani": iso(yayin_ani or simdi()),
                    "not": ("SaaS mukerrer damgaladi: icerik zaten canlida, link "
                            "canli kardes kaydin; yayin saati okunamadi, tespit "
                            "ani yazildi") if mukerrer else
                           "SaaS yayinladi (onay endpoint'inden dogrulandi)" if yayin_ani
                           else "SaaS yayinladi; yayin saati gelmedi, tespit ani yazildi",
                })
        elif yayin == "failed":
            bekleyen_karari = {"sonuc": "yayin_hatasi", "slug": bekleyen["slug"]}
        elif yayin == "skipped":
            bekleyen_karari = {"sonuc": "atlandi_instagram_bagli_degil",
                               "slug": bekleyen["slug"]}
        elif onay == "revision_requested":
            bekleyen_karari = {"sonuc": "revizyon_istendi", "slug": bekleyen["slug"]}
        elif yayin == "scheduled":
            bekleyen_karari = {"sonuc": "yayin_zamanlandi", "slug": bekleyen["slug"]}
        elif yayin == "publishing":
            bekleyen_karari = {"sonuc": "yayin_suruyor", "slug": bekleyen["slug"]}
        elif onay == "pending":
            bekleyen_karari = {"sonuc": "onay_bekliyor", "slug": bekleyen["slug"]}
        elif onay == "approved" and yayin == "idle":
            # SaaS'in "awaitingPublish" hali: onay verilmis ama yayin hic
            # denenmemis. Normal akista imkansiz (onay transaction'i biter
            # bitmez yayin calisir), yani buraya dusen post SaaS tarafinda
            # takilmis demektir — onay sayfasindaki "tekrar dene" isi gorur.
            bekleyen_karari = {"sonuc": "onaylandi_yayin_denenmedi",
                               "slug": bekleyen["slug"]}
        else:
            # SaaS'in sozlugu bu repodan bagimsiz buyuyor. Taninmayan bir deger
            # gelince SESSIZ KALMAK en kotusu: 13.09'da `duplicate` boyle bir
            # degerdi, hicbir dala girmedi, rapor bos dondu ve gozetimsiz
            # calisma "ne oldugunu bilmiyorum" diyemeden durdu. Artik bilinmeyen
            # her bileske adiyla raporlanir; karar yine verilmez (bekleyen
            # korunur, defter degismez) ama en azindan gorunur olur.
            bekleyen_karari = {
                "sonuc": "bilinmeyen_saas_durumu",
                "slug": bekleyen["slug"],
                "status": onay,
                "publishStatus": yayin,
                "permalink": link or None,
            }

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
            yayin_ani = iso_oku(bekleyen_karari.get("yayin_zamani")) or simdi()
            durum["son_yayin"] = iso(yayin_ani)
            # Sayac takvim gunune bagli: dun yayinlanip bugun fark edilen bir post
            # bugune yazilirsa defter "bugun iki post cikti" diye okunuyor.
            if yayin_ani.date() == simdi().date():
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
