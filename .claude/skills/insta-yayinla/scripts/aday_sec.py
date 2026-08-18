"""Siradaki Instagram postunu secer.

Secim kurali: **kategori rotasyonu + puan** — en uzun suredir yayinlanmamis
kategoriden, o kategori icinde **en yuksek puanli** posttan baslanir. Rotasyon
feed'de arka arkaya iki ayni tur post cikmasini engeller; puan da o kategorinin
en iyi postunun once gitmesini saglar.

Puan ELEMEZ, yalnizca siralar: puani olmayan ya da olcut surumu eskimis post
kategorisinin sonuna duser ama aday havuzunda kalir. Puan postun KALITESINI
olcer; gorseldeki harf hatalari ve sablon sapmalari puana girmez, onlarin
defteri HATA-RAPORU.md. Karar gecmisi: TODOS.md > "Post puanlama sistemi";
puani ureten: puanla.py.

Kullanim:
    python aday_sec.py                  # siradaki adayi sec, JSON bas
    python aday_sec.py --dry-run        # ayni sey + stderr'e okunakli ozet
    python aday_sec.py --slug dizi/my-bad   # belirli bir postun verisini bas
    python aday_sec.py --durum          # havuz istatistigi (stok kontrolu icin)

Cikis kodu: 0 basarili, 1 uygun aday yok / hata.
"""

from __future__ import annotations

import argparse
import sys

from furi_ortak import (
    MAX_CAPTION,
    MAX_HASHTAG,
    MAX_KARUSEL,
    MAX_ALT_TEXT,
    STOK_ESIGI,
    caption_ayristir,
    caption_birlestir,
    defter_oku,
    durum_oku,
    ilk_commit_zamani,
    iso_oku,
    json_bas,
    postlari_tara,
    puan_ozet,
    raw_taban,
    raw_url,
    repo_kok,
    url_erisilebilir,
    utf8_cikti,
)


def _dislanan_sluglar(durum: dict, defter: dict) -> dict[str, str]:
    """slug -> dislanma sebebi"""
    dislanan: dict[str, str] = {}
    for kayit in defter.get("kayitlar", []):
        if kayit.get("slug"):
            dislanan[kayit["slug"]] = "yayinlandi"
    for kayit in durum.get("atlananlar", []):
        if kayit.get("slug"):
            dislanan[kayit["slug"]] = f"atlandi ({kayit.get('sebep', 'sebep yok')})"
    bekleyen = durum.get("bekleyen")
    if bekleyen and bekleyen.get("slug"):
        dislanan[bekleyen["slug"]] = "onay bekliyor"
    deneme = durum.get("yayin_denemesi")
    if deneme and deneme.get("slug"):
        dislanan[deneme["slug"]] = "yayin denemesi devam ediyor"
    return dislanan


def _kategori_son_yayin(defter: dict) -> dict[str, float]:
    son: dict[str, float] = {}
    for kayit in defter.get("kayitlar", []):
        kategori = kayit.get("kategori")
        zaman = iso_oku(kayit.get("yayin_zamani"))
        if not kategori or not zaman:
            continue
        an = zaman.timestamp()
        if an > son.get(kategori, 0.0):
            son[kategori] = an
    return son


def veri_topla(kok, post: dict, taban: str, url_kontrol: bool = True) -> tuple[dict, list[str]]:
    """Bir postun yayin verisini kurar. (veri, sorunlar) doner."""
    sorunlar: list[str] = []
    slaytlar = post["slaytlar"]

    if len(slaytlar) > MAX_KARUSEL:
        sorunlar.append(f"{len(slaytlar)} slayt — Instagram karusel limiti {MAX_KARUSEL}")

    ayristirilmis = caption_ayristir(post["yol"] / "caption.md")
    caption = caption_birlestir(ayristirilmis)

    if not ayristirilmis["aciklama"]:
        sorunlar.append("caption.md icinde '## Aciklama' bolumu bos veya yok")
    if len(caption) > MAX_CAPTION:
        sorunlar.append(f"caption {len(caption)} karakter — limit {MAX_CAPTION}")
    if len(ayristirilmis["hashtagler"]) > MAX_HASHTAG:
        sorunlar.append(
            f"{len(ayristirilmis['hashtagler'])} hashtag — limit {MAX_HASHTAG}"
        )

    gorseller = []
    for sira, dosya in enumerate(slaytlar, start=1):
        url = raw_url(taban, post["slug"], dosya.name)
        alt = (ayristirilmis["alt_text"].get(sira) or "").strip()[:MAX_ALT_TEXT]
        girdi = {"no": sira, "dosya": dosya.name, "url": url, "alt_text": alt}
        if url_kontrol:
            tamam, mesaj = url_erisilebilir(url)
            girdi["erisim"] = mesaj
            if not tamam:
                sorunlar.append(f"{dosya.name}: {mesaj}")
        gorseller.append(girdi)

    veri = {
        "slug": post["slug"],
        "kategori": post["kategori"],
        "ad": post["ad"],
        "slayt": len(slaytlar),
        "gorseller": gorseller,
        "caption": caption,
        "caption_uzunluk": len(caption),
        "hashtagler": ayristirilmis["hashtagler"],
        "raw_taban": taban,
    }
    return veri, sorunlar


