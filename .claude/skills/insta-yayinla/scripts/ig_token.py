"""Instagram token'inin omrunu SaaS'a sorar. Bu repo token TUTMAZ, YENILEMEZ.

Token'in tek dogruluk kaynagi content-approval-saas'taki
`Client.instagramAccessToken` kaydidir. Yenilemeyi de SaaS yapiyor: gunluk cron
(`/api/cron/refresh-instagram-tokens`, 03:00) bitisine 20 gun kala token'i
otomatik uzatiyor.

Eskiden bu script token'i kendisi yeniler ve `.env` icindeki `IG_ACCESS_TOKEN`
satirini gunceller, son kullanma tarihini de `otomasyon/durum.json` icinde ayri
tutardi. Iki kopya arasinda senkron YOKTU: SaaS cron'u kendi kopyasini
yeniledigi gece Instagram eskisini gecersiz kiliyor ve buradaki kopya sessizce
bayatliyordu. O yuzden hem yenileme hem yerel tarih kaydi kaldirildi.

Kullanim:
    python ig_token.py --kontrol   # SaaS'a sor: kac gun kaldi?

Cikis kodlari: 0 sorun yok · 1 hata · 3 dikkat gerekiyor (token yakinda oluyor)
"""

from __future__ import annotations

import argparse
import sys

from furi_ortak import (
    SaasTokenHatasi,
    ig_kimlik,
    json_bas,
    kalan_gun,
    repo_kok,
    utf8_cikti,
)

UYARI_ESIGI_GUN = 10  # kalan gun bunun altindaysa uyar

# SaaS cron'u bitise bu kadar kala yeniliyor (kaynak: content-approval-saas
# src/lib/instagram-token.ts > IG_TOKEN_REFRESH_DAYS). Burada sadece raporlanir;
# esigi bu repo BELIRLEMEZ.
SAAS_YENILEME_PENCERESI_GUN = 20


def komut_kontrol(kok, args) -> int:
    try:
        kimlik = ig_kimlik(kok)
    except SaasTokenHatasi as hata:
        json_bas(hata.rapor())
        return 1

    kalan = kalan_gun(kimlik["gecerlilik_bitis"])
    yanit = {
        "durum": "ok",
        "kaynak": "saas",
        "client_id": kimlik["client_id"],
        "gecerlilik_bitis": kimlik["gecerlilik_bitis"],
        "kalan_gun": round(kalan, 1) if kalan is not None else None,
        "yenileyen": "SaaS cron (/api/cron/refresh-instagram-tokens, 03:00)",
    }

    if kimlik["suresi_doldu"]:
        # SaaS cron'u dolmus token'i UZATAMAZ (Instagram izin vermiyor); hesabin
        # panelden elle yeniden baglanmasi gerekir.
        yanit["durum"] = "suresi_doldu"
        yanit["not"] = (
            "Token'in suresi dolmus. Otomatik yenilenemez — SaaS panelinden "
            "musterinin Instagram hesabini yeniden bagla."
        )
    elif kalan is None:
        yanit["durum"] = "bilinmiyor"
        yanit["not"] = (
            "SaaS'ta son kullanma tarihi kayitli degil. Otomatik yenileme tarih "
            "bilinmeyen token'i ATLAR — SaaS panelinden baglantiyi tarihiyle "
            "birlikte yenile."
        )
    elif kalan <= UYARI_ESIGI_GUN:
        # Buraya dusuluyorsa SaaS cron'u calismiyor demektir: yenileme penceresi
        # 20 gun, uyari esigi 10 — normalde cron cok once yenilemis olmali.
        yanit["durum"] = "yakinda_doluyor"
        yanit["not"] = (
            f"Kalan sure {SAAS_YENILEME_PENCERESI_GUN} gunluk yenileme penceresinin "
            "epey icinde ama token hala uzamamis — SaaS cron'u calismiyor olabilir. "
            "Vercel cron loglarina bak."
        )
    elif kalan <= SAAS_YENILEME_PENCERESI_GUN:
        yanit["not"] = "Yenileme penceresinde; SaaS cron'u bu gece uzatacak."

    json_bas(yanit)
    return 3 if yanit["durum"] != "ok" else 0


def main() -> int:
    utf8_cikti()
    a = argparse.ArgumentParser(
        description="Instagram token omru (SaaS'a sorar; bu repo token tutmaz)."
    )
    a.add_argument("--repo", help="Repo kok dizini")
    a.add_argument("--kontrol", action="store_true", help="Kac gun kaldi?")
    args = a.parse_args()

    kok = repo_kok(args.repo)
    if not kok.is_dir():
        sys.stderr.write(f"HATA: repo bulunamadi: {kok}\n")
        return 1

    if args.kontrol:
        return komut_kontrol(kok, args)

    a.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
