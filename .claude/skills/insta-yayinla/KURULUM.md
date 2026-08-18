# Kurulum — tek seferlik

Iki ayri kurulum var:

- **A bolumu** (asagidaki 1-10 adim) — Instagram token'i. Token **yalnizca**
  SaaS'taki `Client` kaydinda durur; bu repo onun kopyasini TUTMAZ. Teshis
  komutlari (`ig_yayinla.py --kontrol/--dogrula`, `ig_token.py --kontrol`)
  token'i her calismada SaaS'tan ceker.

  > Neden: token 60 gunluk ve SaaS'ta gunluk bir cron bitisine 20 gun kala
  > otomatik yeniliyor. Yenileme aninda Instagram eskisini kisa sure sonra
  > gecersiz kiliyor. Burada ayri bir `IG_ACCESS_TOKEN` kopyasi tutulsaydi o
  > gece sessizce bayatlar ve otomasyon aciklamasiz kirilirdi.
- **B bolumu** (en altta) — bulut ortami. Zamanlanmis rutinin calismasi icin
  gereken sey; **bilgisayarin kapaliyken sistemin calismasini saglayan kisim budur.**

Bu adimlari **sen** yapiyorsun — Instagram, Meta ve claude.ai hesabina giris gerekiyor.

---

# A bolumu — Instagram token'i ve SaaS baglantisi

Adim 1-8 Instagram token'ini ve hesap kimligini uretir, adim 9 bunlari **SaaS'a**
kaydeder (tek dogruluk kaynagi orasi), adim 10 zamanlayiciyi kurar. Tahmini sure:
**30-45 dakika**, cogu Meta panelinde tiklama.

> Gmail'e "EVET" yazarak onaylama yolu **emekliye ayrildi**; onay artik SaaS'in
> onay linkinden veriliyor. Eski zincirin belgesi ve geri donus adimlari
> [`emekli/README.md`](emekli/README.md) altinda duruyor.

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

## 4. Token'i `.env`'e YAZMA

Token'in tek yeri SaaS'taki `Client` kaydidir (adim 9a). Bu repoda
`IG_ACCESS_TOKEN` diye bir degisken **yok** — ikinci bir kopya, SaaS'in gunluk
yenileme cron'undan sonra bayatlayan sessiz bir bozukluk demek.

Token'i adim 9a'ya kadar parola yoneticisinde tut; oraya yapistirdiktan sonra
yerelde hicbir yerde durmasin.

---

## 5. `IG_USER_ID`'yi elle bulmana gerek yok

SaaS token'i baglarken hesap kimligini Instagram'a kendisi soruyor ve
`Client.instagramUserId` alanini dolduruyor. Ayri bir adim gerekmez.

Adim 9a'dan **sonra** dogrulamak istersen:

```powershell
cd "C:\Users\enesm\visual studio\furi1"
python .claude\skills\insta-yayinla\scripts\ig_yayinla.py --kimlik
```

`durum: ok` bekleniyor. `uyusmazlik` cikarsa SaaS'taki hesap kimligi token'in
acildigi hesapla ayni degildir — panelden baglantiyi yenile.

---

## 6. Token sayaci — SaaS'ta, otomatik

Token 60 gunde doluyor ve **SaaS yeniliyor**: gunluk cron
(`/api/cron/refresh-instagram-tokens`, 03:00) bitisine 20 gun kala uzatiyor.
Bu repoda yenileme ya da sayac tutma yok.

