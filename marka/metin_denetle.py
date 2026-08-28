"""kart.json metinlerini yayindan once denetler.

Gorsel artik metni bozamiyor (marka/kart_bas.ps1 harfleri gercek fontla
basiyor), bu yuzden tek risk metnin KENDISI. Bu betik onu okur.

Iki kontrol:

1. **Eksik diyakritik.** Sozluk elle tutulmuyor: repodaki caption.md
   dosyalarindan turetiliyor. Caption'lar bastan beri duzgun Turkce yazildigi
   icin dogal bir referans. Bir kelimenin ASCII'ye katlanmis hali sozlukteki
   diyakritikli bir kelimeyle eslesiyor ama kendisi diyakritiksizse, ASCII
   kalintisidir: `lazim` -> `lazım`, `icin` -> `için`.

2. **Uzunluk siniri.** WORKFLOW.md Faz 2: dev baslik <= 22, Ingilizce cumle
   <= 60, Turkce ceviri <= 70 karakter.

Kullanim:
    python marka/metin_denetle.py <kart.json> [...]
    python marka/metin_denetle.py --tumu        # repodaki tum kart.json'lar

Cikis kodu: 0 temiz, 1 bulgu var.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Windows'ta stdout cp1252; bulgu metnindeki `İ` betigi cokertiyordu.
for _akis in (sys.stdout, sys.stderr):
    if hasattr(_akis, "reconfigure"):
        _akis.reconfigure(encoding="utf-8", errors="replace")

KOK = Path(__file__).resolve().parent.parent

KATLAMA = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")

# Turkce buyuk/kucuk harf. Python'un kendi `.lower()`i `İ` icin `i` + birlesik
# nokta (U+0307) uretiyor; o kalinti sozluge girince `iyi` gibi tertemiz bir
# kelime "diyakritiksiz" diye isaretleniyordu.
BUYUK_HARF = str.maketrans("çğıiöşü", "ÇĞIİÖŞÜ")
KUCUK_HARF = str.maketrans("İI", "iı")
SINIR = {
    # tekil kart
    "baslik": 22, "ornek": 60, "anlam": 70, "cta": 45, "etiket": 30,
    # deste slaytlari: kapak basligi bir cumle oldugu icin baslikdan uzun
    # olabiliyor (iki satira boluniyor), sik metni kutuya sigmak zorunda.
    "kapak": 40, "sayac": 16, "soru": 70, "sik": 24, "madde": 30, "aciklama": 85,
    # phrasal/karistirilan/hikayeli kartlarindaki lacivert kalin cumle satiri
    # ve kart ortasindaki turuncu ara etiket
    "cumle": 70, "araetiket": 24,
}

# Kategori etiketi her kartin en ustunde duruyor; tek harf sapmasi tum feed'de
# goze carpar. Cikarim yerine sabit liste: `DIZI` mi `DİZİ` mi sorusunun
# caption'lardan turetilecek hali yok (kelimenin kendisinde diyakritik yok).
ETIKETLER = {
    "DİZİ İNGİLİZCESİ",
    "DURUMSAL İNGİLİZCE",
    "GÜNÜN PHRASAL VERB'Ü",
    "SIK KARIŞTIRILANLAR",
    "KİTAP vs GERÇEK",
    "TÜRKÇE TUZAĞI",
}
ETIKET_TEST = re.compile(r"^(A1|A2|B1|B2|C1|C2) • İNGİLİZCE TESTİ$")


# Turkce soru eki: `mi/mi/mu/mu` + sahis eki. Dort harmoni varyantinin ikisi
# (`mi...`, `mu...`) diyakritiksizdir ve ikisi de DOGRUDUR — hangisinin
# gelecegini onceki hecenin unlusu belirler. ASCII katlamasi dordunu tek
# torbaya attigi icin `durur musunuz` -> `müsünüz` gibi uydurma bulgu
# uretiyordu. Bu formlar diyakritik denetiminden muaf.
SORU_EKI = {
    "misin", "misiniz", "miyim", "miyiz", "midir", "miydi", "miyiz",
    "musun", "musunuz", "muyum", "muyuz", "mudur", "muydu",
}


def katla(s: str) -> str:
    return s.translate(KATLAMA)


def buyuk(s: str) -> str:
    return s.translate(BUYUK_HARF).upper()


def kucuk(s: str) -> str:
    return s.translate(KUCUK_HARF).lower()


def sozluk_kur() -> tuple[dict[str, set[str]], dict[str, str]]:
    """caption.md'lerden iki sozluk turetir.

    - `sozluk`: ASCII karsiligi -> diyakritikli yazimlar (eksik diyakritik icin)
    - `nokta`:  ASCII karsiligi -> kelimenin kendisi (buyuk harf I/İ icin)
    """
    sozluk: dict[str, set[str]] = {}
    nokta: dict[str, str] = {}
    for cap in KOK.glob("*/*/caption.md"):
        for kelime in re.findall(r"[A-Za-zçğıöşüÇĞİÖŞÜ]{3,}", cap.read_text(encoding="utf-8")):
            duz = katla(kelime).lower()
            # Olcut kelimenin kendisi degil KUCUK hali: cumle basindaki `İyi`
            # diyakritikli gorunur ama kucugu `iyi`dir.
            #
            # ASCII buyuk `I` ayrica belirsiz: Turkce kurala gore kucugu `ı`,
            # caption'larda ise `İ` yerine de yaziliyor (`Iyi`). Bu yuzden `I`
            # iceren kelimenin iki okunusu birden denenir. Okunuslardan biri
            # diyakritiksizse kelime sozluge degil `nokta`ya yazilir — yoksa
            # tertemiz bir `iyi`, uydurma bir `ıyi` ile karsilastirilip bulgu
            # uretirdi.
            okunuslar = {kucuk(kelime)}
            if "I" in kelime:
                okunuslar.add(kucuk(kelime.replace("I", "i")))
            diyakritikli = {o for o in okunuslar if katla(o) != o}
            if len(diyakritikli) == len(okunuslar):
                sozluk.setdefault(duz, set()).update(diyakritikli)
            else:
                sade = sorted(okunuslar - diyakritikli)[0]
                if "i" in sade:
                    nokta.setdefault(duz, sade)
    return sozluk, nokta


def denetle(yol: Path, sozluk: dict[str, set[str]], nokta: dict[str, str]) -> list[str]:
    bulgular: list[str] = []
    veri = json.loads(yol.read_text(encoding="utf-8"))
    for no, slayt in enumerate(veri.get("slaytlar", []), start=1):
        for oge in slayt.get("ogeler", []):
            tur, metin = oge.get("tur", "?"), oge.get("metin", "")
            if not metin:
                continue

            kanonik_etiket = tur == "etiket" and (
                metin in ETIKETLER or bool(ETIKET_TEST.match(metin))
            )
            if tur == "etiket" and not kanonik_etiket:
                bulgular.append(
                    f"slayt {no} · etiket: {metin!r} kanonik etiket degil — "
                    f"marka/README.md > Kategori etiketleri"
                )

            sinir = SINIR.get(tur)
            if sinir and len(metin) > sinir:
                bulgular.append(f"slayt {no} · {tur}: {len(metin)} karakter, sinir {sinir} — {metin!r}")

            # Kanonik etiket zaten harfi harfine dogrulandi; kelime kelime
            # yeniden denetlemek yalnizca yanlis alarm uretir. `SIK
            # KARISTIRILANLAR`daki `SIK` dogrudur (`sık`), ama sozluk
            # caption'lardan turedigi icin `sık` iceren caption silinince
            # geriye `şık` kaliyor ve `SIK` "SİK/ŞİK olmali" diye
            # isaretleniyordu. Sozlugun icerigi degistikce denetimin sonucu
            # degismemeli.
            if kanonik_etiket:
                continue

            # Ingilizce oge: sozluk Turkce caption'lardan turedigi icin
            # `SAYING` -> `SAYİNG` gibi uydurma bulgular uretiyordu. Dil
            # tahmin edilmiyor, kart.json'da yaziyor. Uzunluk siniri ve
            # kanonik etiket denetimi yine de gecerli.
            dil = oge.get("dil")
            if dil == "en":
                continue

            for kelime in re.findall(r"[A-Za-zçğıöşüÇĞİÖŞÜ]{3,}", metin):
                duz = katla(kelime).lower()
                adaylar = set(sozluk.get(duz, ()))
                if duz in nokta:
                    adaylar.add(nokta[duz])
                if not adaylar:
                    continue

                # Buyuk harfte `ı` ve `i` ayrisir (`I` / `İ`), yani buyuk
                # yazilmis bir kelimede diyakritik eksik GORUNUR ama dogru
                # olabilir: `ANAHTARI` dogru, `KAYDIR` dogru, `TESTI` degil.
                # Karsilastirma bu yuzden adaylarin Turkce buyuk hali uzerinden.
                # `karisik`: satirda hem Ingilizce terim hem Turkce karsilik
                # var (`REMIND: Hatirlatmak`). Buyuk harf I/İ kurali Ingilizce
                # terimde uydurma bulgu uretiyor; diyakritik denetimi Turkce
                # kelimeler icin gecerli kalir.
                if kelime == buyuk(kelime):
                    if dil == "karisik":
                        continue
                    dogrular = {buyuk(a) for a in adaylar}
                    if kelime not in dogrular:
                        bulgular.append(
                            f"slayt {no} · {tur}: {kelime!r} — Turkce buyuk harfte "
                            f"{'/'.join(sorted(dogrular))} olmali"
                        )
                    continue

                if katla(kelime) != kelime:        # zaten diyakritikli, temiz
                    continue
                # Burada yalnizca `sozluk` konusur: `nokta` diyakritiksiz
                # kelimelerin kendisini tutuyor, onu aday saymak her temiz
                # kelimeyi kendisiyle karsilastirip bulgu uretirdi.
                if kucuk(kelime) in SORU_EKI:
                    continue
                yazimlar = sozluk.get(duz)
                if yazimlar:
                    bulgular.append(
                        f"slayt {no} · {tur}: {kelime!r} diyakritiksiz — "
                        f"caption'larda {'/'.join(sorted(yazimlar))} olarak geciyor"
                    )
    return bulgular


def main() -> int:
    argv = sys.argv[1:]
    if not argv:
        print(__doc__.strip().splitlines()[0])
        print("kullanim: python marka/metin_denetle.py <kart.json> | --tumu")
        return 1

    yollar = (sorted(KOK.glob("*/*/kart.json")) if argv[0] == "--tumu"
              else [Path(a).resolve() for a in argv])
    if not yollar:
        print("kart.json bulunamadi")
        return 1

    sozluk, nokta = sozluk_kur()
    toplam = 0
    for yol in yollar:
        bulgular = denetle(yol, sozluk, nokta)
        toplam += len(bulgular)
        durum = "TEMIZ" if not bulgular else f"{len(bulgular)} BULGU"
        try:
            ad = yol.relative_to(KOK)
        except ValueError:
            ad = yol
        print(f"{ad}: {durum}")
        for b in bulgular:
            print(f"  ! {b}")
    print(f"\n{len(yollar)} kart, {len(sozluk)} sozluk girdisi, {toplam} bulgu")
    return 1 if toplam else 0


if __name__ == "__main__":
    sys.exit(main())