def komut_sec(kok, args) -> int:
    durum = durum_oku(kok)
    defter = defter_oku(kok)
    taban = raw_taban(kok)

    postlar = postlari_tara(kok)
    dislanan = _dislanan_sluglar(durum, defter)
    adaylar = [p for p in postlar if p["slug"] not in dislanan]

    if not adaylar:
        json_bas(
            {
                "durum": "aday_yok",
                "mesaj": "Yayinlanmamis post kalmadi. insta-ingilizce ile yeni post uretilmeli.",
                "havuz": len(postlar),
                "dislanan": len(dislanan),
            }
        )
        return 1

    kategori_son = _kategori_son_yayin(defter)
    ilk_commit_onbellek: dict[str, int] = {}
    puanlar = {p["slug"]: puan_ozet(p["yol"]) for p in adaylar}

    def sira_anahtari(post: dict):
        slug = post["slug"]
        if slug not in ilk_commit_onbellek:
            ilk_commit_onbellek[slug] = ilk_commit_zamani(kok, slug)
        puan = puanlar[slug]
        return (
            kategori_son.get(post["kategori"], 0.0),  # en eski kategori once
            post["kategori"],
            0 if puan["var"] else 1,                  # puansiz/bayat kategorinin sonuna
            -(puan["toplam"] or 0.0),                 # kategori icinde en yuksek puan
            ilk_commit_onbellek[slug],                # esitlik bozucu: en eski post
            post["ad"],
        )

    adaylar.sort(key=sira_anahtari)

    elenenler: list[dict] = []
    for post in adaylar:
        veri, sorunlar = veri_topla(kok, post, taban)
        if sorunlar:
            elenenler.append({"slug": post["slug"], "sorunlar": sorunlar})
            continue

        veri["durum"] = "secildi"
        veri["puan"] = puanlar[post["slug"]]
        veri["kalan_aday"] = len(adaylar) - len(elenenler) - 1
        veri["stok_dusuk"] = veri["kalan_aday"] < STOK_ESIGI
        if elenenler:
            veri["elenenler"] = elenenler

        if args.dry_run:
            _ozet_bas(veri, len(postlar), len(dislanan), elenenler)
        json_bas(veri)
        return 0

    json_bas(
        {
            "durum": "uygun_aday_yok",
            "mesaj": "Aday var ama hicbiri dogrulamayi gecemedi.",
            "elenenler": elenenler,
        }
    )
    return 1


def _ozet_bas(veri: dict, havuz: int, dislanan: int, elenenler: list[dict]) -> None:
    y = sys.stderr.write
    y("\n" + "=" * 62 + "\n")
    y(f"  SECILEN: {veri['slug']}\n")
    y("=" * 62 + "\n")
    y(f"  kategori     : {veri['kategori']}\n")
    puan = veri.get("puan") or {}
    if puan.get("hal") == "guncel":
        y(f"  puan         : {puan['toplam']}\n")
    elif puan.get("hal") == "bozuk":
        y(f"  puan         : BOZUK — {puan['sorun']}\n")
    elif puan.get("hal") == "bayat":
        y(f"  puan         : BAYAT — olcut surumu {puan['olcut_surumu']}, yeniden puanlanmali\n")
    else:
        y("  puan         : YOK\n")
    y(f"  slayt        : {veri['slayt']}\n")
    y(f"  caption      : {veri['caption_uzunluk']} karakter (limit {MAX_CAPTION})\n")
    y(f"  hashtag      : {len(veri['hashtagler'])} adet\n")
    y(f"  havuz        : {havuz} post, {dislanan} dislanan, {veri['kalan_aday']} aday kaldi\n")
    if veri["stok_dusuk"]:
        y(f"  ! STOK DUSUK : esik {STOK_ESIGI}\n")
    y("\n  gorseller:\n")
    for g in veri["gorseller"]:
        alt = (g["alt_text"][:52] + "...") if len(g["alt_text"]) > 55 else g["alt_text"]
        y(f"    {g['no']}. {g['dosya']:<8} {g.get('erisim', '-'):<6} alt: {alt or '(YOK)'}\n")
    if elenenler:
        y("\n  elenen adaylar:\n")
        for e in elenenler:
            y(f"    {e['slug']}: {'; '.join(e['sorunlar'])}\n")
    y("\n  caption onizleme:\n")
    for satir in veri["caption"].splitlines()[:6]:
        y(f"    | {satir[:70]}\n")
    y("=" * 62 + "\n\n")