Kalan sureyi gormek icin (adim 9a'dan sonra):

```powershell
python .claude\skills\insta-yayinla\scripts\ig_token.py --kontrol
```

---

## 7. Kurulumu dogrula

Adim 9a'dan **sonra** calistir — token'i SaaS'tan cektigi icin once oradaki
kaydin var olmasi gerekiyor:

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

## 8. En-boy testi — **yapildi, tekrarlanmasi gerekmiyor**

Gorseller 1920x2400. Meta dokumaninda azami genislik 1440 piksel yaziyor, yani
Instagram'in kirpip kirpmadigi varsayilmak yerine olculmustu:

> https://www.instagram.com/p/DcGQsbviHtT/ — 1920x2400 kaynak, Instagram
> 1440x1800'e kuculttu, **oran korundu, kirpma yok.**

Sonuc: ek gorsel isleme adimi gerekmiyor, 4:5 oranli gorseller oldugu gibi
gonderilebilir.

Bu olcumu yeni bir gorsel boyutu icin tekrarlaman gerekirse, elle yayin
komutlari duruyor (`ig_yayinla.py --isaretle` -> `--slug ... --tek-slayt`,
`--tek-slayt` deftere yazmaz). Ama normal kurulumda **bu adimi atla** — SaaS
yolunda gerekli degil ve gercek bir Instagram postu olusturur.

---

## 9. SaaS baglantisini kur ve dogrula

Onay ve yayin `content-approval-saas`'ta yapiliyor. Bu adim bir kez yapilir.

**9a. SaaS tarafinda musteri kaydi.** Panelde bir `Client` olustur (`Furkan
Teacher`, `eneshan034@gmail.com`) ve **Instagram'i bagla**: adim 3'teki 60
gunluk token'i yapistir. Hesap kimligini (`instagramUserId`) SaaS token'dan
turetir; son kullanma tarihini de girmen onemli — cron tarih bilinmeyen token'i
atlar.

> **Bu adim token'in tek durdugu yerdir.** Buradaki kayit hem SaaS'in yayin
> yolunu hem de bu reponun teshis komutlarini besler; ikinci bir kopya yok.

> `instagramUserId` bos kalirsa onay calisir ama **yayin yapilmaz**:
> `publishStatus = "skipped"` doner. Bu bilincli bir guvenli varsayilan,
> hata degil.

**9b. `.env`'i doldur.** `.env.example`'i kopyala, uc SaaS degiskenini yaz:

```
FURI_SAAS_URL=https://content-approval-saas.vercel.app
FURI_CLIENT_ID=<9a'da olusan Client kaydinin id'si>
FURI_API_KEY=<SaaS'in makine erisim anahtari>
```

`FURI_API_KEY`, SaaS tarafinda `FURI_API_KEY` + `FURI_API_AGENCY_ID` ortam
degiskenleriyle eslesir. Ikisi de Vercel'de tanimli olmali.

> Ayni ucu Instagram token'ini cekmek icin de kullaniliyor
> (`GET /api/clients/<id>/instagram-token`). Bu uc **yalnizca** API anahtariyla
> acilir ve anahtarin ajansindaki musterileri gorur — baska ajansin musteri
> id'si 404 doner.

**9c. Kuru calistirma** — hicbir yere yazmadan ne gidecegini gor:

```powershell
python .claude\skills\insta-yayinla\scripts\saas_gonder.py --kuru
```

Beklenen: `durum: kuru`, `govde.imageUrls` hepsi
`https://raw.githubusercontent.com/...`, `caption_uzunluk` 2000'in altinda.

**9d. Ucdan uca** — gercek bir post siraya konur:

```
/insta-yayinla
```

1. `saas_gonder.py` -> `durum: gonderildi`, `onay_url` dolu
2. Onay maili SaaS'tan geldi mi, gorseller mailde gorunuyor mu
3. Linke gir, **Onayla** — sayfa "Yayinlaniyor..." gosterip permalink dondurmeli
   (olculen sure ~11 saniye)
4. `/insta-yayinla` tekrar calistir: `esitle.py` postu deftere islemeli,
   `bekleyen` kapanmali
5. Bir kez daha calistir: **ayni postu tekrar siraya koymamali**

Reddi denemek istersen 3. adimda **Reddet**'e bas; `esitle.py` postu
`atlananlar`'a yazar ve bir sonraki calisma yeni aday onerir.

---

## 10. Zamanlayiciyi bagla

Hepsi calistiktan sonra:

```
/schedule
```

- cron: `7 9 * * *` UTC = 12:07 Istanbul (gunde 1 post temposu)
- komut: `/insta-yayinla`
- ortam degiskenleri: `FURI_SAAS_URL`, `FURI_CLIENT_ID`, `FURI_API_KEY`

> **Instagram token'i hicbir ortama konmaz** — ne yerelde ne bulutta. Token
> SaaS'ta duruyor ve gerektiginde `FURI_API_KEY` ile oradan cekiliyor.
> Ayrinti: B bolumu, adim 1.

Ayrintili bulut kurulumu (ag izinleri dahil) icin **B bolumu**.

Yerel zamanlayici da calisir, skill'de degisiklik gerekmez:

```powershell
schtasks /create /tn "furi-insta" /tr "claude -p /insta-yayinla" /sc hourly
```

Saat basi tetiklemek sorun degil — gunluk kota (gunde 1 gonderim) skill'in
icinde. Yani saat basi tetiklense bile gunde en fazla 1 post siraya konur.

---

## Ortam degiskenleri kunyesi

Bos sablon: repo kokundeki [`.env.example`](../../../.env.example) — kopyala,
`.env` adiyla kaydet, doldur. `.env` gitignored; repo public, asla commit etme.

| Degisken | Nerede | Ne ise yarar |
|---|---|---|
| `FURI_SAAS_URL` | yerel `.env` + **bulut ortami** | SaaS adresi |
| `FURI_CLIENT_ID` | yerel `.env` + **bulut ortami** | Hangi musteri |
| `FURI_API_KEY` | yerel `.env` + **bulut ortami** | SaaS'a post olusturma + token cekme yetkisi |

Instagram token'i ve hesap kimligi **ortam degiskeni degil**: ikisi de SaaS'taki
`Client` kaydinda durur (`instagramAccessToken`, `instagramUserId`) ve script'ler
`GET /api/clients/<FURI_CLIENT_ID>/instagram-token` ile ceker. `IG_ACCESS_TOKEN`
/ `IG_USER_ID` degiskenleri **kaldirildi**; `.env`'inde duruyorsa sil — artik
hicbir yerde okunmuyor, ama duran bir sir gereksiz risk.

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

**`--kimlik` "Invalid OAuth access token" diyor** — SaaS'taki token gecersiz.
Kopyalanirken basina/sonuna bosluk karismis ya da suresi dolmus olabilir; SaaS
panelinden baglantiyi yenile.

**`--kontrol` calisiyor ama `account_type` `PERSONAL`** — adim 1 tamamlanmamis.

**`kaynak: saas_token` hatasi aliyorum** — token SaaS'tan cekilemiyor. `kod`
alanina bak: `client_not_found` -> `FURI_CLIENT_ID` yanlis · `instagram_not_connected`
-> panelde Instagram bagli degil · `baglanti` -> SaaS'a ulasilamiyor (bulutta
`content-approval-saas.vercel.app` ag izin listesinde mi?) · HTTP 401 ->
`FURI_API_KEY` yanlis.

