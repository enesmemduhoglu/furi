---
name: insta-ingilizce
description: Instagram Ingilizce ogrenme sayfasi icin post uretir - fikir gorusmesi, slayt metni, kart gorsellerinin yerelde basilmasi, metin denetimi, caption ve puanlama. Kullanici post, karusel, slayt, gonderi, "ne paylassak" gibi seylerden bahsettiginde calisir.
---

# Instagram Ingilizce Sayfasi — Post Uretim Akisi

Bu akis 8 fazdan olusur (Faz 3 emekli). Iki onay noktasi var: **Faz 2 (slayt
metni)** ve **Faz 8 (commit)**.

> **Kart metni bir goruntu modelinden gecmez.** Harfler `marka/kart_bas.ps1`
> ile gercek fontla basiliyor; yazim hatasi ve eksik Turkce karakter mumkun
> degil. Gerekce: [Faz 4](#faz-4--gorsel-uretimi).

## ⚠️ Her PowerShell cagrisinda gecerli iki kural

1. **Shell state cagrilar arasinda korunmuyor.** Degiskenler ve `$env:` degerleri bir sonraki komutta yok. Her PowerShell komutunun ilk satiri `.env` yuklemesi olmali:
   ```powershell
   Get-Content "C:\Users\enesm\visual studio\furi1\.env" | Where-Object { $_ -match '^\s*[A-Za-z_]+\s*=' } | ForEach-Object { $k,$v = $_ -split '=',2; Set-Item -Path "env:$($k.Trim())" -Value $v.Trim() }
   ```
2. **`Invoke-RestMethod` kullanma.** PS 5.1'de bu API'lerde `NullReferenceException` firlatiyor ve hata mesaji hicbir sey soylemiyor. Bunun yerine `& "$env:SystemRoot\System32\curl.exe"` kullan; govdeyi gecici bir dosyaya yazip `--data-binary "@dosya"` ile gonder (UTF-8 ve tirnak sorunlarini bu cozuyor).

Uretim yeri: `C:\Users\enesm\visual studio\furi1\<format>\<konu-slug>\`
Referans arsiv: ayni repodaki `seviye-testi/`, `hikayeli/`, `durumsal/`, `phrasal/`, `karistirilan/` klasorleri — 60 gorsel, marka sisteminin canli ornegi. Emin olmadigin bir tasarim kararinda bunlardan birini `Read` ile ac ve bak.

**Klasor duzeni:** her post kendi klasorunde durur, klasor de formatinin altinda. Bir post = bir klasor = `1.jpg … N.jpg` + `caption.md` + `kart.json` (slayt metni, gorselin kaynagi) + `puan.json`.

---

## Faz 0 — Kurulum kontrolu

Her oturumda ilk is, anahtarlarin yuklu oldugunu dogrula:

```powershell
$envFile = "C:\Users\enesm\visual studio\furi1\.env"
if (Test-Path $envFile) {
  Get-Content $envFile | Where-Object { $_ -match '^\s*[A-Za-z_]+\s*=' } | ForEach-Object {
    $k, $v = $_ -split '=', 2
    Set-Item -Path "env:$($k.Trim())" -Value $v.Trim()
  }
}
"GEMINI_API_KEY: " + $(if ($env:GEMINI_API_KEY) { "var" } else { "YOK" })
"FAL_KEY: " + $(if ($env:FAL_KEY) { "var" } else { "YOK" })
```

Gemini modelini de dogrula — plan degisirse hangi modelin acik oldugu degisir:

```powershell
$m = (& "$env:SystemRoot\System32\curl.exe" -s "https://generativelanguage.googleapis.com/v1beta/models?pageSize=200" -H "x-goog-api-key: $env:GEMINI_API_KEY") -join "" | ConvertFrom-Json
$m.models | Where-Object { $_.supportedGenerationMethods -contains "generateContent" } | ForEach-Object { $_.name }
```

**Not (2026-08 itibariyle):** `gemini-3.1-pro-preview` listede gorunuyor ama ucretsiz katmanda kotasi 0 — 429 doner. Ucretsiz katmanda calisan: `gemini-3.6-flash` (varsayilan), `gemini-3.5-flash`, `gemini-3-flash-preview`. Prompt yazma isi icin flash yeterli. Kullanici Google Cloud'da faturalandirmayi acarsa `gemini-3.1-pro-preview`'a gec.

Eksikse kullanicidan `furi1\.env` dosyasina eklemesini iste:

```
GEMINI_API_KEY=...
FAL_KEY=...
```

**Repo public.** `.env` asla commit edilmez, ekrana yazdirilmaz, prompt icine konmaz. `.gitignore`'da `.env` satiri olmali — yoksa once onu ekle.

---

## Faz 1 — Brief (konusma)

Kullanici ya net bir konuyla gelir ("otelde check-in cumleleri yapalim") ya da fikir ister ("ne paylassak").

**Fikir isteniyorsa:** asagidaki 5 formatin arsivde ne kadar kullanildigina bak, 3 somut oneri sun. Her oneri: *format + baslik + neden ilgi ceker* (tek satir). Tekrar eden konu onerme — arsivdeki klasor adlari zaten islenmis konular.

**Konu netse:** dogrudan format + slayt sayisi oner.

Sonra `AskUserQuestion` ile format ve slayt sayisini onaylat.

### 5 post formati

| Format | Slayt | Arsiv ornegi |
|---|---|---|
| Seviye testi (A1/A2/B1/B2) | 8 | `seviye-testi/a1/`, `seviye-testi/b2/` |
| Durumsal Ingilizce — seri | 5 | `hikayeli/otel/`, `hikayeli/havaalaninda/` |
| Durumsal Ingilizce — tekil kart | 1 | `durumsal/on-the-side/` |
| Gunun Phrasal Verb'u | 1 | `phrasal/figure-out/` |
| Sik Karistirilanlar (X vs Y) | 1 | `karistirilan/make-vs-do/` |

Slayt iskeletleri icin → [Ek B](#ek-b--format-iskeletleri).

---

## Faz 2 — Slayt metni  ⛔ ONAY NOKTASI

Slayt slayt metni yaz ve **markdown tablo** halinde kullaniciya goster. Onaylanmadan Faz 3'e gecme.

### Metin kurallari

1. **Tam Turkce — zorunlu.** `ç ğ ı ö ş ü İ` oldugu gibi yazilir; ASCII'ye cevrilmez. *(2026-08-20 oncesi kural bunun tersiydi — sebep gorsel modelinin diyakritigi bozmasiydi. Metin artik modelden gecmiyor: [Faz 4](#faz-4--gorsel-uretimi) kartlari gercek fontla yerelde basiyor, yani harf bozulmasi mumkun degil.)* Metni `kart.json`'a yazip `python marka/metin_denetle.py <kart.json>` calistir; eksik diyakritik ve kanonik olmayan kategori etiketi oradan doner.
2. Ingilizce metin oldugu gibi yazilir.
3. Uzunluk siniri: dev baslik ≤ 22 karakter · Ingilizce cumle ≤ 60 karakter · Turkce ceviri ≤ 70 karakter · CTA ≤ 45. `metin_denetle.py` bunlari zorluyor. Sebep artik yazim hatasi degil yerlesim: uzun baslikta punto dusuyor ve hiyerarsi zayifliyor.
4. Karuselin son slaytinda mutlaka CTA olsun (kaydet / yorum yap / arkadasina gonder).
5. Emoji sadece CTA satirinda ve en fazla 1 tane.
6. Turkce ceviri her zaman **parantez icinde** ve gri tonda.

### Tablo formati

| # | Etiket | Baslik | Ingilizce | Turkce (parantez) | CTA |
|---|---|---|---|---|---|
| 1 | DURUMSAL İNGİLİZCE | OTELDE CHECK-IN | — | — | Kaydır → |
| 2 | DURUMSAL İNGİLİZCE | I HAVE A RESERVATION | I have a reservation under the name Demir. | (Demir adına bir rezervasyonum vardı.) | Odaya çıkalım... Kaydır → |

Onaylanan tablo `kart.json`'a gecer (sema: `marka/README.md`). Model sutunu
kalkti — kartlari artik model uretmiyor.

---

## Faz 3 — Gemini ile gorsel promptu uretimi  ⛔ EMEKLI (2026-08-20)

Kart metni artik bir goruntu promptuna girmiyor; `kart.json`'dan dogruca
basiliyor (Faz 4). Bu fazin butun isi — metni tirnak icinde birebir tasitmak,
Gemini'nin diyakritik "duzeltmesini" engellemek — konusuz kaldi.

Asagidaki blok, ileride gorsel bir oge (ornegin yeni bir zemin dokusu)
gerekirse referans olsun diye duruyor. **Sistem promptundaki ASCII sarti
gecersiz.**

<details>
<summary>Emekli Faz 3 (referans)</summary>

```powershell
$sistem = @'
You are a prompt engineer for a text-to-image model. You will receive slide texts for an
Instagram carousel and must return one image-generation prompt per slide.

HARD RULES:
- Every prompt MUST reproduce the given text EXACTLY, wrapped in double quotes, character
  for character. Never rewrite, translate, correct, shorten or re-order the text.
- The text is intentionally ASCII-only Turkish (no c-cedilla, no dotless i, no umlauts).
  Never add diacritics back. Never "fix" the spelling.
- Every prompt MUST describe this exact visual system:
  4:5 vertical typographic poster, warm cream paper background #FAF6E9 with subtle paper
  grain, deep navy ink #0E2038, a single orange-red accent #EF4A18 used ONLY for the small
  uppercase category label at the top, generous whitespace, everything center-aligned,
  bold geometric grotesque headline, clean geometric sans for body text, flat editorial
  design.
- Explicitly forbid: illustrations, photographs, human figures, icons other than a single
  arrow or emoji if specified, borders, frames, logos, watermarks, gradients, drop shadows,
  decorative objects, extra text of any kind.
- State the vertical order of every text element and its relative size.

Return ONLY a JSON array: [{"slide": 1, "prompt": "..."}, ...]
'@

$slaytlar = @'
<Faz 2'de onaylanan tablo buraya, duz metin olarak>
'@

$body = @{
  contents = @(@{ role = "user"; parts = @(@{ text = "$sistem`n`n---`n`nSLIDES:`n$slaytlar" }) })
  generationConfig = @{ responseMimeType = "application/json"; temperature = 0.4 }
} | ConvertTo-Json -Depth 10
$body | Out-File "$env:TEMP\gemini_req.json" -Encoding utf8 -NoNewline

$raw = & "$env:SystemRoot\System32\curl.exe" -s -X POST `
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent" `
  -H "x-goog-api-key: $env:GEMINI_API_KEY" -H "Content-Type: application/json" `
  --data-binary "@$env:TEMP\gemini_req.json"

$parsed = ($raw -join "") | ConvertFrom-Json
if ($parsed.error) { "API HATASI: " + $parsed.error.message } else {
  $txt = $parsed.candidates[0].content.parts[0].text
  $txt | Out-File "$out\prompts.json" -Encoding utf8
  $txt
}
```

</details>

---

## Faz 4 — Gorsel uretimi

Kartlar **yerelde basiliyor**. Metin bir goruntu modelinden gecmiyor.

```powershell
powershell -File marka\kart_bas.ps1 -Spec dizi\tell-me-about-it\kart.json -Hedef dizi\tell-me-about-it
```

Sema, oge turleri, kanonik kategori etiketleri ve font secimi: **`marka/README.md`**.

Betik basmadan once `metin_denetle.py`'yi calistirir; denetim gecmezse **hicbir
dosya yazmaz**. Yani "denetimi atlamak" diye bir ihtimal yok.

### Neden model degil

`HATA-RAPORU.md` bu sorunun defteri: `conoditional`, `değidlir`, `alablir`,
`edoceklere`, `KITAP vs GERCEX`. 2026-08-20'de tek bir kart uzerinde uc deneme
yapildi, **ikisinde harf hatasi cikti** (`olocak`, `Kaybet`). Difuzyon modeline
"dogru yaz" demek istatistiksel bir sey; kac kez denersen dene garanti vermiyor,
yalnizca denetimle yakalaniyor. Harfleri cizdirmek yerine basmak sorunu
kokunden kaldiriyor: ciktinin metni girdinin metni.

Yan kazanclar: slayt basina uretim maliyeti sifir, tekrar denemek bedava,
hizalama piksel piksel kontrolde, zemin her kartta ayni (arsivdeki "zemin rengi
kayiyor" sorunu kapandi) ve postun metni repoda `kart.json` olarak duruyor —
diff'lenebilir, grep'lenebilir.

### fal.ai — artik kart uretiminde kullanilmiyor

Asagidaki cagrilar **yeni bir zemin dokusu** gerekirse duruyor (`marka/zemin.jpg`
arsivden cikarildi, yenisi lazim olursa seedream'e metinsiz kagit uretimi
yaptirilir). Kart metni icin kullanilmaz.

### seedream cagrisi

> ⛔ **Status/result URL'ini elle kurma.** fal'da submit adresi tam endpoint yolu (`fal-ai/bytedance/seedream/v5/lite/text-to-image`) ama status/result adresi sadece **uygulama kimligi** (`fal-ai/bytedance`). Tam yolu kullanirsan HTTP 405 + bos govde doner ve polling sonsuza kadar bosa doner. Cozum: submit yanitindaki `status_url` ve `response_url` alanlarini oldugu gibi kullan.

```powershell
$ep = "fal-ai/bytedance/seedream/v5/lite/text-to-image"
$body = @{
  prompt     = $prompt
  image_size = @{ width = 1920; height = 2400 }
  num_images = 1
} | ConvertTo-Json -Depth 5
$body | Out-File "$env:TEMP\fal_req.json" -Encoding utf8 -NoNewline

$sub = (& "$env:SystemRoot\System32\curl.exe" -s -X POST "https://queue.fal.run/$ep" `
  -H "Authorization: Key $env:FAL_KEY" -H "Content-Type: application/json" `
  --data-binary "@$env:TEMP\fal_req.json") -join "" | ConvertFrom-Json

if (-not $sub.request_id) { "SUBMIT HATASI: " + ($sub | ConvertTo-Json -Depth 4 -Compress); return }
"request_id: $($sub.request_id)"

$deadline = (Get-Date).AddSeconds(150)
do {
  Start-Sleep -Seconds 5
  $st = (& "$env:SystemRoot\System32\curl.exe" -s $sub.status_url -H "Authorization: Key $env:FAL_KEY") -join "" | ConvertFrom-Json
  "durum: $($st.status)"
} while ($st.status -ne "COMPLETED" -and (Get-Date) -lt $deadline)

$res = (& "$env:SystemRoot\System32\curl.exe" -s $sub.response_url -H "Authorization: Key $env:FAL_KEY") -join "" | ConvertFrom-Json
& "$env:SystemRoot\System32\curl.exe" -s -o "$out\$n.jpg" $res.images[0].url
```

> `image_size` custom deger limiti: toplam piksel 2560×1440 ile 4096×4096 arasi olmali. 1920×2400 = 4.6 MP ✓ gecerli.
>
> Uretim ~35 saniye suruyor. PowerShell aracinin varsayilan zaman asimi 2 dakika — **cok slaytli karuselde her slaytin uretimini ayri komutta calistir**, hepsini tek komuta koyma yoksa timeout yersin.

### mai cagrisi + 4:5 duzeltmesi

`microsoft/mai-image-2.5-pro`'nun `aspect_ratio` enum'unda **4:5 yok** (`auto, 1:1, 4:3, 3:4, 16:9, 9:16, 3:2, 2:3`). Arsivdeki `seviye-testi/a1/7.png`, `a2/7.png`, `b1/7.png` bu yuzden 1024×1024 kare kalmis ve karuselde kirpiliyor. Cozum: 3:4 uret, 1920 genislige olcekle, ustten ve alttan 80'er piksel simetrik kirp.

```powershell
$ep = "microsoft/mai-image-2.5-pro"
$body = @{
  prompt        = $prompt
  aspect_ratio  = "3:4"
  output_format = "jpeg"
  num_images    = 1
} | ConvertTo-Json -Depth 5
# ... submit + polling yukaridakiyle ayni, ciktiyi "$out\_raw$n.jpg" olarak indir

Add-Type -AssemblyName System.Drawing
$src    = [System.Drawing.Image]::FromFile("$out\_raw$n.jpg")
$scaled = New-Object System.Drawing.Bitmap 1920, 2560
$g      = [System.Drawing.Graphics]::FromImage($scaled)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.DrawImage($src, 0, 0, 1920, 2560)
$final = $scaled.Clone([System.Drawing.Rectangle]::new(0, 80, 1920, 2400), $scaled.PixelFormat)
$final.Save("$out\$n.jpg", [System.Drawing.Imaging.ImageFormat]::Jpeg)
$final.Dispose(); $g.Dispose(); $scaled.Dispose(); $src.Dispose()
Remove-Item "$out\_raw$n.jpg"
```

Marka duzeni ortalanmis ve kenar bosluklari genis oldugu icin 80px kirpma icerik kaybettirmez.

### Dosya adlandirma

`furi1\<format>\<konu-slug>\1.jpg`, `2.jpg`, ... — arsivdeki `seviye-testi/a1/1.jpg`, `hikayeli/otel/1.jpg` kuralinin aynisi.

`<format>` su besten biri:

| `<format>` | Ne girer | Ornek |
|---|---|---|
| `seviye-testi` | 8 slaytlik CEFR testleri | `seviye-testi/b1/` |
| `hikayeli` | Cok slaytli, bir yolculugu anlatan seriler | `hikayeli/havaalaninda/` |
| `durumsal` | Durumsal Ingilizce tekil kartlari | `durumsal/on-the-side/` |
| `phrasal` | Gunun Phrasal Verb'u kartlari | `phrasal/break-down/` |
| `karistirilan` | Sik Karistirilanlar (X vs Y) kartlari | `karistirilan/make-vs-do/` |

`<konu-slug>` ASCII ve tireli olsun, konuyu tarif etsin: `break-down`, `make-vs-do`, `hold-the-onions`.

---

## Faz 5 — Yazim denetimi  ⚠️ atlanmaz

Uretilen **her** gorseli `Read` ile ac ve kontrol et.

**Metin artik denetlenmiyor** — denetlenemez degil, *gerekmiyor*: harfler
`marka/kart_bas.ps1` tarafindan gercek fontla basiliyor, ciktinin metni
`kart.json`'un metni. Metnin kendisi Faz 2'de ve `metin_denetle.py` ile
denetlendi. Geriye yerlesim kaliyor:

1. Boyut 1920×2400 mu?
2. Metin kenardan tasmis / kesilmis / ust uste binmis mi?
3. Baslik punto dusurulurken fazla kuculmus mu? (uzun basliklarda olur — metni kisalt)
4. Dikey denge bozulmus mu? (cok satirli kartlarda blok asagi tasabilir)
5. Zemin dokusu duzgun bindi mi?

**Esik (2026-08-20'de sertlestirildi):** yazim ve diyakritik hatasi
**istisnasiz** duzeltilir — yerel basimda bu zaten bir `kart.json` duzeltmesi,
bedava. Tipografik ufakliklar (tirnak yonu, ok gliflerinin bicimi, birkac
piksel hizalama kaymasi) birakilir ve raporlanir.

> Onceki esik "tek tuk harf hatasi bile yeniden uretim sebebi degil" idi; o
> kural yeniden uretimin **pahali ve belirsiz** oldugu doneme aitti. Yerel
> basimda duzeltme bir metin degisikligi oldugu icin tavizin sebebi kalmadi.

Denetim sonucunu kisa bir tabloyla ozetle.

---

## Faz 6 — Caption

`furi1\<format>\<konu-slug>\caption.md` dosyasina yaz. **Caption metin alani, gorsel degil — burada tam Turkce kullan** (ASCII kurali sadece gorsel icin gecerli).

```markdown
## Aciklama
<2-4 satir. Ilk satir kanca olsun. Konuyu ve kime yaradigini soyle.>

<Son satir: kaydetmeye / yorum yapmaya cagiran CTA>

## Hashtag
<10-15 etiket: genel ingilizce ogrenme + seviye/konu ozel. Tek satir, bosluklu.>

## Alt text
1. <slayt 1 icin erisilebilirlik metni>
2. ...
```

---

## Faz 7 — Puanlama

Post bitti; simdi ona puan ver. Puan `puan.json` olarak post klasorune yazilir ve
icerikle **ayni commit'te** gider.

⚠ **Puan artik yayin sirasini dogrudan belirliyor:** havuz en yuksek puandan
asagiya dogru yayinlaniyor. Yani buradaki puan "bir bilgi notu" degil, postun
kuyrukta nereye oturacagi. Puansiz birakilan post havuzun sonuna duser ve
puanli aday bitene kadar hic yayinlanmaz — bu fazi atlamak postu rafa kaldirir.

```powershell
$S = ".claude\skills\insta-yayinla\scripts"
python $S\puanla.py --sema                          # dallar ve formul
python $S\puanla.py --yaz <kategori>/<slug> --kuru  # yazmadan dogrula
python $S\puanla.py --yaz <kategori>/<slug>         # JSON stdin'den
```

Bes dal, her biri 1-10 **ve zorunlu gerekce**:

| Dal | Soru |
|---|---|
| `ilgi_cekicilik` | Kaydirmayi durdurur mu, kaydetmeye/paylasmaya deger mi |
| `ogretici_deger` | Gercekten bir sey ogretiyor mu, bilineni mi tekrarliyor |
| `ozgunluk` | Onceki postlardan ve piyasadaki tipik icerikten ayrisiyor mu |
| `hedef_kitle` | Seviye, ton ve ornek secimi takipciye oturuyor mu |
| `gorsel_kalite` | Kompozisyon, hiyerarsi, okunabilirlik |

`toplam` script tarafindan hesaplanir, elle yazma: **`ortalama(5 dal)`**.

### ⛔ Uretim kusurlari puana GIRMEZ

Gorseldeki harf hatalari, diyakritik sizintilari, imla ve sablon/marka sapmalari
puanlanmaz — onlarin defteri `HATA-RAPORU.md` ve tespit yeri Faz 5. Puanin
cevapladigi soru **"bu post iyi mi, ilgi ceker mi"**; "duzgun basilmis mi" degil.

Sinir `gorsel_kalite` dalinda geciyor:

- **Girer:** kirik baslik, kutuya sigmayan metin, bozuk dikey denge, birbiriyle
  yarisan iki odak, okunmayan kontrast — bunlar okunabilirligi bozar.
- **Girmez:** yanlis harf, eksik diyakritik, farkli font, kayan zemin rengi,
  baska bir CTA ikonu — bunlar uretim kusuru, kalite olcusu degil.

### Puanlarken

Ureten ile puanlayan ayni model; tek korumamiz gerekcelerin kontrol edilebilir
olmasi. Gerekce **bos sifat olamaz** — "iyi", "guzel", "temiz" tek basina
yazilmaz; **neyin nerede** oldugu yazilir.

> ✅ "Baslik 'RUN OUT' dev puntoda, 'OF' cok daha kucuk ikinci satirda; goz
> kalibi tek birim olarak almiyor."
> ❌ "Gorsel kalitesi dusuk."

Karar gecmisi ve sema: `TODOS.md` > "Post puanlama sistemi",
`otomasyon/README.md` > "Post puani".

---

## Faz 8 — Teslim

1. `SendUserFile` ile uretilen gorselleri kullaniciya goster (`display: "render"`).
2. Ozet ver: kac slayt, hangi model, kac yeniden deneme, nereye kaydedildi.
3. **Commit'i sen yapma — oner ve onay iste.** Repo public; ne zaman yayinlanacagi kullanicinin karari.

---
---

## Ek A — Marka sistemi

Arsivdeki 52 gorselden cikarilmis, degismez sistem:

| Oge | Deger |
|---|---|
| Tuval | 1920 × 2400 px (4:5) |
| Zemin | Sicak krem kagit `#FAF6E9`, uzerinde cok ince grain dokusu |
| Ana mürekkep | Koyu lacivert `#0E2038` |
| Vurgu | Turuncu-kirmizi `#EF4A18` — **sadece** ust kategori etiketinde ve ince ayrac cizgilerinde |
| Ikincil metin | Orta gri `#6B7280` — ceviri ve aciklama satirlarinda |
| Hizalama | Her sey ortalanmis |
| Baslik | Kalin geometrik grotesk, cok buyuk punto; uzun basliklar icin sikisik (condensed) kesim |
| Govde | Temiz geometrik sans, orta agirlik |
| Bosluk | Cok genis — tuvalin ustunde ve altinda buyuk nefes alani |
| Yasak | Illustrasyon, fotograf, ikon, cerceve, logo, watermark, gradyan, golge, dekoratif obje |

Dikey siralama (tekil kart):
```
        KATEGORI ETIKETI          <- kucuk, buyuk harf, turuncu
                                     (genis bosluk)
         DEV BASLIK               <- lacivert, cok kalin, en buyuk oge
                                     (bosluk)
     Ingilizce ornek cumle        <- orta punto, lacivert, kalin
      (Turkce cevirisi)           <- kucuk punto, gri, parantezli
                                     (genis bosluk)
          CTA satiri              <- orta punto, lacivert, kalin
```

---

## Ek B — Format iskeletleri

### 1. Seviye testi — 8 slayt (`seviye-testi/a1/` … `b2/`)
| # | Icerik |
|---|---|
| 1 | Kapak: `A1 • INGILIZCE TESTI` / `BU A1 TESTINI GECEBILIR MISIN?` / `5 soru • 1 dakika` / `BASLAMAK ICIN KAYDIR →` |
| 2-6 | Soru: etiket + `SORU 01 / 05` / bosluklu cumle (`I ___ a student.`) / kutulu siklar `A) am` `B) is` `C) are` / `Cevabini sec.` |
| 7 | **Cevap anahtari** (→ mai): `CEVAP ANAHTARI` + 5 madde (`01 — A) am` + tek satir Turkce aciklama, aralarinda ince turuncu ayrac) + `Kac dogrun var?` |
| 8 | Skor yorumu: `SONUCUN` + `5/5`, `4/5`, `3/5`, `0-2/5` satirlari + `Bu kisa bir pratik testidir, resmi bir CEFR degerlendirmesi degildir.` + `Skorun ne? Asagiya yorum yap ⬇` |

### 2. Durumsal Ingilizce — seri, 5 slayt (`hikayeli/otel/`, `hikayeli/havaalaninda/`)
| # | Icerik |
|---|---|
| 1 | Kapak: `DURUMSAL INGILIZCE` / `OTELDE HAYAT KURTARAN CUMLELER` / `Check-in yapmak icin kaydir →` |
| 2-4 | Cumle karti: etiket / `I HAVE A RESERVATION` / tam cumle / `(Turkce cevirisi)` / gecis CTA'si (`Odaya cikalim... Kaydir →`) |
| 5 | Kapanis: son cumle + `Seyahat edeceklere gonder` |

### 3. Durumsal Ingilizce — tekil kart (`durumsal/<konu>/`)
`DURUMSAL INGILIZCE` / `ON THE SIDE` / `Can I have the sauce on the side?` / `(Sosu yaninda alabilir miyim?)` / `Daha fazla kelime icin begen ⬇`

### 4. Gunun Phrasal Verb'u (`phrasal/<verb>/`)
`GUNUN PHRASAL VERB'U` / `FIGURE OUT` / `To understand or solve something.` / ornek cumle / `(Turkce cevirisi)` / `Senin ornek cumlen nedir? 🥰`

### 5. Sik Karistirilanlar (`karistirilan/<x>-vs-<y>/`)
`SIK KARISTIRILANLAR` / `MAKE vs DO` / `MAKE: Ortaya cikarmak` + `Make a new Flutter app.` / `DO: Eylemi yapmak` + `Do some coding today.` / `Bu gonderiyi kaydet ⬇`

---

## Ek C — ASCII donusum  ⛔ EMEKLI (2026-08-20)

Bu bolum kartlarin metnini bir goruntu modeli yazarken vardi: model
diyakritigi bozdugu icin metin once ASCII'ye cevriliyordu. **Artik gecerli
degil.** Metin `marka/kart_bas.ps1` ile gercek fontla basiliyor; `ç ğ ı ö ş ü
İ` oldugu gibi yaziliyor.

Kuralin kendi bedeli de vardi: ASCII'de anlamsizlasan kelimeler cikiyordu
(`ÖLÜ` → `OLU`). Iki sorun da birlikte kapandi.

Donusum tablosu tek yerde hala kullaniliyor: `metin_denetle.py`, caption'lardan
sozluk kurarken kelimeleri ASCII'ye katliyor ki `lazim` ile `lazım`i
eslestirebilsin. Yani ayni tablo artik diyakritigi **silmek** icin degil,
**eksigini bulmak** icin var.

Arsivdeki 60 gorsel ASCII kalmaya devam ediyor; gecis kademeli
(`HATA-RAPORU.md` §5).

## Ek D — Bilinen tuzaklar

| Tuzak | Sonuc | Kacinma |
|---|---|---|
| **Shell state korunmuyor** | `$env:FAL_KEY` bos gider, 403 "unregistered caller" | Her komutun basinda `.env` yukle |
| **`Invoke-RestMethod` PS 5.1'de patliyor** | `NullReferenceException`, hicbir ipucu yok | `curl.exe` + `--data-binary "@dosya"` |
| **BOM'suz `.ps1`** | PS 5.1 dosyayi ANSI okur; UTF-8 `—` -> `â€”` olur ve `”` tirnak sayilip dize erken kapanir, anlamsiz parser hatasi | `.ps1` dosyalarini **UTF-8 BOM ile** kaydet |
| **fal status URL'i tam endpoint yolu degil** | HTTP 405, bos govde, sonsuz polling | Submit yanitindaki `status_url` / `response_url`'i kullan |
| **`gemini-3.1-pro-preview` ucretsiz katmanda kotasi 0** | 429 | `gemini-3.6-flash` kullan veya faturalandirmayi ac |
| **Uretim ~35 sn, arac timeout'u 2 dk** | Karuselde timeout | Her slayti ayri PowerShell komutunda uret |
| mai-image-2.5-pro'da 4:5 yok | Kare cikti, karuselde kirpma (`seviye-testi/a1/7.png` 1024×1024) | 3:4 uret + 80px simetrik kirp |
| seedream custom boyut limiti | 400 hatasi | Toplam piksel 3.69 MP – 16.78 MP arasi kalsin; 1920×2400 guvenli |
| Turkce diyakritik | `gónderiyi`, `değidlir` | ~~ASCII-only~~ → metni yerelde bas (`marka/kart_bas.ps1`) |
| Kucuk puntoda yogun metin | `conoditional`, `dogrune` | ~~mai kullan~~ → metni yerelde bas; punto ne olursa olsun harf bozulmaz |
| Gemini metni "duzeltir" | Diyakritik geri gelir, cumle degisir | Kart metni artik prompta girmiyor; Gemini yalnizca gorsel yon icin |
| mai `fiili` kelimesini basamiyor | `fili` / `fill` cikiyor, ust uste 2 denemede duzelmedi | Kelimeyi cumleden cikar. `"I" oznesi ile "am" yardimci fiili kullanilir` → `"I" oznesi her zaman "am" ile kullanilir`. Ayni promptu tekrar gondermek ise yaramiyor, metni kisaltmak yariyor |
| mai 3:4'te 768×1024 donuyor | Kaynak cozunurluk dusuk, 1920'ye olceklerken 2.5x buyutme | Kacinilmaz — mai'de cozunurluk parametresi yok. IG zaten 1080'e indirdigi icin pratikte sorun cikarmiyor |
| `.env` public repoda | Anahtar sizinti | `.gitignore`'da `.env`; commit oncesi `git status` kontrolu |

## Ek E — Dogrulanmis API kunyesi

2026-08-11'de canli olarak dogrulandi (break down dry-run).

| | |
|---|---|
| Gemini model (ucretsiz) | `gemini-3.6-flash` ✓ calisiyor |
| Gemini model (ucretli) | `gemini-3.1-pro-preview` — free tier kotasi 0, 429 doner |
| Gemini endpoint | `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent` |
| Gemini auth | header `x-goog-api-key: $GEMINI_API_KEY` |
| fal ana model | `fal-ai/bytedance/seedream/v5/lite/text-to-image` ✓ |
| fal yedek model | `microsoft/mai-image-2.5-pro` |
| fal submit | `POST https://queue.fal.run/fal-ai/bytedance/seedream/v5/lite/text-to-image` |
| fal durum | submit yanitindaki `status_url` → `https://queue.fal.run/fal-ai/bytedance/requests/{id}/status` |
| fal sonuc | submit yanitindaki `response_url` → `https://queue.fal.run/fal-ai/bytedance/requests/{id}` |
| fal auth | header `Authorization: Key $FAL_KEY` |
| seedream uretim suresi | ~35 sn (`metrics.inference_time`) |