def komut_slug(kok, args) -> int:
    hedef = args.slug.replace("\\", "/").strip("/")
    for post in postlari_tara(kok):
        if post["slug"] == hedef:
            veri, sorunlar = veri_topla(kok, post, raw_taban(kok), url_kontrol=not args.hizli)
            veri["durum"] = "hata" if sorunlar else "ok"
            veri["puan"] = puan_ozet(post["yol"])
            if sorunlar:
                veri["sorunlar"] = sorunlar
            json_bas(veri)
            return 1 if sorunlar else 0
    json_bas({"durum": "bulunamadi", "slug": hedef})
    return 1


def komut_durum(kok, args) -> int:
    durum = durum_oku(kok)
    defter = defter_oku(kok)
    postlar = postlari_tara(kok)
    dislanan = _dislanan_sluglar(durum, defter)
    kalan_postlar = [p for p in postlar if p["slug"] not in dislanan]
    kalan = [p["slug"] for p in kalan_postlar]

    kategori_dagilimi: dict[str, int] = {}
    for slug in kalan:
        kategori = slug.split("/", 1)[0]
        kategori_dagilimi[kategori] = kategori_dagilimi.get(kategori, 0) + 1

    # Stok uyarisi "kac post kaldi"in yaninda "kac PUANLI post kaldi"i da
    # soylemeli; kalan on postun sekizi puansizsa havuz gorundugu kadar saglam degil.
    puan_dagilimi = {"guncel": 0, "bayat": 0, "puansiz": 0, "bozuk": 0}
    toplamlar: list[float] = []
    for post in kalan_postlar:
        oz = puan_ozet(post["yol"])
        puan_dagilimi[oz["hal"]] += 1
        if oz["toplam"] is not None:
            toplamlar.append(oz["toplam"])

    json_bas(
        {
            "durum": "ok",
            "havuz": len(postlar),
            "yayinlanan": len(defter.get("kayitlar", [])),
            "atlanan": len(durum.get("atlananlar", [])),
            "kalan_aday": len(kalan),
            "stok_dusuk": len(kalan) < STOK_ESIGI,
            "stok_esigi": STOK_ESIGI,
            "kategori_dagilimi": kategori_dagilimi,
            "puan_dagilimi": puan_dagilimi,
            "puan_ortalamasi": round(sum(toplamlar) / len(toplamlar), 2) if toplamlar else None,
            "en_dusuk_puan": min(toplamlar) if toplamlar else None,
            "en_yuksek_puan": max(toplamlar) if toplamlar else None,
            "kalan_sluglar": kalan,
        }
    )
    return 0


def main() -> int:
    utf8_cikti()
    ayrist = argparse.ArgumentParser(description="Siradaki Instagram postunu secer.")
    ayrist.add_argument("--repo", help="Repo kok dizini (varsayilan: script konumundan turetilir)")
    ayrist.add_argument("--slug", help="Belirli bir postun verisini bas (secim yapma)")
    ayrist.add_argument("--durum", action="store_true", help="Havuz istatistigi bas")
    ayrist.add_argument("--dry-run", action="store_true", help="Secime ek olarak okunakli ozet")
    ayrist.add_argument("--hizli", action="store_true", help="--slug ile: URL kontrolunu atla")
    args = ayrist.parse_args()

    kok = repo_kok(args.repo)
    if not kok.is_dir():
        sys.stderr.write(f"HATA: repo bulunamadi: {kok}\n")
        return 1

    if args.durum:
        return komut_durum(kok, args)
    if args.slug:
        return komut_slug(kok, args)
    return komut_sec(kok, args)


if __name__ == "__main__":
    raise SystemExit(main())