**Token'i kaybettim / suresi doldu** — Meta panelinden yeniden **Generate token**
ve **yalnizca** SaaS panelinden musterinin Instagram baglantisini yenile. Bu
repoda guncellenecek bir kopya yok.

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

**Instagram token'i buraya KONMAZ** — zaten hicbir ortama konmuyor. Dialogun
altinda su uyari yaziyor:

> "These are visible to anyone using this environment — don't add secrets or credentials."

Bulut ortamlarinda secrets store yok. Instagram token'i hesaba dogrudan post
atabildigi icin ortama hic girmez; onun yerine `FURI_API_KEY` ile SaaS'tan
cekilir. `FURI_API_KEY` dar kapsamli: yalnizca kendi ajansinin musterilerini
gorur, baska ajansa dokunamaz.

`FURI_API_KEY` de bir sirdir ve bu uyari onun icin de gecerli — ama ele
gecirilirse kaybedilen sey Instagram token'inin kendisi degil, tek bir ajansin
SaaS erisimidir ve SaaS tarafindan tek degisken degistirilerek iptal edilir.

Bulutta SaaS'a ulasilamazsa `esitle.py` Instagram karsilastirmasini atlar ve
defteri oldugu gibi birakir; raporda `instagram: ... atlandi` satiri neden
atlandigini yazar. Bekleyen postun akibetini zaten SaaS'in public onay
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
| `IG_ACCESS_TOKEN: NOT SET` | Dogru — token hicbir ortamda tutulmuyor |
| `esitle.py` -> `durum: esit` | Faz 1 calisti (token SaaS'tan cekildi) |
| `esitle.py` -> `instagram: ... atlandi` | SaaS'a ulasilamamis; mesajdaki sebebe bak |
| `saas_gonder.py` -> `durum: gonderildi` | Ag kapisi acik, SaaS'a ulasildi |
| `otomasyon/durum.json` commit + push | State kalici |

> Degisiklikler **sonraki** oturumlardan itibaren gecerli; calisan oturumlar
> yapilandirmayi yeniden okumaz.
