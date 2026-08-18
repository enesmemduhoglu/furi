"""Post puanlarini tarar, dogrular ve yazar.

Puani Claude verir; bu script puanlamaz. Isi tarama (kim puansiz, kimin puani
bayat), dogrulama (sema, aralik, gerekce) ve yazmadir (`toplam` hesabi tek
yerde kalsin diye). Karar gecmisi: TODOS.md > "Post puanlama sistemi".

Kullanim:
    python puanla.py                       # puansiz + bozuk + bayat postlari listele
    python puanla.py --eksik               # sadece puani hic olmayanlar
    python puanla.py --bayat               # sadece olcut surumu eski olanlar
    python puanla.py --tumu                # havuzun tamami, puan durumuyla
    python puanla.py --slug dizi/my-bad    # tek postun puani + puanlama malzemesi
    python puanla.py --sema                # dallar, kontroller, formul
    python puanla.py --yaz dizi/my-bad < puan.json     # puan yaz (stdin JSON)
    python puanla.py --yaz dizi/my-bad --dosya p.json  # puan yaz (dosyadan)
    python puanla.py --yaz dizi/my-bad --kuru < p.json # yazmadan dogrula

--yaz'in bekledigi JSON yalnizca su iki alani tasir; `toplam`, `olcut_surumu`,
`tarih` ve `model` script tarafindan eklenir (elle verilse de ezilir):

    {"dallar": {"ilgi_cekicilik": {"puan": 7, "gerekce": "..."}, ...},
     "kontroller": {"gorselde_harf_hatasi": false, ...}}

Cikis kodu: 0 basarili, 1 hata / dogrulama basarisiz.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from furi_ortak import (
    KONTROL_CEZASI,
    OLCUT_SURUMU,
    PUAN_ALT,
    PUAN_DALLARI,
    PUAN_KONTROLLERI,
    PUAN_UST,
    basarisiz_kontroller,
    caption_ayristir,
    defter_oku,
    durum_oku,
    json_bas,
    postlari_tara,
    puan_dogrula,
    puan_oku,
    puan_yaz,
    repo_kok,
    simdi,
    toplam_hesapla,
    utf8_cikti,
)

VARSAYILAN_MODEL = "claude-opus-5"


def _yayinlanan_sluglar(kok: Path) -> set[str]:
    """Yayinlanmis ve atlanmis postlar. Puanlama havuzu bunlari kapsamaz.

    Gerekce: puan aday secimini beslemek icin var; bir daha aday olmayacak
    postu puanlamak zamani bosa harcar. Yine de --tumu ile gorunurler, cunku
    "neden bu puansiz" sorusunun cevabi lazim olabiliyor.
    """
    disarida = {k["slug"] for k in defter_oku(kok).get("kayitlar", []) if k.get("slug")}
    disarida |= {k["slug"] for k in durum_oku(kok).get("atlananlar", []) if k.get("slug")}
    return disarida


def _post_durumu(post: dict, disarida: set[str]) -> dict:
    veri, sorun = puan_oku(post["yol"])
    surum = veri.get("olcut_surumu") if veri else None
    if sorun:
        hal = "bozuk"
    elif veri is None:
        hal = "puansiz"
    elif not isinstance(surum, int) or surum < OLCUT_SURUMU:
        hal = "bayat"
    else:
        hal = "guncel"

    kayit = {
        "slug": post["slug"],
        "kategori": post["kategori"],
        "hal": hal,
        "toplam": veri["toplam"] if veri else None,
        "olcut_surumu": surum,
        "aday": post["slug"] not in disarida,
    }
    if sorun:
        kayit["sorun"] = sorun
    if veri and veri.get("toplam_yeniden_hesaplandi"):
        kayit["not"] = "dosyadaki toplam formulle uyusmuyordu, yeniden hesaplandi"
    return kayit


def _malzeme(post: dict) -> dict:
    """Puanlamak icin acilmasi gereken dosyalar + caption metni.

    Gorselleri Claude kendi okur; script sadece nerede olduklarini soyler.
    """
    ayristirilmis = caption_ayristir(post["yol"] / "caption.md")
    return {
        "yol": str(post["yol"]),
        "slaytlar": [str(p) for p in post["slaytlar"]],
        "caption_yolu": str(post["yol"] / "caption.md"),
        "aciklama": ayristirilmis["aciklama"],
        "hashtagler": ayristirilmis["hashtagler"],
        "alt_text": {str(k): v for k, v in sorted(ayristirilmis["alt_text"].items())},
    }


def komut_liste(kok: Path, args) -> int:
    disarida = _yayinlanan_sluglar(kok)
    postlar = postlari_tara(kok)
    kayitlar = [_post_durumu(p, disarida) for p in postlar]

    if args.tumu:
        secilen = kayitlar
        baslik = "tumu"
    elif args.eksik:
        secilen = [k for k in kayitlar if k["hal"] == "puansiz"]
        baslik = "eksik"
    elif args.bayat:
        secilen = [k for k in kayitlar if k["hal"] == "bayat"]
        baslik = "bayat"
    else:
        secilen = [k for k in kayitlar if k["hal"] != "guncel"]
        baslik = "islenmemis"

    if not args.tumu:
        # Yayinlanmis/atlanmis postu puanlamak bosa is; --tumu bunlari yine gosterir.
        secilen = [k for k in secilen if k["aday"]]

    sayim: dict[str, int] = {}
    for k in kayitlar:
        if k["aday"]:
            sayim[k["hal"]] = sayim.get(k["hal"], 0) + 1

    if args.malzeme:
        yol_haritasi = {p["slug"]: p for p in postlar}
        for kayit in secilen:
            kayit["malzeme"] = _malzeme(yol_haritasi[kayit["slug"]])

    json_bas(
        {
            "durum": "ok",
            "kume": baslik,
            "olcut_surumu": OLCUT_SURUMU,
            "havuz": len(postlar),
            "aday_dagilimi": sayim,
            "sayi": len(secilen),
            "postlar": secilen,
        }
    )
    return 0


def komut_slug(kok: Path, args) -> int:
    hedef = args.slug.replace("\\", "/").strip("/")
    for post in postlari_tara(kok):
        if post["slug"] != hedef:
            continue
        veri, _ = puan_oku(post["yol"])
        cikti = _post_durumu(post, _yayinlanan_sluglar(kok))
        cikti["durum"] = "ok"
        if veri:
            cikti["puan"] = veri
            cikti["basarisiz_kontroller"] = basarisiz_kontroller(veri["kontroller"])
        cikti["malzeme"] = _malzeme(post)
        json_bas(cikti)
        return 0
    json_bas({"durum": "bulunamadi", "slug": hedef})
    return 1


def komut_sema(kok: Path, args) -> int:
    json_bas(
        {
            "durum": "ok",
            "olcut_surumu": OLCUT_SURUMU,
            "puan_araligi": [PUAN_ALT, PUAN_UST],
            "dallar": PUAN_DALLARI,
            "kontroller": {
                ad: "kusursuz postta beklenen deger: " + str(beklenen).lower()
                for ad, beklenen in PUAN_KONTROLLERI.items()
            },
            "kontrol_cezasi": KONTROL_CEZASI,
            "formul": (
                "toplam = ortalama(" + str(len(PUAN_DALLARI)) + " dal) - "
                + str(KONTROL_CEZASI) + " * basarisiz_kontrol_sayisi"
            ),
            "not": (
                "Her dal icin kisa bir gerekce zorunlu. Kontroller yargi degil "
                "evet/hayir sorusu; tartisilabilir olan sey dala yazilir."
            ),
        }
    )
    return 0


def komut_yaz(kok: Path, args) -> int:
    hedef = args.yaz.replace("\\", "/").strip("/")
    post = next((p for p in postlari_tara(kok) if p["slug"] == hedef), None)
    if post is None:
        json_bas({"durum": "bulunamadi", "slug": hedef})
        return 1

    if args.dosya:
        try:
            ham = Path(args.dosya).read_text(encoding="utf-8-sig")
        except OSError as hata:
            json_bas({"durum": "hata", "mesaj": args.dosya + " okunamadi: " + str(hata)})
            return 1
    else:
        ham = sys.stdin.buffer.read().decode("utf-8-sig", errors="replace")

    if not ham.strip():
        json_bas(
            {
                "durum": "hata",
                "mesaj": "girdi bos — JSON stdin'den ya da --dosya ile verilmeli",
            }
        )
        return 1

    try:
        girdi = json.loads(ham)
    except json.JSONDecodeError as hata:
        json_bas({"durum": "hata", "mesaj": "JSON ayristirilamadi: " + str(hata)})
        return 1

    sorunlar = puan_dogrula(girdi)
    if sorunlar:
        json_bas({"durum": "gecersiz", "slug": hedef, "sorunlar": sorunlar})
        return 1

    dallar = {
        ad: {
            "puan": girdi["dallar"][ad]["puan"],
            "gerekce": girdi["dallar"][ad]["gerekce"].strip(),
        }
        for ad in PUAN_DALLARI
    }
    kontroller = {ad: bool(girdi["kontroller"][ad]) for ad in PUAN_KONTROLLERI}

    veri = {
        "olcut_surumu": OLCUT_SURUMU,
        "tarih": simdi().date().isoformat(),
        "model": args.model,
        "dallar": dallar,
        "kontroller": kontroller,
        "toplam": toplam_hesapla(dallar, kontroller),
    }

    if args.kuru:
        json_bas({"durum": "kuru", "slug": hedef, "yazilacak": veri})
        return 0

    yol = puan_yaz(post["yol"], veri)
    json_bas(
        {
            "durum": "yazildi",
            "slug": hedef,
            "dosya": str(yol.relative_to(kok)).replace("\\", "/"),
            "toplam": veri["toplam"],
            "basarisiz_kontroller": basarisiz_kontroller(kontroller),
        }
    )
    return 0


def main() -> int:
    utf8_cikti()
    ayrist = argparse.ArgumentParser(description="Post puanlarini tarar, dogrular, yazar.")
    ayrist.add_argument("--repo", help="Repo kok dizini (varsayilan: script konumundan turetilir)")
    ayrist.add_argument("--eksik", action="store_true", help="Sadece puani hic olmayanlar")
    ayrist.add_argument("--bayat", action="store_true", help="Sadece olcut surumu eski olanlar")
    ayrist.add_argument("--tumu", action="store_true", help="Havuzun tamami")
    ayrist.add_argument("--malzeme", action="store_true", help="Listeye caption + slayt yollarini ekle")
    ayrist.add_argument("--slug", help="Tek postun puani ve puanlama malzemesi")
    ayrist.add_argument("--sema", action="store_true", help="Dallar, kontroller, formul")
    ayrist.add_argument("--yaz", metavar="SLUG", help="Puan yaz (JSON stdin'den ya da --dosya)")
    ayrist.add_argument("--dosya", help="--yaz ile: JSON'u stdin yerine bu dosyadan oku")
    ayrist.add_argument("--kuru", action="store_true", help="--yaz ile: dogrula ama yazma")
    ayrist.add_argument("--model", default=VARSAYILAN_MODEL, help="Puani veren model adi")
    args = ayrist.parse_args()

    kok = repo_kok(args.repo)
    if not kok.is_dir():
        sys.stderr.write("HATA: repo bulunamadi: " + str(kok) + "\n")
        return 1

    if args.sema:
        return komut_sema(kok, args)
    if args.yaz:
        return komut_yaz(kok, args)
    if args.slug:
        return komut_slug(kok, args)
    return komut_liste(kok, args)


if __name__ == "__main__":
    raise SystemExit(main())
