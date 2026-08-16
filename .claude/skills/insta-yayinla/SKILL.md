---
name: insta-yayinla
description: Repodaki hazir postlari siraya koyup @furkanteacherteaching hesabina yayinlatir. Kategori rotasyonuyla siradaki postu secer ve content-approval-saas'a gonderir; onay maili oradan gider, kullanici telefondan onaylayinca yayin ~11 saniye icinde SaaS tarafindan yapilir. Bu skill yayin yapmaz, sadece siradakini secer ve defteri tutar. Zamanlanmis calisma icin tasarlandi; elle "/insta-yayinla" ile de calistirilabilir.
---

# insta-yayinla — siradaki postu siraya koy

Bu skill **iki sey yapmaz**: post uretmez (o `insta-ingilizce`'nin isi) ve
**Instagram'a yayin yapmaz** (onu SaaS yapar).

Yaptigi iki sey:

1. Kategori rotasyonuyla siradaki postu secip onaya gonderir
2. Yayin defterini Instagram ile esitler

Hedef tempo: **gunde 2 post**.

---

## Akis

```
  BU SKILL (cron, gunde 2 kez)
    aday sec  ->  POST /api/posts  ->  SaaS musteriye onay maili atar
                                              |
                                              v
                                    Sen: telefondan ONAYLA
                                              |
                          SaaS ayni istekte Instagram'a basar
                                    olculen sure: ~11 saniye
                                              |
  BU SKILL (sonraki calisma)                  v
    esitle.py  <----  Instagram'a bakip defteri gunceller
```

Onaydan sonra bu skill devreye **hic girmiyor**. Yayin bittiginde de haberi
olmuyor — bir sonraki calismasinda Instagram'a bakip ogreniyor.

### Neden yayin burada degil

Onay geldigi an yayini tetikleyecek bir yol yoktu: Claude cloud routine'i
webhook ile tetiklenemedi (dort yapilandirma denendi, hicbiri teslim edilmedi)
ve zamanlanmis rutinlerin minimum araligi 1 saat. Yayin cagrisini onayin
gerceklestigi yere tasiyinca tetikleme sorunu tamamen ortadan kalkti.

Ayrinti: `SAAS-ENTEGRASYON-PLANI.md`

---

## DEGISMEZ KURALLAR

1. **Bu skill Instagram'a yazmaz.** `ig_yayinla.py --slug` normal akista
   **cagrilmaz**. O komut artik yalnizca elle teshis/kurtarma icin duruyor.
2. **Ayni post iki kez siraya konmaz.** Defterde olan, `atlananlar`'da olan ve
   `bekleyen` olan sluglar aday havuzunun disinda.
3. **Calisma basina en fazla 1 oneri, takvim gunu basina en fazla 2 yayin.**
4. **Hata olursa state'e dokunma.** Hata mailini at, oldugun yerde dur.
5. **Sadece `otomasyon/*.json` commit edilir.** Gorseller, `caption.md`, skill
   dosyalari bu akista asla degistirilmez. `--force` push yok.
6. **`.env` asla commit edilmez.** Repo public. API anahtarini ve token'i
   hicbir yere (mail, log, commit mesaji) yazma.
7. **Kullaniciya sorma.** Gozetimsiz calisiyorsun. `AskUserQuestion` cagirma —
   karar veremedigin durumda mail at ve cik.

---

## Faz 0 — Ortam

```bash
git checkout main 2>/dev/null || git checkout -B main origin/main
git pull --ff-only origin main
```

> **Bulut calismasi `detached HEAD` ile baslar.** Bu halde ne `git pull` ne
> `git push` calisir — yani Faz 4'te state'i kaydedemezsin ve bir sonraki
> calisma eski durumu gorur. Bu iki satiri atlamadan calistir; `git status`
> ciktisinda `On branch main` gordugunden emin ol.

Gerekli ortam degiskenleri: `FURI_SAAS_URL`, `FURI_API_KEY`, `FURI_CLIENT_ID`
(oneri icin) ve `IG_ACCESS_TOKEN`, `IG_USER_ID` (esitleme icin). Eksikse
script'ler anlasilir hatayla durur — hata mailini at ve cik.

---

## Faz 1 — Defteri esitle

Her calisma buradan baslar. Instagram tek dogruluk kaynagidir.

```bash
python .claude/skills/insta-yayinla/scripts/esitle.py
```

Script iki kaynaga birden bakar ve gerekli state guncellemelerini kendi yapar.

**1. Bekleyen postun SaaS'taki durumu** (kesin bilgi — `bekleyen.onay_url`
uzerinden, token yeterli, oturum gerekmiyor):

