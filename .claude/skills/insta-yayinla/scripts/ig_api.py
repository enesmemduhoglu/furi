"""Instagram Graph API icin ince bir katman. Sadece stdlib.

Host ve surum ortamdan override edilebilir:
    IG_API_HOST     varsayilan graph.instagram.com   (Instagram Login yolu)
    IG_API_VERSION  varsayilan v23.0
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

VARSAYILAN_HOST = "graph.instagram.com"
VARSAYILAN_SURUM = "v23.0"


class IGHatasi(Exception):
    """Meta'nin dondugu hata. `.ayrinti` ham JSON'u tasir."""

    def __init__(self, mesaj: str, ayrinti: dict | None = None, http: int | None = None):
        super().__init__(mesaj)
        self.ayrinti = ayrinti or {}
        self.http = http

    def rapor(self) -> str:
        satirlar = [str(self)]
        hata = self.ayrinti.get("error") if isinstance(self.ayrinti, dict) else None
        if isinstance(hata, dict):
            for alan in ("type", "code", "error_subcode", "error_user_title", "error_user_msg", "fbtrace_id"):
                if hata.get(alan):
                    satirlar.append(f"  {alan}: {hata[alan]}")
        return "\n".join(satirlar)


def _taban() -> str:
    host = os.environ.get("IG_API_HOST") or VARSAYILAN_HOST
    surum = os.environ.get("IG_API_VERSION") or VARSAYILAN_SURUM
    return f"https://{host}/{surum}"


def _cagir(yol: str, veri: dict | None, token: str, metot: str) -> dict:
    parametreler = {k: v for k, v in (veri or {}).items() if v not in (None, "")}
    parametreler["access_token"] = token

    if metot == "GET":
        url = f"{_taban()}/{yol.lstrip('/')}?{urllib.parse.urlencode(parametreler)}"
        istek = urllib.request.Request(url, method="GET")
    else:
        url = f"{_taban()}/{yol.lstrip('/')}"
        govde = urllib.parse.urlencode(parametreler).encode("utf-8")
        istek = urllib.request.Request(url, data=govde, method="POST")
        istek.add_header("Content-Type", "application/x-www-form-urlencoded")

    istek.add_header("User-Agent", "furi-insta-yayinla/1.0")

    try:
        with urllib.request.urlopen(istek, timeout=60) as yanit:
            ham = yanit.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as hata:
        ham = hata.read().decode("utf-8", errors="replace")
        try:
            ayrinti = json.loads(ham)
        except json.JSONDecodeError:
            ayrinti = {"ham_yanit": ham}
        mesaj = ""
        if isinstance(ayrinti.get("error"), dict):
            mesaj = ayrinti["error"].get("message", "")
        raise IGHatasi(
            mesaj or f"Instagram API HTTP {hata.code} dondu ({metot} {yol})",
            ayrinti,
            hata.code,
        ) from None
    except (urllib.error.URLError, TimeoutError, OSError) as hata:
        raise IGHatasi(f"Instagram API'ye ulasilamadi ({metot} {yol}): {hata}") from None

    try:
        return json.loads(ham)
    except json.JSONDecodeError:
        raise IGHatasi(f"Instagram API gecersiz JSON dondu ({metot} {yol}): {ham[:200]}") from None


def post(yol: str, veri: dict, token: str) -> dict:
    return _cagir(yol, veri, token, "POST")


def get(yol: str, veri: dict, token: str) -> dict:
    return _cagir(yol, veri, token, "GET")


# ------------------------------------------------------------------- islemler


def container_olustur(ig_id: str, token: str, **alanlar) -> str:
    """POST /{ig-user-id}/media -> container id"""
    yanit = post(f"{ig_id}/media", alanlar, token)
    if not yanit.get("id"):
        raise IGHatasi("Container olusturuldu ama yanitta 'id' yok", yanit)
    return str(yanit["id"])


def container_bekle(container_id: str, token: str, azami_saniye: int = 90) -> None:
    """Instagram gorseli cekene kadar bekle. FINISHED degilse yayina gecilmez."""
    bitis = time.monotonic() + azami_saniye
    son = "UNKNOWN"
    bekleme = 2.0
    while time.monotonic() < bitis:
        yanit = get(container_id, {"fields": "status_code,status"}, token)
        son = yanit.get("status_code", "UNKNOWN")
        if son == "FINISHED":
            return
        if son in ("ERROR", "EXPIRED"):
            raise IGHatasi(
                f"Container {container_id} durumu {son}: {yanit.get('status', '')}", yanit
            )
        time.sleep(bekleme)
        bekleme = min(bekleme * 1.5, 10.0)
    raise IGHatasi(
        f"Container {container_id} {azami_saniye} saniyede hazir olmadi (son durum: {son})"
    )


def yayinla(ig_id: str, container_id: str, token: str) -> str:
    """POST /{ig-user-id}/media_publish -> media id"""
    yanit = post(f"{ig_id}/media_publish", {"creation_id": container_id}, token)
    if not yanit.get("id"):
        raise IGHatasi("Yayin cagrisi yanitinda 'id' yok", yanit)
    return str(yanit["id"])


def medya_bilgisi(media_id: str, token: str) -> dict:
    return get(media_id, {"fields": "id,permalink,timestamp,media_type,caption"}, token)


def son_medyalar(ig_id: str, token: str, adet: int = 10) -> list[dict]:
    yanit = get(
        f"{ig_id}/media",
        {"fields": "id,permalink,timestamp,media_type,caption", "limit": str(adet)},
        token,
    )
    return yanit.get("data", []) or []


def yayin_limiti(ig_id: str, token: str) -> dict:
    yanit = get(f"{ig_id}/content_publishing_limit", {"fields": "config,quota_usage"}, token)
    veri = yanit.get("data") or [{}]
    return veri[0] if veri else {}


def hesap_bilgisi(ig_id: str, token: str) -> dict:
    return get(ig_id, {"fields": "user_id,username,account_type,media_count"}, token)


def kimlik(token: str) -> dict:
    """GET /me — kurulumda IG_USER_ID'yi bulmak icin (token disinda bilgi gerekmez)."""
    return get("me", {"fields": "user_id,username,account_type,media_count"}, token)
