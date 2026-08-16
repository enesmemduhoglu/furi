# Kurulum — tek seferlik

Otomatik yayinin calisabilmesi icin iki degere ihtiyac var: `IG_ACCESS_TOKEN` ve
`IG_USER_ID`. Bu rehber ikisini de ureterek `.env`'e yaziyor. Tahmini sure: **30-45 dakika**,
cogu Meta panelinde tiklama.

Bu adimlari **sen** yapiyorsun — Instagram ve Meta hesabina giris gerekiyor.

---

## 1. Instagram hesabini Professional yap

Instagram uygulamasi > `@furkanteacherteaching` > **Ayarlar** > **Hesap turu ve araclar**
> **Profesyonel hesaba gec** > **Creator** (veya **Business**).

Kisisel hesaplarda API ile yayin yapilamiyor; bu adim zorunlu.

---

## 2. Meta uygulamasi olustur

1. [developers.facebook.com/apps](https://developers.facebook.com/apps) > **Create app**
2. Uygulama turu: **Business**
   (Baska bir tur secersen Instagram urunu duzgun baglanmiyor, bastan yaratman gerekir.)
3. Isim: `furi-insta` gibi bir sey — kullaniciya gorunmuyor.

---

## 3. Instagram urununu ekle ve token uret

1. Uygulama panelinde sol menu: **Instagram** > **API setup with Instagram business login**
2. **Add account** ile `@furkanteacherteaching` hesabini bagla
3. Ayni ekranda hesabin yaninda **Generate token** > Instagram'a giris yap > izinleri onayla
4. Cikan token'i kopyala

Bu paneldeki token dogrudan **60 gunluk (long-lived)** gelir; ayrica bir takas adimi yok.
Token `IGAA...` veya `IGAG...` ile baslar ve 150-250 karakterdir.

> **Graph API Explorer'dan token alma.** `Tools > Graph API Explorer` ekranindaki
> "Generate Access Token" butonu `EAA...` ile baslayan, birkac saatlik ve Instagram
> izni olmayan bir token verir — bu akista ise yaramaz. Token'i mutlaka yukaridaki
> Instagram panelinden uret.

Gereken izinler otomatik veriliyor: `instagram_business_basic`,
`instagram_business_content_publish`.

> **App Review gerekmiyor.** Yayin yapilacak hesap senin ve uygulama development
> modunda. App Review sadece baskalarinin hesaplarina yayin yapan uygulamalar icin.

---

## 4. Token'i `.env`'e yaz

Repo kokundeki `.env` dosyasina ekle (dosya gitignored, repo public — asla commit edilmez):

```
IG_ACCESS_TOKEN=IGQVJ...buraya_yapistir
```

---

## 5. `IG_USER_ID`'yi bul

Token yeterli, baska bilgi gerekmiyor:

```powershell
cd "C:\Users\enesm\visual studio\furi1"
python .claude\skills\insta-yayinla\scripts\ig_yayinla.py --kimlik
```

Cikti:

```json
{
  "durum": "ok",
  "hesap": { "user_id": "178414...", "username": "furkanteacherteaching", ... },
  "not": "IG_USER_ID=178414... degerini .env'e ekle."
}
```

`user_id` degerini `.env`'e ekle:

```
IG_USER_ID=178414...
```

---

## 6. Token sayacini baslat

Token 60 gunde oluyor. Sayaci simdiden baslat ki skill ne zaman yenileyecegini bilsin:

```powershell
python .claude\skills\insta-yayinla\scripts\ig_token.py --kaydet
```

Bundan sonrasi otomatik: 50. gunden itibaren kendi yeniler, son 10 gunde uyari maili atar.

---

## 7. Kurulumu dogrula

```powershell
python .claude\skills\insta-yayinla\scripts\ig_yayinla.py --kontrol
```

Beklenen: `durum: ok`, dogru `username`, `account_type` = `BUSINESS` veya `CREATOR`,
ve `yayin_limiti` bilgisi.

```powershell
python .claude\skills\insta-yayinla\scripts\aday_sec.py --dry-run
```

Beklenen: bir aday, tum gorsel URL'leri `ok`, caption dogru ayristirilmis.

---

## 8. En-boy testi (canliya baglamadan once, 1 kez)

Gorseller 1920x2400. Meta dokumaninda azami genislik 1440 piksel yaziyor; Instagram
pratikte kendi kucultuyor ama **bunu varsaymak yerine olcmek gerekiyor.**

```powershell
python .claude\skills\insta-yayinla\scripts\ig_yayinla.py --isaretle dizi/my-bad
python .claude\skills\insta-yayinla\scripts\ig_yayinla.py --slug dizi/my-bad --tek-slayt
```

`--tek-slayt` sadece `1.jpg`'yi atar ve **yayin defterine yazmaz** — bu bir test postu.

Sonra Instagram'da gozle bak:

- **Duzgun gorunuyorsa** -> postu elle sil,
  `ig_yayinla.py --temizle-isaret` calistir, kuruluma devam.
- **Kirpilmis / metin kesilmisse** -> gorselleri 1080x1350'ye kucultup
  `otomasyon/pub/<kategori>/<slug>/` altina yazan bir adim eklemek gerekiyor
  (`pip install pillow`), sonra `.env`'e `IG_RAW_BASE` ile o klasoru gosterirsin.
  Bu durumda haber ver, adimi ekleyelim.
- **API hata dondurduyse** -> hata mesajini paylas.

---

## 9. Onay dongusunu ucdan uca dene

```
/insta-yayinla
```

1. Mail geldi mi, gorseller mailde gorunuyor mu?
2. **"HAYIR"** diye yanitla, `/insta-yayinla` tekrar calistir.
   Beklenen: post `atlananlar`'a dustu, yeni bir aday onerildi.
3. Bu sefer **"EVET"** diye yanitla, `/insta-yayinla` tekrar calistir.
   Beklenen: post gercekten yayinlandi, `otomasyon/yayinlananlar.json`'a permalink'i
   ile yazildi.
4. Hemen ardindan `/insta-yayinla` bir kez daha: ayni postu tekrar **atmamali**.

---

## 10. Zamanlayiciyi bagla

Hepsi calistiktan sonra:

```
/schedule
```

- cron: `13 6-21 * * *` (06:00-21:00 arasi saat basi; :00 yigilmasindan kacinmak icin
  13. dakika)
- komut: `/insta-yayinla`
- secret olarak tanimla: `IG_ACCESS_TOKEN`, `IG_USER_ID`

Saat basi tetiklemek sorun degil — gunluk kota (2) ve yayinlar arasi minimum sure
(4 saat) skill'in icinde.

**Bulutta Gmail'e erisilemiyorsa** zamanlayiciyi yerele al, skill'de degisiklik gerekmez:

```powershell
schtasks /create /tn "furi-insta" /tr "claude -p /insta-yayinla" /sc hourly
```

---

## Ortam degiskenleri kunyesi

| Degisken | Zorunlu | Varsayilan | Ne ise yarar |
|---|---|---|---|
| `IG_ACCESS_TOKEN` | evet | — | Long-lived Instagram token (60 gun) |
| `IG_USER_ID` | evet | — | Instagram professional hesap ID'si |
| `IG_API_HOST` | hayir | `graph.instagram.com` | Facebook Login yolu icin `graph.facebook.com` |
| `IG_API_VERSION` | hayir | `v23.0` | Graph API surumu |
| `IG_RAW_BASE` | hayir | git remote'tan turetilir | Gorsellerin public URL tabani |
| `FURI_REPO` | hayir | script konumundan turetilir | Repo kok dizini |

---

## Sik takilinan yerler

**"Generate token" butonu yok** — hesap Professional degil (adim 1) veya uygulama
Business turunde degil (adim 2).

**`--kimlik` "Invalid OAuth access token" diyor** — token kopyalanirken basina/sonuna
bosluk veya tirnak karismis olabilir. `.env`'de tirnak kullanma.

**`--kontrol` calisiyor ama `account_type` `PERSONAL`** — adim 1 tamamlanmamis.

**Token'i kaybettim** — panelden yeniden **Generate token**, `.env`'i guncelle,
`ig_token.py --kaydet` ile sayaci sifirla.
