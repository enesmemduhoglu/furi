---
name: insta-yayinla
description: Repodaki hazir postlari siraya koyup @furkanteacherteaching hesabina yayinlatir. Havuzdaki en yuksek puanli postu secer ve content-approval-saas'a gonderir; onay maili oradan gider, kullanici telefondan onaylayinca yayin ~11 saniye icinde SaaS tarafindan yapilir. Bu skill yayin yapmaz, sadece siradakini secer ve defteri tutar. Zamanlanmis calisma icin tasarlandi; elle "/insta-yayinla" ile de calistirilabilir.
---

# insta-yayinla — siradaki postu siraya koy

Bu skill **iki sey yapmaz**: post uretmez (o `insta-ingilizce`'nin isi) ve
**Instagram'a yayin yapmaz** (onu SaaS yapar).

Yaptigi iki sey:

1. En yuksek puanli postu secip onaya gonderir
2. Yayin defterini Instagram ile esitler

Hedef tempo: **gunde 1 post** (oglen).

---

## Akis

```
  BU SKILL (cron, gunde 1 kez)
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
3. **Calisma basina en fazla 1 oneri, takvim gunu basina en fazla 1 gonderim.**
   Kota siraya konani sayar (`bugun.siraya_konan`), yayinlanani degil.
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

### Ortam degiskenleri

| Degisken | Bulutta gerekli mi | Ne icin |
|---|---|---|
| `FURI_SAAS_URL` | **evet** | SaaS adresi (sir degil) |
| `FURI_CLIENT_ID` | **evet** | Hangi musteri (opak id) |
| `FURI_API_KEY` | **evet** | SaaS'a post olusturma + Instagram token'ini cekme yetkisi |

**Instagram token'i hicbir ortama konmaz** — ne yerelde ne bulutta. Tek
dogruluk kaynagi SaaS'taki `Client` kaydidir; script'ler gerektiginde
`GET /api/clients/<FURI_CLIENT_ID>/instagram-token` ile ceker
(`furi_ortak.ig_kimlik`).

> Neden ikinci kopya yok: token 60 gunluk ve SaaS'ta gunluk bir cron bitisine
> 20 gun kala otomatik yeniliyor. Yenileme aninda Instagram eskisini kisa sure
> sonra gecersiz kiliyor — ayri bir `IG_ACCESS_TOKEN` kopyasi o gece sessizce
> bayatlar ve otomasyon aciklamasiz kirilirdi.

`FURI_API_KEY` dar kapsamli: yalnizca kendi ajansinin musterilerini gorur,
baska ajansa dokunamaz ve ele gecerse SaaS'ta tek degisken degistirilerek
iptal edilir.

Instagram'a bakilamayan bir oturumda — token cekilemedi ya da cagri basarisiz
oldu, fark etmez — `esitle.py` karsilastirmayi atlar ve **defteri oldugu gibi
birakir** (raporda `instagram: ... atlandi` + sebep). Bekleyen postun akibetini
zaten SaaS'in public onay endpoint'inden kesin olarak ogreniyor; o cagri
Instagram'a hic dokunmuyor.

> **`esitle.py` hata verip Faz 2'yi dusurmez.** Bir kez dusurdu: bulut
> oturumunun cikis proxy'si `graph.instagram.com`'a CONNECT'i 403 ile kesince
> Faz 1 hata koduyla cikti, o gunun 15:07 yuvasina post konmadi. Emniyet aginin
> kopmasi akisi durdurmamali; script artik atlayip devam ediyor.

**Bulutta Instagram karsilastirmasi calismiyor** (proxy `graph.instagram.com`'a
izin vermiyor). Yani zamanlanmis calismalarda "defterde var, Instagram'da yok"
tespiti yapilmiyor: elle silinen bir post kendiliginden havuza donmez. Silme
yaptiysan `atlananlar`'a elle eklemek ya da yerelde bir kez `esitle.py`
calistirmak gerekir.

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
| `publishStatus: published` | Deftere islenir, `bekleyen` kapanir, yayin BUGUNSE `bugun.yayinlanan` artar (bilgi sayaci) |
| `published` ama Instagram'da yok | **Deftere islenmez** (silinmis, icerik havuza doner) ama `bekleyen` kapanir |
| `status: rejected` | `atlananlar`'a eklenir, `bekleyen` kapanir |
| `publishStatus: failed` | **`bekleyen` KORUNUR** — onay sayfasindan tekrar denenebilir. Hata mailini at. |
| `publishStatus: skipped` | Musteride Instagram bagli degil. `bekleyen` kapanir, post havuzda kalir, durumu mail ile bildir. |

**2. Instagram ile defter karsilastirmasi** (caption eslestirmesi):

| Durum | Ne olur |
|---|---|
| Instagram'da var, defterde yok | Deftere eklenir |
| Defterde var, Instagram'da yok | Defterden dusurulur, icerik tekrar aday olur |

`durum: esit` ve `bekleyen` alani yoksa yapacak is yok, Faz 2'ye gec.

> **Yayin saati SaaS'in `publishedAt` alanindan gelir, esitlemenin kostugu
> andan degil.** Eslesme cogu zaman ertesi gunun cron'unda kuruldugu icin
> "simdi" yazmak her kaydi bir gun ileri kaydiriyordu ve defter "bugun iki post
> cikti" diye okunuyordu. Alan bos donerse (eski bir SaaS surumu) tespit ani
> yazilir; o zaman kayitta `zaman_kaynagi: "tespit"` ve kaydin `not` alaninda
> uyari cikar — raporlarken buna bak.

> SaaS sorgusu once gelir cunku **caption eslestirmesi bir cikarim, SaaS cevabi
> kesin bilgi**. Ozellikle "yayinlandi ama sonra silindi" durumunu sadece SaaS
> bilebilir; Instagram'a bakmak o postu hic yayinlanmamis gibi gosterir ve
> `bekleyen` suresi dolana kadar asili kalir.

---

## Faz 2 — Siradakini siraya koy

Cikis sartlari — herhangi biri saglaniyorsa hicbir sey yapmadan Faz 4'e gec:

- `bugun.siraya_konan >= 1` (gunluk kota dolu)
- `son_gonderim` ayni takvim gununde (gunde tek gonderim)
- `bekleyen` dolu **ve** `son_gecerlilik` gecmemis (onay bekliyor, karistirma)

> **Her iki kural da YAYIN'a degil GONDERIM'e bakar.** `son_yayin` ve
> `bugun.yayinlanan` sadece bilgi amaclidir, siraya koymayi engellemez.
> Sebebi: yayin ani senin onay verdigin an — repo onu ne belirliyor ne de
> zamaninda goruyor, sadece bir sonraki calismada Faz 1'de fark ediyor. Yayina
> bakan kural bu yuzden kendi kendini bloke ediyordu: Faz 1 "yayinlandi" deyip
> `son_yayin`'i gunceliyor, ayni calismanin Faz 2'si de "daha yeni yayin
> oldu" deyip cikiyordu. **Dun onaylanip bugun sabah yayinlanmis bir post,
> bugun oglen calismasini durdurmaz.**

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

Script siradaki adayi secer, gorselleri ve caption'i dogrular, SaaS'a
post olusturur ve `durum.json > bekleyen` alanini kendisi yazar. **Onay mailini
SaaS gonderir** — bu skill mail yazmaz.

| Cikti `durum` | Ne yapilir |
|---|---|
| `gonderildi` | Faz 4'e gec — ama once `mail_gitti` alanina bak |
| `aday_yok` | Stok gercekten bitmis. Faz 5, sonra Faz 4 |
| `uygun_aday_yok` | Post var ama hicbiri dogrulamayi gecemedi. **Stok sorunu degil, hata.** `elenenler` listesini hata mailine koy, Faz 4, cik |
| `hata` | State'e dokunulmadi. Hata mailini `yanit` alaniyla at, Faz 4, cik |

> `gonderildi` ciktisinda **`elenenler` alani varsa** onu da hata mailine ekle:
> gonderim basarili olsa bile o postlar bozuk ve duzeltilmezse havuz sessizce
> erir.

**`mail_gitti: false` ise post siraya kondu ama musteriye haber GITMEDI.** State
dogru, geri alma yok — ama onay istegi kimseye ulasmadi, yani post kendiliginden
yayinlanmaz. `[FURI-HATA] onay maili gonderilemedi` konulu maili `mail_hatasi`
sebebi ve `onay_url` ile birlikte at, sonra Faz 4'e gec.

> Bu alan yoksa (eski SaaS surumu) sessiz kalinir. 16-17.08'de bu geri bildirim
> hic yoktu: SaaS 201 donuyordu, otomasyon "haber gitti" varsayiyordu, mail ise
> gitmiyordu — iki gun boyunca kimse fark etmedi.

`uygun_aday_yok` en cok "dal push edilmemis" durumunda cikar — gorseller
`raw.githubusercontent.com` uzerinden servis edildigi icin push edilmemis bir
postun URL'leri 404 verir ve tum adaylar elenir. `elenenler` icinde toplu
`HTTP 404` goruyorsan once Faz 0'daki `git pull`/dal durumunu kontrol et.

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
- govde: kalan sayi, kategori dagilimi, kac gun yeter (kalan / 1), yeni post
  uretilmesi gerektigi
- sonra `son_stok_uyarisi` = bugunun tarihi, Faz 4'te commit et

> Gmail arac adlari ortama gore degisir: yerelde `mcp__claude_ai_Gmail__*`,
> bulut rutininde `mcp__Gmail__*`. Arac adini varsayma; `ToolSearch` ile
> `gmail send_message` diye ara.

> **Gmail bu skill'de yalnizca uyari kanali.** Onay maili SaaS'tan gidiyor ve
> onay SaaS'ta veriliyor; Gmail'e "EVET" yazarak onaylama yolu emekliye
> ayrildi (`emekli/README.md`). Buradan cikan tek sey stok ve hata bildirimi —
> yani Gmail'e ulasilamamasi yayin akisini durdurmaz, sadece sessizlestirir.

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
| `aday_sec.py --durum` | Havuz istatistigi, stok ve puan dagilimi | hayir |
| `puanla.py` | Puansiz / bayat postlari listeler | hayir |
| `puanla.py --yaz K/S` | Post puani yazar (JSON stdin'den) | hayir |
| `aday_sec.py --dry-run` | Siradaki adayin okunakli ozeti | hayir |

**Elle teshis / kurtarma** (normal akista kullanilmaz):

| Komut | Ne zaman |
|---|---|
| `ig_yayinla.py --kontrol` | Instagram token'i saglam mi |
| `ig_yayinla.py --kimlik` | SaaS'taki hesap kimligi token'inkiyle ayni mi |
| `ig_yayinla.py --dogrula K/S` | Yarida kalmis bir yayin gercekten atilmis mi |
| `ig_yayinla.py --slug K/S` | SaaS calismiyorken elle yayin (son care) |
| `ig_token.py --kontrol` | SaaS'taki token kac gun gecerli |

> Hepsi token'i SaaS'tan cekiyor: **SaaS erisilemezken calismazlar** ve
> `kaynak: saas_token` hatasi verirler. Sessizce bayat bir token'la calisip
> yanlis sonuc uretmelerindense durmalari yeglenir.

---

## Aday secimi

**En yuksek puandan asagiya.** Havuzun tamami puana gore siralanir ve tepeden
baslanir. Kategori **birincil olcut degil**, yalnizca esit puanlilar arasinda
konusur: ayni puanda iki post varsa uzun suredir gorunmeyen kategoriden olani
secilir.

> **Takas:** feed'de arka arkaya ayni turden iki post cikabilir. Onceki kural
> (kategori rotasyonu once) cesitliligi garantiliyordu ama iyi bir postu
> sirasi gelmedigi icin bekletiyordu. 2026-08-18 karari: yayin sirasi
> kaliteyi izler, cesitliligi degil.

Puan postun **kalitesini** olcer (ilgi cekiyor mu, ogretiyor mu, ayrisiyor
mu). Gorseldeki harf hatalari ve sablon sapmalari puana **girmez** —
onlarin defteri `HATA-RAPORU.md`.

`durum.json > sonraki` doluysa **once o slug denenir** — gunun postu elle
secildiginde (havuzdaki postlar gunu gunune yerel basima cevriliyor, cevrilen
post ertesi gun yayina girmeli) puan sirasi bir kereligine ezilir. Sabit
gonderimden sonra kendini temizler.

Puan **elemez** ama sirayi tamamen belirler: puani olmayan ya da olcut surumu
eskimis post havuzun **tamaminin** sonuna duser, yani puanli tek bir aday
kaldigi surece secilmez. Uretim akisi her postu puanladigi icin bu gecici
olmali; `puanla.py` puansiz kalanlari listeler. Bozuk bir `puan.json` secimi
durdurmaz.

Havuzun puan dagilimini ve yaklasik yayin planini `aday_sec.py --durum`
ciktisindaki `puan_dagilimi` ve `yayin_sirasi` alanlari gosterir; sema
`puanla.py --sema`, karar gecmisi `TODOS.md` icinde.

Bir post su durumlarda aday olmaz: yayin defterinde kayitli, `atlananlar`
icinde, `bekleyen` olarak duruyor, ya da dogrulamayi gecemiyor (10'dan fazla
slayt, 30'dan fazla hashtag, erisilemeyen gorsel URL'i, cok uzun caption).

**Caption limiti iki tane.** Instagram 2200 karaktere izin veriyor ama yayin
SaaS uzerinden gittigi icin baglayici olan **SaaS'in 2000 limiti**
(`validation.ts > CAPTION_MAX_LENGTH`). `saas_gonder.py` gonderimden once
2000'e gore eliyor; arada kalan bir caption SaaS'tan 400 donerdi.

Gorseller `raw.githubusercontent.com` uzerinden servis edilir — Instagram public
URL istiyor, repo public oldugu icin ek barindirma gerekmiyor. **Bu yuzden bir
post push edilmeden siraya konamaz**; `saas_gonder.py` her URL'i HEAD ile
kontrol eder ve erisilemeyeni eler.

---

## Sorun giderme

**`aday_yok`** — yayinlanmamis post kalmadi. `insta-ingilizce` ile yeni post
uret, push et.

**`uygun_aday_yok`** — post var, hepsi elendi. `elenenler` sebebi yaziyor. Toplu
`HTTP 404` ise postlar push edilmemis ya da yanlis daldasin; `IG_RAW_BASE`
elle ayarlanmissa yanlis yeri gosteriyor olabilir.

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

**`code=4` / `error_subcode=2207051`** (`Application request limit reached` +
`We restrict certain activity to protect our community`) — Instagram'in spam
korumasi. SaaS'ta, token'da ya da kotada sorun yok; kisit **hesap seviyesinde**
ve her "tekrar dene" yeni bir media container acip kisiti besliyor. Yapilacak:
**denemeyi birak, birkac saat bekle**. Tipik olarak kendiliginden kalkiyor.

> 2026-08-19'da boyle yasandi: bir posta ait **iki ayri onay linki** ayni anda
> canliydi (hatali gorselle giden ilk kayit + duzeltilmis gorselle gonderilen
> ikinci kayit). Musteri once eskisini onayladi, post yayinlandi; 18 dakika
> sonra yenisi onaylaninca Instagram ayni gorselin ikinci kez atilmasini spam
> sayip hesabi kisitladi. SaaS'in mukerrer korumasi da devreye giremedi, cunku
> canlilik sorgusu ayni kisita takilip "belirsiz" dondu ve belirsizde yayina
> izin veriliyor (`publish-post.ts`, bilincli karar).
>
> **Ders: bir postun duzeltilmis surumu gonderilecekse, once eski SaaS kaydi
> panelden silinmeli.** Iki canli onay linki = iki yayin riski.

**Defter ile Instagram ayrismis** — `esitle.py` iki yonlu duzeltir. Silinen bir
post defterden dusurulup tekrar aday olur.

**Token suresi doluyor** — yenileme SaaS'in isi: gunluk cron
(`/api/cron/refresh-instagram-tokens`, 03:00) bitisine 20 gun kala token'i
otomatik uzatiyor ve tek kopya oldugu icin bu repo da aninda yeni token'i
goruyor. `ig_token.py --kontrol` kalan sureyi soyler. `yakinda_doluyor`
goruyorsan cron calismiyor demektir — Vercel cron loglarina bak. Suresi
tamamen dolmus bir token otomatik uzatilamaz; SaaS panelinden musterinin
Instagram baglantisini yenilemek gerekir.

---

## Ilgili dosyalar

- `otomasyon/README.md` — durum dosyalarinin semasi, elle mudahale
- `SAAS-ENTEGRASYON-PLANI.md` — mimarinin neden boyle oldugu, SaaS tarafi
- `KURULUM.md` — Instagram token'i + SaaS baglantisi (tek seferlik)
- `emekli/README.md` — Gmail/Apps Script zinciri: neden birakildi, nasil geri alinir
- `.env.example` — gereken ortam degiskenlerinin adlari (repo kokunde)
- `WORKFLOW.md` — post uretim akisi (`insta-ingilizce` skill'i)

## Kunye

| Parca | Deger |
|---|---|
| Rutin | `trig_01TtprvNfdZd5DDEfR8uDCRj` ([panel](https://claude.ai/code/routines/trig_01TtprvNfdZd5DDEfR8uDCRj)) |
| Cron | `7 9 * * *` UTC = 12:07 Istanbul (gunde 1 calisma) |
| SaaS | https://content-approval-saas.vercel.app |
| Instagram hesabi | `furkanteacherteaching` (`17841441566401393`) |
| Onay -> yayin | ~11 saniye (production'da olculdu) |
