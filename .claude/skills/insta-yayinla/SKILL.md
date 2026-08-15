---
name: insta-yayinla
description: Repodaki hazir postlari @furkanteacherteaching Instagram hesabina otomatik yayinlar. Siradaki postu kategori rotasyonuyla secer, eneshan034@gmail.com adresine onay maili atar, mailde "EVET" yaniti gelirse Instagram Graph API ile yukler. Zamanlanmis calisma (cron / routine) icin tasarlandi; elle "/insta-yayinla" ile de calistirilabilir.
---

# insta-yayinla — otomatik Instagram yayinlama

Bu skill **post uretmez**. Uretim `insta-ingilizce` skill'inin isi. Bu skill sadece
repoda hazir duran postlari sirayla, onay alarak Instagram'a tasir.

Hedef tempo: **gunde 2 post**.

---

## Bu skill'in calisma mantigi

Bir agent calismasi saatlerce mail yaniti bekleyemez. Bu yuzden akis tek parca degil,
**durum makinesi**: her tetiklemede tek bir is yapilir ve cikilir.

```
   tetikleme 1  ->  aday sec, onay maili at, CIK
   tetikleme 2  ->  yanit gelmis mi? gelmemis. CIK          (hicbir sey yapma)
   tetikleme 3  ->  yanit gelmis mi? "EVET". YAYINLA. CIK
   tetikleme 4  ->  gunluk kota dolmus mu? dolmamis, 4 saat gecmis. Yeni aday. CIK
```

Durum `otomasyon/durum.json` ve `otomasyon/yayinlananlar.json` icinde tutulur ve
**her calismanin sonunda commit + push edilir**. Bulut calismasi her seferinde temiz
klonla basladigi icin state'in hayatta kalmasinin tek yolu budur.

Zamanlayici saat basi tetikleyebilir; kota mantigi bu skill'in icinde oldugu icin
gunde en fazla 2 post cikar.

---

## DEGISMEZ KURALLAR

Bu kurallar canli bir hesaba yaziyor. Hicbiri "duruma gore" degil.

1. **Onay yoksa yayin yok.** Mail thread'inde, onay maili gonderildikten SONRA gelmis,
   acikca "EVET" diyen bir yanit olmadan hicbir post yayinlanmaz. Yanit yokluğu onay
   degildir. Belirsiz yanit ("bence olur", "bakarim") onay degildir — onay sayilmaz,
   bekleyen olarak birakilir.
2. **Ayni post iki kez atilmaz.** Yayin defteri + `yayin_denemesi` isareti + Instagram
   dogrulamasi bunu birlikte garanti eder. Isaret adimlarini asla atlama.
3. **Calisma basina en fazla 1 yayin, takvim gunu basina en fazla 2.**
4. **Hata olursa state'e dokunma.** Hata maili at, oldugun yerde dur. Yarim durum yazma.
5. **Sadece `otomasyon/*.json` commit edilir.** Gorseller, `caption.md`, skill dosyalari
   bu akista asla degistirilmez. `--force` push yok.
6. **`.env` asla commit edilmez.** Repo public. Token'i hicbir yere (mail, log, commit
   mesaji, ekrana) yazma.
7. **Kullaniciya sorma.** Bu skill gozetimsiz calisir. Karar veremedigin bir durumda
   `AskUserQuestion` cagirma — mail at ve cik.

---

## Faz 0 — Ortam

```powershell
cd "C:\Users\enesm\visual studio\furi1"
git pull --ff-only
```

Bulut calismasinda repo zaten taze klonlanmis olur; `git pull` hata verirse gec.

Sonra saglik kontrolu:

```powershell
python .claude\skills\insta-yayinla\scripts\ig_yayinla.py --kontrol
```

- `durum: hata` -> **DUR.** Hata mailini at (asagidaki sablon), state'e dokunma, cik.
- Token/`IG_USER_ID` eksik hatasi -> kurulum yapilmamis. `KURULUM.md`'yi isaret eden
  bir mail at ve cik.

Token omru:

```powershell
python .claude\skills\insta-yayinla\scripts\ig_token.py --kontrol
```

- `yenileme_gerekli: true` -> `ig_token.py --yenile` calistir.
- `durum: yakinda_doluyor` veya `suresi_doldu` -> uyari maili at (gunde 1 kez yeter).
- `durum: bilinmiyor` -> `ig_token.py --kaydet` calistir, devam et.

**Yarida kalmis yayin kontrolu.** `otomasyon/durum.json` icinde `yayin_denemesi`
dolu ise, bir onceki calisma yayin sirasinda kesilmis demektir:

```powershell
python .claude\skills\insta-yayinla\scripts\ig_yayinla.py --dogrula <slug>
```

- `aslinda_yayinlanmis` -> post gercekten atilmis, script deftere isledi. Faz 4'e gec.
- `yayinlanmamis` -> isaret duruyor, Faz 3'ten yayina devam edilebilir.
- **Bu adimi atlayip dogrudan yayinlama.** Ayni postun ikinci kez atilmasini engelleyen
  tek kontrol budur.

---

## Faz 1 — Bekleyen onay var mi?

`otomasyon/durum.json` > `bekleyen` bos ise Faz 2'ye gec.

Dolu ise thread'i bul:

1. `mcp__claude_ai_Gmail__search_threads`
   query: `subject:"<bekleyen.mail_konu>" newer_than:3d`
   (`bekleyen.mail_thread_id` kayitliysa dogrudan onu kullan.)
2. `mcp__claude_ai_Gmail__get_thread`
   threadId: bulunan id, messageFormat: `PLAIN_TEXT`

**Yanit ayristirma — dikkatli yap:**

- Sadece `date` degeri `bekleyen.gonderim_zamani`'ndan **sonra** olan mesajlara bak.
- Gonderdigin orijinal maili yanit sanma.
- Govdede alinti bolumu (`On ... wrote:` satiri veya `>` ile baslayan satirlar)
  baslamadan onceki kismi al.
- O kismin ilk bos olmayan satirini buyuk/kucuk harf duyarsiz degerlendir:

| Yanit | Karar |
|---|---|
| `EVET`, `OK`, `TAMAM`, `YAYINLA`, `ONAY` | **onaylandi** -> Faz 3 |
| `HAYIR`, `YOK`, `ATLA`, `IPTAL`, `GECE` | **reddedildi** |
| Bunlarin disinda bir sey | **belirsiz** -> onay SAYMA, bekleyen kalsin, cik |

**Onaylandi** -> Faz 3.

**Reddedildi** -> `durum.json` icinde:
- `atlananlar` listesine `{slug, tarih, sebep: "mailde HAYIR"}` ekle
- `bekleyen` -> `null`

Sonra Faz 2'ye gec (ayni calismada yeni bir aday onerilebilir).

**Yanit yok:**
- `son_gecerlilik` gecmemisse -> hicbir sey yapma, **cik**. State'e dokunma.
- `son_gecerlilik` gecmisse -> `atlananlar`'a `sebep: "onay suresi doldu"` ile ekle,
  `bekleyen` -> `null`, bilgi maili at, Faz 4'e gec ve **cik** (ayni calismada yeni
  aday onerme; bir sonraki tetiklemede onerilir).

---

## Faz 2 — Yeni aday oner

Cikis sartlari — herhangi biri saglaniyorsa hicbir sey yapmadan Faz 4'e gec:

