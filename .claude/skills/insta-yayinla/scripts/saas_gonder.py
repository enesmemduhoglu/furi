"""Siradaki postu content-approval-saas'a gonderir; onay maili oradan gider.

Yayini artik bu repo yapmiyor. SaaS onay geldigi anda, ayni HTTP isteginde
Instagram'a basiyor (olculen sure: ~11 saniye). Bu script'in isi sadece
"su post siradaki" demek.

Kullanim:
    python saas_gonder.py                  # siradaki adayi sec ve gonder
    python saas_gonder.py --slug dizi/my-bad
    python saas_gonder.py --kuru           # ne gonderilecegini goster, gonderme

Cikis kodlari: 0 gonderildi · 1 hata · 2 gonderilecek aday yok
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

from aday_sec import _dislanan_sluglar, _kategori_son_yayin, veri_topla
from furi_ortak import (
    durum_oku,
    durum_yaz,
    defter_oku,
    gerekli_ortam,
    gunluk_sayaci_tazele,
    ilk_commit_zamani,
    iso,
    json_bas,
    postlari_tara,
    raw_taban,
    repo_kok,
    simdi,
    utf8_cikti,
)
from datetime import timedelta

# Onay 7 gun gecerli (SaaS token omru). Biz daha kisa tutuyoruz: bu surede
# yanit gelmezse siradaki posta gecilir, kuyruk tek postta tikanmaz.
ONAY_PENCERESI_SAAT = 24


def _siradaki(kok) -> dict | None:
    """aday_sec ile ayni rotasyon: en uzun suredir yayinlanmamis kategori once."""
    durum, defter = durum_oku(kok), defter_oku(kok)
    dislanan = _dislanan_sluglar(durum, defter)
    adaylar = [p for p in postlari_tara(kok) if p["slug"] not in dislanan]
    if not adaylar:
        return None
    kategori_son = _kategori_son_yayin(defter)
    onbellek: dict[str, int] = {}

    def anahtar(p):
        if p["slug"] not in onbellek:
            onbellek[p["slug"]] = ilk_commit_zamani(kok, p["slug"])
        return (kategori_son.get(p["kategori"], 0.0), p["kategori"],
                onbellek[p["slug"]], p["ad"])

    return min(adaylar, key=anahtar)


def _gonder(ortam: dict, govde: dict) -> tuple[int, dict]:
    url = ortam["FURI_SAAS_URL"].rstrip("/") + "/api/posts"
    istek = urllib.request.Request(url, data=json.dumps(govde).encode("utf-8"),
                                   method="POST")
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


def main() -> int:
    utf8_cikti()
    a = argparse.ArgumentParser(description="Siradaki postu SaaS'a gonderir.")
    a.add_argument("--repo")
    a.add_argument("--slug", help="Belirli bir postu gonder (rotasyonu atla)")
    a.add_argument("--kuru", action="store_true", help="Gonderme, ne gidecegini bas")
    args = a.parse_args()

    kok = repo_kok(args.repo)
    ortam = gerekli_ortam(kok, "FURI_SAAS_URL", "FURI_API_KEY", "FURI_CLIENT_ID")

    if args.slug:
        hedef = args.slug.replace("\\", "/").strip("/")
        post = next((p for p in postlari_tara(kok) if p["slug"] == hedef), None)
        if not post:
            json_bas({"durum": "bulunamadi", "slug": hedef})
            return 1
    else:
        post = _siradaki(kok)
        if not post:
            json_bas({"durum": "aday_yok",
                      "mesaj": "Yayinlanmamis post kalmadi. insta-ingilizce ile uretilmeli."})
            return 2

    veri, sorunlar = veri_topla(kok, post, raw_taban(kok))
    if sorunlar:
        json_bas({"durum": "hata", "slug": veri["slug"], "sorunlar": sorunlar})
        return 1

    govde = {
        "clientId": ortam["FURI_CLIENT_ID"],
        "caption": veri["caption"],
        # SaaS duz string dizisi bekliyor; nesne sekli reddediliyor.
        "imageUrls": [g["url"] for g in veri["gorseller"]],
        # Asagidaki ikisi SaaS tarafinda yoksa yok sayilir, zarari olmaz.
        "altTexts": [g["alt_text"] for g in veri["gorseller"]],
        "externalRef": veri["slug"],
    }

    if args.kuru:
        json_bas({"durum": "kuru", "slug": veri["slug"], "slayt": veri["slayt"],
                  "caption_uzunluk": veri["caption_uzunluk"], "govde": govde})
        return 0

    kod, yanit = _gonder(ortam, govde)
    if kod != 201:
        json_bas({"durum": "hata", "slug": veri["slug"], "http": kod, "yanit": yanit,
                  "not": "Durum dosyalarina dokunulmadi."})
        return 1

    saas_post = yanit.get("post") or {}
    an = simdi()
    durum = gunluk_sayaci_tazele(durum_oku(kok))
    durum["bekleyen"] = {
        "slug": veri["slug"],
        "kategori": veri["kategori"],
        "slayt": veri["slayt"],
        "saas_post_id": saas_post.get("id"),
        "onay_url": yanit.get("approvalUrl"),
        "gonderim_zamani": iso(an),
        "son_gecerlilik": iso(an + timedelta(hours=ONAY_PENCERESI_SAAT)),
    }
    durum_yaz(kok, durum)

    json_bas({
        "durum": "gonderildi",
        "slug": veri["slug"],
        "kategori": veri["kategori"],
        "slayt": veri["slayt"],
        "saas_post_id": saas_post.get("id"),
        "onay_url": yanit.get("approvalUrl"),
        "not": "Onay maili SaaS tarafindan gonderildi. Onaylaninca yayin ~11 sn icinde olur.",
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
