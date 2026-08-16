# Kurulum — tek seferlik

Iki ayri kurulum var:

- **A bolumu** (asagidaki 1-10 adim) — Instagram token'i. Yayini artik SaaS yaptigi
  icin bu token **SaaS'taki `Client` kaydinda** durur; yereldeki `.env` kopyasi
  yalnizca elle teshis komutlari (`ig_yayinla.py --kontrol/--dogrula`) icindir.
- **B bolumu** (en altta) — bulut ortami. Zamanlanmis rutinin calismasi icin
  gereken sey; **bilgisayarin kapaliyken sistemin calismasini saglayan kisim budur.**

Bu adimlari **sen** yapiyorsun — Instagram, Meta ve claude.ai hesabina giris gerekiyor.

---

# A bolumu — Instagram token'i

Bu bolum `IG_ACCESS_TOKEN` ve `IG_USER_ID` uretir. Tahmini sure: **30-45 dakika**,
cogu Meta panelinde tiklama.

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

| Degisken | Nerede | Ne ise yarar |
|---|---|---|
| `FURI_SAAS_URL` | yerel `.env` + **bulut ortami** | SaaS adresi |
| `FURI_CLIENT_ID` | yerel `.env` + **bulut ortami** | Hangi musteri |
| `FURI_API_KEY` | yerel `.env` + **bulut ortami** | SaaS'a post olusturma yetkisi |
| `IG_ACCESS_TOKEN` | yerel `.env` + **SaaS `Client` kaydi** — buluta KONMAZ | Instagram token'i (60 gun) |
| `IG_USER_ID` | yerel `.env` + **SaaS `Client` kaydi** | Instagram hesap ID'si |

Opsiyonel override'lar (hepsi yalnizca yerel):

| Degisken | Zorunlu | Varsayilan | Ne ise yarar |
|---|---|---|---|
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
`ig_token.py --kaydet` ile sayaci sifirla. **SaaS'taki `Client.instagramAccessToken`
alanini da guncelle** — token iki yerde duruyor, yayini yapan taraf SaaS.

---

# B bolumu — bulut ortami

Zamanlanmis rutin Anthropic'in bulutunda calisiyor. Bilgisayarin kapaliyken
sistemin islemesi buna bagli. Bu bolum bir kez yapilir; ortam bozulur ya da
yeniden kurulursa buraya don.

## Ortam dialogunu bulmak

**Ayarlar menusunde degil.** Dokumandan birebir:

> "claude.ai/code'da, **mesaj kutusunun ustundeki satirda** bulunan, mevcut
> ortamin adini gosteren bulut ikonunu sec. Bunun icin bir ayarlar sayfasi
> veya dogrudan URL yok."

Sonra ortamin uzerine gel > sagda beliren **disli** ikonu > dialog acilir.

> **Mevcut ortami duzenle, yenisini yaratma.** Rutin bir ortam kimligine bagli
> (`env_01TN9TTQAZn4w7Ye1isHAFCd`). **Add cloud environment** ile yeni bir ortam
> yaratirsan yeni bir kimlik olusur, rutin hala eskisine bakar ve ayarlarin hicbir
> ise yaramaz. Dialog basliginda **Update** yazdigindan emin ol.

## 1. Environment variables

`.env` formatinda, satir basina bir tane:

```
FURI_SAAS_URL=https://content-approval-saas.vercel.app
FURI_CLIENT_ID=<SaaS'taki Client kaydinin id'si>
FURI_API_KEY=<SaaS'in makine erisim anahtari>
```

**Instagram token'i buraya KONMAZ.** Dialogun altinda su uyari yaziyor:

> "These are visible to anyone using this environment — don't add secrets or credentials."

Bulut ortamlarinda secrets store yok. `IG_ACCESS_TOKEN` hesaba dogrudan post
atabildigi icin disarida birakilir; `FURI_API_KEY` ise dar kapsamli (sadece kendi
SaaS'inda post olusturur, yayin yapamaz, Instagram'a dokunamaz).

Token'siz bulut oturumunda `esitle.py` Instagram karsilastirmasini atlar ve defteri
oldugu gibi birakir — bekleyen postun akibetini zaten SaaS'in public onay
endpoint'inden ogreniyor.

## 2. Network access

Varsayilan **Trusted** yetmez: sadece paket depolari ve GitHub gibi bir izin
listesine cikisa izin verir, Vercel o listede yoktur. Belirtisi:

```
Tunnel connection failed: 403 Forbidden
gateway answered 403 to CONNECT
```

**Custom** sec, **Allowed domains** kutusuna:

```
content-approval-saas.vercel.app
```

**"Also include default list of common package managers"** kutusunu **isaretli birak** —
yoksa GitHub erisimi de kesilir ve `git pull` bozulur.

`Full` de calisir ama gereksiz genis: rutin gozetimsiz calisiyor, tek ihtiyaci olan
host'a izin vermek yeterli.

## 3. Setup script

**Bos birak.** Kutudaki `#!/bin/bash npm install` gri placeholder metindir, gercek
icerik degil. Bu bir Python reposu; ek kurulum gerekmiyor, script'ler yalnizca
standart kutuphane kullaniyor.

## Dogrulama

Rutini elle tetikle ve calisma logunda sunlari ara:

| Beklenen | Anlami |
|---|---|
| `FURI_SAAS_URL/CLIENT_ID/API_KEY: set` | Degiskenler ulasti |
| `IG_ACCESS_TOKEN: NOT SET` | Dogru — token bilerek disarida |
| `esitle.py` -> `durum: esit` + `instagram: ... atlandi` | Faz 1 token'siz calisti |
| `saas_gonder.py` -> `durum: gonderildi` | Ag kapisi acik, SaaS'a ulasildi |
| `otomasyon/durum.json` commit + push | State kalici |

> Degisiklikler **sonraki** oturumlardan itibaren gecerli; calisan oturumlar
> yapilandirmayi yeniden okumaz.