- `bugun.yayinlanan >= 2` (gunluk kota dolu)
- `son_yayin` uzerinden 4 saatten az gecmis (iki post ayni saate yigilmasin)
- `bekleyen` hala dolu (Faz 1'de temizlenmemis)

Adayi sec:

```powershell
python .claude\skills\insta-yayinla\scripts\aday_sec.py
```

Cikti `durum: aday_yok` ise: "post stogu bitti" maili at (gunde 1 kez), Faz 4'e gec.

Cikti `durum: secildi` ise onay mailini gonder — `mcp__claude_ai_Gmail__send_message`:

- **to:** `["eneshan034@gmail.com"]`
- **subject:** `[FURI-ONAY] <slug> - <GG.AA.YYYY SS:DD>`
- **htmlBody:** asagidaki sablon
- **body:** ayni icerigin duz metin hali (gorseller yerine URL listesi)

```html
<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:520px;
            color:#0E2038;line-height:1.55">
  <p style="margin:0 0 4px;font-size:13px;color:#6B7280">
    <b style="color:#EF4A18">FURI</b> &middot; yayin onayi
  </p>
  <h2 style="margin:0 0 2px;font-size:19px">{slug}</h2>
  <p style="margin:0 0 18px;font-size:13px;color:#6B7280">
    {kategori} &middot; {slayt} slayt &middot; kalan aday: {kalan_aday}
  </p>

  <!-- her gorsel icin bir tane -->
  <img src="{url}" alt="{alt_text}" width="260"
       style="display:block;width:260px;max-width:100%;border-radius:8px;
              margin:0 0 10px;border:1px solid #E5E0CF">

  <h3 style="margin:22px 0 6px;font-size:14px">Caption</h3>
  <div style="white-space:pre-wrap;font-size:14px;background:#FAF6E9;
              padding:14px 16px;border-radius:8px">{caption}</div>

  <div style="margin:22px 0 0;padding:14px 16px;background:#FAF6E9;
              border-left:3px solid #EF4A18;border-radius:4px;font-size:14px">
    <b>Bu maili yanitla:</b><br>
    <b>EVET</b> &rarr; Instagram'a yuklenir<br>
    <b>HAYIR</b> &rarr; atlanir, sirada bir sonraki post secilir
  </div>
  <p style="margin:12px 0 0;font-size:12px;color:#6B7280">
    {son_gecerlilik} tarihine kadar yanit gelmezse iptal olur.
  </p>
</div>
```

Gonderdikten hemen sonra thread id'yi yakala: `search_threads` ile
`subject:"<gonderdigin konu>"` ara, donen `id`'yi kaydet.

`durum.json` > `bekleyen` yaz:

```json
{
  "slug": "<slug>",
  "kategori": "<kategori>",
  "slayt": <n>,
  "mail_konu": "<gonderilen konu, birebir>",
  "mail_thread_id": "<bulunduysa>",
  "gonderim_zamani": "<simdi, ISO+03:00>",
  "son_gecerlilik": "<simdi + 6 saat, ISO+03:00>"
}
```

`aday_sec.py` ciktisinda `stok_dusuk: true` ise Faz 5'i de calistir. Faz 4'e gec.

---

## Faz 3 — Yayinla

Sirayi bozma. Isaret **once** yazilir ve **push edilir**; boylece calisma yayin
sirasinda kesilse bile bir sonraki calisma ne oldugunu anlayabilir.

```powershell
# 1) isaretle
python .claude\skills\insta-yayinla\scripts\ig_yayinla.py --isaretle <slug>

# 2) isareti PUSH et  (bu adim atlanamaz)
git add otomasyon/durum.json
git commit -m "Yayin denemesi isareti: <slug>"
git push

# 3) yayinla
python .claude\skills\insta-yayinla\scripts\ig_yayinla.py --slug <slug>
```

Ciktiya gore:

| `durum` | Ne yapilir |
|---|---|
| `yayinlandi` | Script defteri ve sayaci zaten guncelledi. Sonuc mailini at, Faz 4. |
| `zaten_yayinlandi` | Post daha once atilmis. Tekrar deneme. Bilgi maili at, Faz 4. |
| `hata` | State'e dokunma. Hata mailini `mesaj` + `ayrinti` ile at, Faz 4, **cik**. |
| `isaret_yok` | 1. adim atlanmis. Basa don. |

Yayin basariliysa **sonuc maili** at:

- subject: `[FURI-YAYIN] <slug> yayinlandi`
- govde: permalink, kategori, slayt sayisi, `bugun.yayinlanan` / 2, kalan aday sayisi

Hata durumunda **hata maili**:

- subject: `[FURI-HATA] <slug> yayinlanamadi`
- govde: script ciktisindaki `mesaj` ve `ayrinti` **oldugu gibi** (Meta'nin hata kodu
  teshis icin gerekli), ne yapildigi, ne yapilmadigi, `yayin_denemesi` isaretinin
  durdugu ve bir sonraki calismanin `--dogrula` ile kontrol edecegi

---

## Faz 4 — Kapanis (her cikista, istisnasiz)

```powershell
git add otomasyon/durum.json otomasyon/yayinlananlar.json
git commit -m "<yapilan is: aday onerildi / yayinlandi / atlandi / kota dolu>"
git push
```

Degisiklik yoksa commit atma, sorun degil. Baska hicbir dosyayi `git add` etme.

Push basarisiz olursa: bu ciddidir — bir sonraki calisma eski state'i gorur ve ayni
postu tekrar onerebilir. Push hatasini **hata maili ile bildir**.

---

## Faz 5 — Stok kontrolu

`aday_sec.py --durum` ciktisinda `stok_dusuk: true` ve `durum.json` >
`son_stok_uyarisi` bugun degilse:

- subject: `[FURI-STOK] N post kaldi`
- govde: kalan sayi, kategori dagilimi, kac gun yeter (kalan / 2), `insta-ingilizce`
  ile yeni post uretilmesi gerektigi
- sonra `son_stok_uyarisi` = bugunun tarihi, Faz 4'te commit et

---

## Komut kunyesi

Tum komutlar repo kokunden calistirilir.

| Komut | Ne yapar | API'ye yazar mi |
|---|---|---|
| `aday_sec.py` | Siradaki adayi secer, JSON basar | hayir |
| `aday_sec.py --dry-run` | Ayni + okunakli ozet | hayir |
| `aday_sec.py --durum` | Havuz istatistigi, stok durumu | hayir |
| `aday_sec.py --slug K/S` | Belirli postun verisi | hayir |
| `ig_yayinla.py --kontrol` | Hesap + yayin limiti + token saglik testi | hayir (okur) |
| `ig_yayinla.py --onizle K/S` | Yayin hazirligini test eder | hayir |
| `ig_yayinla.py --isaretle K/S` | Yayin oncesi isareti yazar | hayir |
| `ig_yayinla.py --slug K/S` | **YAYINLAR** | **EVET** |
| `ig_yayinla.py --dogrula K/S` | Yarida kalan deneme gercekten atilmis mi | hayir (okur) |
| `ig_yayinla.py --tek-slayt K/S` | Sadece 1.jpg yayinlar, kayit tutmaz (en-boy testi) | **EVET** |
| `ig_yayinla.py --temizle-isaret` | Isareti siler | hayir |
| `ig_token.py --kontrol` | Token kac gun gecerli | hayir |
| `ig_token.py --yenile` | Gerekiyorsa token yeniler | hayir |
| `ig_token.py --kaydet` | 60 gunluk sayaci baslatir (kurulumda 1 kez) | hayir |

Cikis kodlari: `0` basarili · `1` hata · `2` yapilacak is yok (zaten yayinlanmis) ·
`3` dikkat gerekiyor.

---

## Aday secimi nasil calisir

**Kategori rotasyonu.** En uzun suredir yayinlanmamis kategori once gelir; o kategori
icinde repoya en once eklenmis post secilir. Boylece arka arkaya iki phrasal ya da iki
seviye testi cikmaz.

Bir post su durumlarda aday olmaz: yayin defterinde kayitli, `atlananlar` icinde,
`bekleyen` olarak duruyor, ya da dogrulamayi gecemiyor (10'dan fazla slayt, 2200'den
uzun caption, 30'dan fazla hashtag, erisilemeyen gorsel URL'i).

Gorseller `raw.githubusercontent.com` uzerinden servis edilir — Instagram API'si public
URL istiyor, repo public oldugu icin ek bir barindirma gerekmiyor. **Bu yuzden bir post
push edilmeden yayinlanamaz**; `aday_sec.py` her URL'i HEAD ile kontrol eder ve
erisilemeyeni eler.

---

## Sorun giderme

**`isaret_yok`** — `--isaretle` calistirilmadan `--slug` denendi. Sira: isaretle, push,
yayinla.

**`yayin_denemesi` dolu kalmis** — bir calisma yayin sirasinda kesilmis.
`--dogrula <slug>` calistir. Instagram'da varsa script deftere isler; yoksa yayin
tekrar denenebilir. **Elle `--temizle-isaret` calistirmadan once mutlaka `--dogrula`.**

**`Media ID is not available` / container hatasi** — Instagram gorseli cekemedi.
Genelde URL sorunu: repo push edilmemis, dosya adi degismis, ya da branch farkli.
`aday_sec.py --slug K/S` ile URL'lerin 200 dondugunu dogrula.

**Gorsel reddedildi / kirpildi** — gorseller 1920x2400 (4:5). Meta dokumani azami
genislik olarak 1440 piksel veriyor ve Instagram genelde kendi kucultuyor. Sorun
cikarsa gorselleri 1080x1350'ye kucultup `otomasyon/pub/<kategori>/<slug>/` altina
yazan bir adim eklenmeli ve `IG_RAW_BASE` oraya yonlendirilmeli.

**Token suresi doldu** — `ig_token.py --yenile` 24 saatten eski token'lari yeniler.
Token tamamen olduyse yenileme calismaz; `KURULUM.md` ile yeni token uret.

**Mail yaniti okunamiyor** — `get_thread`'i `PLAIN_TEXT` ile cagir. Alinti bolumunu
(`On ... wrote:` / `>` satirlari) ayikladigindan ve sadece gonderim zamanindan sonraki
mesajlara baktigindan emin ol.

**Bulutta Gmail'e erisilemiyor** — routine ortaminda Gmail baglantisi yoksa akis
calismaz. Bu durumda zamanlayiciyi yerel makineye tasi:
`schtasks /create /tn "furi-insta" /tr "claude -p /insta-yayinla" /sc hourly`
Skill'de degisiklik gerekmez, iki ortamda da ayni calisir.

---

## Ilgili dosyalar

- `otomasyon/README.md` — durum dosyalarinin semasi, elle mudahale
- `.claude/skills/insta-yayinla/KURULUM.md` — Meta app + token kurulumu (tek seferlik)
- `WORKFLOW.md` — post uretim akisi (`insta-ingilizce` skill'i)
