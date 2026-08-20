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
import unicodedata
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent

KATLAMA = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
SINIR = {"baslik": 22, "ornek": 60, "anlam": 70, "cta": 45, "etiket": 30}

# Kategori etiketi her kartin en ustunde duruyor; tek harf sapmasi tum feed'de
# goze carpar. Cikarim yerine sabit liste: `DIZI` mi `DİZİ` mi sorusunun
# caption'lardan turetilecek hali yok (kelimenin kendisinde diyakritik yok).
ETIKETLER = {
    "DİZİ İNGİLİZCESİ",
    "DURUMSAL İNGİLİZCE",
    "GÜNÜN PHRASAL VERB'Ü",
    "SIK KARIŞTIRILANLAR",
    "KİTAP vs GERÇEK",
}
ETIKET_TEST = re.compile(r"^(A1|A2|B1|B2|C1|C2) • İNGİLİZCE TESTİ$")


def katla(s: str) -> str:
    return s.translate(KATLAMA)


def sozluk_kur() -> tuple[dict[str, set[str]], dict[str, str]]:
    """caption.md'lerden iki sozluk turetir.

    - `sozluk`: ASCII karsiligi -> diyakritikli yazimlar (eksik diyakritik icin)
    - `nokta`:  ASCII karsiligi -> kelimenin kendisi (buyuk harf I/İ icin)
    """
    sozluk: dict[str, set[str]] = {}
    nokta: dict[str, str] = {}
    for cap in KOK.glob("*/*/caption.md"):
        for kelime in re.findall(r"[A-Za-zçğıöşüÇĞİÖŞÜ]{3,}", cap.read_text(encoding="utf-8")):
            kucuk = kelime if kelime.islower() else None
            duz = katla(kelime).lower()
            if katla(kelime) != kelime:            # diyakritik iceriyor
                sozluk.setdefault(duz, set()).add(kelime.lower())
            if kucuk and "i" in kucuk:
                nokta.setdefault(duz, kucuk)
    return sozluk, nokta


def buyuk_turkce(kelime: str, kaynak: str) -> str:
    """Turkce buyuk harf: kucuk `i` -> `İ`, `ı` -> `I`. Kaynaktaki harf sirasina bakar."""
    if len(kelime) != len(kaynak):
        return kelime
    return "".join("İ" if k == "i" else h for h, k in zip(kelime, kaynak))


def denetle(yol: Path, sozluk: dict[str, set[str]], nokta: dict[str, str]) -> list[str]:
    bulgular: list[str] = []
    veri = json.loads(yol.read_text(encoding="utf-8"))
    for no, slayt in enumerate(veri.get("slaytlar", []), start=1):
        for oge in slayt.get("ogeler", []):
            tur, metin = oge.get("tur", "?"), oge.get("metin", "")
            if not metin:
                continue

            if tur == "etiket" and metin not in ETIKETLER and not ETIKET_TEST.match(metin):
                bulgular.append(
                    f"slayt {no} · etiket: {metin!r} kanonik etiket degil — "
                    f"marka/README.md > Kategori etiketleri"
                )

            sinir = SINIR.get(tur)
            if sinir and len(metin) > sinir:
                bulgular.append(f"slayt {no} · {tur}: {len(metin)} karakter, sinir {sinir} — {metin!r}")

            for kelime in re.findall(r"[A-Za-zçğıöşüÇĞİÖŞÜ]{3,}", metin):
                duz = katla(kelime).lower()

                # Buyuk harf I/İ: Turkce'de kucuk `i`nin buyugu `İ`dir. `DIZI`
                # yerine `DİZİ` olmali; sozluk bunu yakalayamaz cunku `dizi`
                # kelimesinin kendisinde diyakritik yok.
                if kelime.isupper() and "I" in kelime and duz in nokta:
                    dogru = buyuk_turkce(kelime, nokta[duz])
                    if dogru != kelime:
                        bulgular.append(
                            f"slayt {no} · {tur}: {kelime!r} — Turkce buyuk harfte {dogru!r} olmali"
                        )
                    continue

                if katla(kelime) != kelime:        # zaten diyakritikli, temiz
                    continue
                adaylar = sozluk.get(duz)
                if adaylar:
                    bulgular.append(
                        f"slayt {no} · {tur}: {kelime!r} diyakritiksiz — "
                        f"caption'larda {'/'.join(sorted(adaylar))} olarak geciyor"
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