| SaaS ne diyor | Ne olur |
|---|---|
| `publishStatus: published` | Deftere islenir, `bekleyen` kapanir, gunluk sayac artar |
| `published` ama Instagram'da yok | **Deftere islenmez** (silinmis, icerik havuza doner) ama `bekleyen` kapanir ve kota sayilir |
| `status: rejected` | `atlananlar`'a eklenir, `bekleyen` kapanir |
| `publishStatus: failed` | **`bekleyen` KORUNUR** — onay sayfasindan tekrar denenebilir. Hata mailini at. |
| `publishStatus: skipped` | Musteride Instagram bagli degil. `bekleyen` kapanir, post havuzda kalir, durumu mail ile bildir. |

**2. Instagram ile defter karsilastirmasi** (caption eslestirmesi):

| Durum | Ne olur |
|---|---|
| Instagram'da var, defterde yok | Deftere eklenir |
| Defterde var, Instagram'da yok | Defterden dusurulur, icerik tekrar aday olur |

`durum: esit` ve `bekleyen` alani yoksa yapacak is yok, Faz 2'ye gec.

> SaaS sorgusu once gelir cunku **caption eslestirmesi bir cikarim, SaaS cevabi
> kesin bilgi**. Ozellikle "yayinlandi ama sonra silindi" durumunu sadece SaaS
> bilebilir; Instagram'a bakmak o postu hic yayinlanmamis gibi gosterir ve
> `bekleyen` suresi dolana kadar asili kalir.

---

## Faz 2 — Siradakini siraya koy

Cikis sartlari — herhangi biri saglaniyorsa hicbir sey yapmadan Faz 4'e gec:

- `bugun.yayinlanan >= 2` (gunluk kota dolu)
- `son_yayin` uzerinden 4 saatten az gecmis (iki post ayni saate yigilmasin)
- `bekleyen` dolu **ve** `son_gecerlilik` gecmemis (onay bekliyor, karistirma)

**`bekleyen` dolu ve suresi gecmisse** — post cope atilmaz:

- `bekleyen` -> `null`
- `durum.json` > `sure_dolanlar` sozlugunde bu slug'in sayacini bir artir
- Sayac **3'e ulastiysa** -> `atlananlar`'a `sebep: "3 kez onay suresi doldu"`
  ile ekle. Ucuncu kez de bakilmadiysa artik gercekten istenmiyor demektir.
- Sayac 3'ten kucukse post havuzda kalir, sirasi gelince tekrar onerilir.

Sonra gonder:

```bash
python .claude/skills/insta-yayinla/scripts/saas_gonder.py
```

Script kategori rotasyonunu uygular, gorselleri ve caption'i dogrular, SaaS'a
post olusturur ve `durum.json > bekleyen` alanini kendisi yazar. **Onay mailini
SaaS gonderir** — bu skill mail yazmaz.

| Cikti `durum` | Ne yapilir |
|---|---|
| `gonderildi` | Faz 4'e gec |
| `aday_yok` | Stok bitmis. Faz 5, sonra Faz 4 |
| `hata` | State'e dokunulmadi. Hata mailini `yanit` alaniyla at, Faz 4, cik |

---

## Faz 3 — (yok)

Yayin adimi bu skill'den kaldirildi. SaaS onay istegi icinde yayinliyor.

---

## Faz 4 — Kapanis (her cikista, istisnasiz)

```bash
git add otomasyon/durum.json otomasyon/yayinlananlar.json
git commit -m "<yapilan is: esitlendi / siraya kondu / kota dolu>"
git push origin main
```

Degisiklik yoksa commit atma, sorun degil. Baska hicbir dosyayi `git add` etme.

Push basarisiz olursa bu ciddidir — bir sonraki calisma eski state'i gorur ve
ayni postu tekrar siraya koyabilir. Push hatasini **hata maili ile bildir**.

---

## Faz 5 — Stok kontrolu

`aday_sec.py --durum` ciktisinda `stok_dusuk: true` ve `durum.json` >
`son_stok_uyarisi` bugun degilse:

- subject: `[FURI-STOK] N post kaldi`
- govde: kalan sayi, kategori dagilimi, kac gun yeter (kalan / 2), yeni post
  uretilmesi gerektigi
- sonra `son_stok_uyarisi` = bugunun tarihi, Faz 4'te commit et

> Gmail arac adlari ortama gore degisir: yerelde `mcp__claude_ai_Gmail__*`,
> bulut rutininde `mcp__Gmail__*`. Arac adini varsayma; `ToolSearch` ile
> `gmail send_message` diye ara.

---

## Komut kunyesi

Tum komutlar repo kokunden calistirilir.

| Komut | Ne yapar | Disariya yazar mi |
|---|---|---|
| `esitle.py` | Defteri Instagram ile esitler | sadece yerel dosya |
| `esitle.py --kuru` | Farki raporlar, dosyaya dokunmaz | hayir |
| `saas_gonder.py` | Siradakini secip SaaS'a gonderir | **SaaS'a post olusturur** |
| `saas_gonder.py --kuru` | Ne gonderilecegini basar | hayir |
| `saas_gonder.py --slug K/S` | Belirli postu gonderir (rotasyonu atlar) | **evet** |
| `aday_sec.py --durum` | Havuz istatistigi, stok durumu | hayir |
| `aday_sec.py --dry-run` | Siradaki adayin okunakli ozeti | hayir |

**Elle teshis / kurtarma** (normal akista kullanilmaz):

| Komut | Ne zaman |
|---|---|
| `ig_yayinla.py --kontrol` | Instagram token'i saglam mi |
| `ig_yayinla.py --dogrula K/S` | Yarida kalmis bir yayin gercekten atilmis mi |
| `ig_yayinla.py --slug K/S` | SaaS calismiyorken elle yayin (son care) |
| `ig_token.py --kontrol` | Token kac gun gecerli |

---

## Aday secimi

**Kategori rotasyonu.** En uzun suredir yayinlanmamis kategori once gelir; o
kategori icinde repoya en once eklenmis post secilir. Boylece arka arkaya iki
phrasal ya da iki seviye testi cikmaz.

Bir post su durumlarda aday olmaz: yayin defterinde kayitli, `atlananlar`
icinde, `bekleyen` olarak duruyor, ya da dogrulamayi gecemiyor (10'dan fazla
slayt, 2200'den uzun caption, 30'dan fazla hashtag, erisilemeyen gorsel URL'i).

Gorseller `raw.githubusercontent.com` uzerinden servis edilir — Instagram public
URL istiyor, repo public oldugu icin ek barindirma gerekmiyor. **Bu yuzden bir
post push edilmeden siraya konamaz**; `saas_gonder.py` her URL'i HEAD ile
kontrol eder ve erisilemeyeni eler.

---

## Sorun giderme

**`aday_yok`** — yayinlanmamis post kalmadi. `insta-ingilizce` ile yeni post
uret, push et.

**SaaS 401** — `FURI_API_KEY` yanlis ya da sonunda satir sonu var. Deploy
sirasinda bir kez bu yasandi: `vercel env add`'e degeri pipe ile vermek sonuna
`\n` ekliyor.

**SaaS 403** — `FURI_CLIENT_ID` baska bir ajansa ait. IDOR korumasi calisiyor.

**`Gorsel URL'leri metin olmali`** — `imageUrls` duz string dizisi olmali,
nesne sekli reddediliyor.

**Onayladim ama post cikmadi** — SaaS tarafina bak: musterinin
`instagramUserId` alani dolu mu (bossa `publishStatus='skipped'` olur, sessizce
yayinlanmaz), `publishStatus` ne durumda. **Toplu onay (`/batch`) su an yayin
yapmiyor** — bilinen bosluk, tek tek onayla.

**Defter ile Instagram ayrismis** — `esitle.py` iki yonlu duzeltir. Silinen bir
post defterden dusurulup tekrar aday olur.

**Token suresi doluyor** — Instagram token'i 2026-10-15'te oluyor. SaaS
panelinde uyari yok; o tarihte sessizce durur. `ig_token.py --yenile` yeniler,
sonra yeni token SaaS'taki `Client.instagramAccessToken` alanina da yazilmali.

---

## Ilgili dosyalar

- `otomasyon/README.md` — durum dosyalarinin semasi, elle mudahale
- `SAAS-ENTEGRASYON-PLANI.md` — mimarinin neden boyle oldugu, SaaS tarafi
- `KURULUM.md` — Instagram token'i uretimi (tek seferlik)
- `WORKFLOW.md` — post uretim akisi (`insta-ingilizce` skill'i)

## Kunye

| Parca | Deger |
|---|---|
| Rutin | `trig_01TtprvNfdZd5DDEfR8uDCRj` ([panel](https://claude.ai/code/routines/trig_01TtprvNfdZd5DDEfR8uDCRj)) |
| Cron | `7 5,12 * * *` UTC = 08:07 / 15:07 Istanbul |
| SaaS | https://content-approval-saas.vercel.app |
| Instagram hesabi | `furkanteacherteaching` (`17841441566401393`) |
| Onay -> yayin | ~11 saniye (production'da olculdu) |
