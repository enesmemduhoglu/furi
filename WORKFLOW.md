---
name: insta-ingilizce
description: Instagram Ingilizce ogrenme sayfasi icin post uretir - fikir gorusmesi, slayt metni, kart gorsellerinin yerelde basilmasi, metin denetimi, caption ve puanlama. Kullanici post, karusel, slayt, gonderi, "ne paylassak" gibi seylerden bahsettiginde calisir.
---

<!-- Yukaridaki frontmatter bilerek ASCII: ~/.claude/skills/insta-ingilizce/SKILL.md
     ile birebir ayni olmali, yoksa skill eslesmesi iki surum arasinda ayrisir. -->

# Instagram İngilizce Sayfası — Post Üretim Akışı

Bu akış 8 fazdan oluşur (Faz 3 emekli). İki onay noktası var: **Faz 2 (slayt
metni)** ve **Faz 8 (commit)**.

> **Kart metni bir görüntü modelinden geçmez.** Harfler `marka/kart_bas.ps1`
> ile gerçek fontla basılıyor; yazım hatası ve eksik Türkçe karakter mümkün
> değil. Gerekçe: [Faz 4](#faz-4--görsel-üretimi).

## ⚠️ Her PowerShell çağrısında geçerli iki kural

1. **Shell state çağrılar arasında korunmuyor.** Değişkenler ve `$env:` değerleri bir sonraki komutta yok. Her PowerShell komutunun ilk satırı `.env` yüklemesi olmalı:
   ```powershell
   Get-Content "C:\Users\enesm\visual studio\furi1\.env" | Where-Object { $_ -match '^\s*[A-Za-z_]+\s*=' } | ForEach-Object { $k,$v = $_ -split '=',2; Set-Item -Path "env:$($k.Trim())" -Value $v.Trim() }
   ```
2. **`Invoke-RestMethod` kullanma.** PS 5.1'de bu API'lerde `NullReferenceException` fırlatıyor ve hata mesajı hiçbir şey söylemiyor. Bunun yerine `& "$env:SystemRoot\System32\curl.exe"` kullan; gövdeyi geçici bir dosyaya yazıp `--data-binary "@dosya"` ile gönder (UTF-8 ve tırnak sorunlarını bu çözüyor).

Üretim yeri: `C:\Users\enesm\visual studio\furi1\<format>\<konu-slug>\`
Referans arşiv: aynı repodaki `seviye-testi/`, `hikayeli/`, `phrasal/`, `karistirilan/`, `dizi/`, `kitap-vs-gercek/` klasörleri — marka sisteminin canlı örneği. Emin olmadığın bir tasarım kararında bunlardan birini `Read` ile aç ve bak.

**Klasör düzeni:** her post kendi klasöründe durur, klasör de formatının altında. Bir post = bir klasör = `1.jpg … N.jpg` + `caption.md` + `kart.json` (slayt metni, görselin kaynağı) + `puan.json`.

---

## Faz 0 — Kurulum kontrolü

Her oturumda ilk iş, anahtarların yüklü olduğunu doğrula:

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

Gemini modelini de doğrula — plan değişirse hangi modelin açık olduğu değişir:

```powershell
$m = (& "$env:SystemRoot\System32\curl.exe" -s "https://generativelanguage.googleapis.com/v1beta/models?pageSize=200" -H "x-goog-api-key: $env:GEMINI_API_KEY") -join "" | ConvertFrom-Json
$m.models | Where-Object { $_.supportedGenerationMethods -contains "generateContent" } | ForEach-Object { $_.name }
```

**Not (2026-08 itibarıyla):** `gemini-3.1-pro-preview` listede görünüyor ama ücretsiz katmanda kotası 0 — 429 döner. Ücretsiz katmanda çalışan: `gemini-3.6-flash` (varsayılan), `gemini-3.5-flash`, `gemini-3-flash-preview`. Prompt yazma işi için flash yeterli. Kullanıcı Google Cloud'da faturalandırmayı açarsa `gemini-3.1-pro-preview`'a geç.

Eksikse kullanıcıdan `furi1\.env` dosyasına eklemesini iste:

```
GEMINI_API_KEY=...
FAL_KEY=...
```

**Repo public.** `.env` asla commit edilmez, ekrana yazdırılmaz, prompt içine konmaz. `.gitignore`'da `.env` satırı olmalı — yoksa önce onu ekle.

---

## Faz 1 — Brief (konuşma)

Kullanıcı ya net bir konuyla gelir ("otelde check-in cümleleri yapalım") ya da fikir ister ("ne paylaşsak").

**Fikir isteniyorsa:** aşağıdaki formatların arşivde ne kadar kullanıldığına bak, 3 somut öneri sun. Her öneri: *format + başlık + neden ilgi çeker* (tek satır). Tekrar eden konu önerme — arşivdeki klasör adları zaten işlenmiş konular.

**Konu netse:** doğrudan format + slayt sayısı öner.

Sonra `AskUserQuestion` ile format ve slayt sayısını onaylat.

### 9 post formatı

| Format | Slayt | Arşiv örneği |
|---|---|---|
| Seviye testi (A1…C1) | 7 | `seviye-testi/a1/`, `seviye-testi/b2/` |
| Türkçe Tuzağı | 5 | `turkce-tuzagi/ceviri-refleksi/`, `.../kibarlik-tuzagi/` |
| Kitap vs Gerçek | 6 | `kitap-vs-gercek/ofis-kaliplari/`, `.../anlamadim/` |
| Cümleyi Tamamla | 6 | `cumleyi-tamamla/iki-dogru/`, `.../siksiz/` |
| Zaman Farkı | 5 | `zaman-farki/aradim/` |
| Durumsal İngilizce — seri | 5-6 | `hikayeli/havaalaninda/`, `hikayeli/is-gorusmesinde/` |
| Dizi İngilizcesi | 1 | `dizi/tell-me-about-it/`, `dizi/no-offense/` |
| Günün Phrasal Verb'ü | 1 | `phrasal/give-up/` |
| Sık Karıştırılanlar (X vs Y) | 1 | `karistirilan/lose-vs-loose/` |

> `durumsal` (tekil kart) **emekli** — 2026-08-22'de tüm postları silindi,
> klasör kaldırıldı. İskeleti Ek B'de tarihsel kayıt olarak duruyor.
>
> **Reels sıraya girmez** — `aday_sec` yalnızca karusel havuzunu yönetir,
> Reel'ler elle gönderilir. Ayrıntısı `CLAUDE.md`.

**Format seçerken puana bak.** `aday_sec.py --durum` kategori dağılımını verir;
hangi kategorinin geçmişte ne aldığı `<format>/<slug>/puan.json` dosyalarında.
2026-09-03 ölçümü: `ozgunluk` dalı **format tekrarıyla çürüyor** — aynı
iskeletle üretilen her yeni post öncekinden ~1 puan düşük özgünlük alıyor
(`cumleyi-tamamla` 6 → 5). Var olan bir formattan yeni post açacaksan
iskelette adı konmuş bir mekanik yenilik olsun; yoksa post havuzun dibine
düşer.

Slayt iskeletleri için → [Ek B](#ek-b--format-iskeletleri).

---

## Faz 2 — Slayt metni  ⛔ ONAY NOKTASI

Slayt slayt metni yaz ve **markdown tablo** halinde kullanıcıya göster. Onaylanmadan Faz 4'e geçme.

### Metin kuralları

1. **Tam Türkçe — zorunlu.** `ç ğ ı ö ş ü İ` olduğu gibi yazılır; ASCII'ye çevrilmez. *(2026-08-20 öncesi kural bunun tersiydi — sebep görsel modelinin diyakritiği bozmasıydı. Metin artık modelden geçmiyor: [Faz 4](#faz-4--görsel-üretimi) kartları gerçek fontla yerelde basıyor, yani harf bozulması mümkün değil.)* Metni `kart.json`'a yazıp `python marka/metin_denetle.py <kart.json>` çalıştır; eksik diyakritik ve kanonik olmayan kategori etiketi oradan döner.
2. İngilizce metin olduğu gibi yazılır. Öğesine `"dil": "en"` koy — denetim o zaman Türkçe diyakritik kurallarını o satıra uygulamaz.
3. Uzunluk sınırı: dev başlık ≤ 22 karakter · İngilizce cümle ≤ 60 karakter · Türkçe çeviri ≤ 70 karakter · CTA ≤ 45. `metin_denetle.py` bunları zorluyor. Sebep artık yazım hatası değil yerleşim: uzun başlıkta punto düşüyor ve hiyerarşi zayıflıyor.
4. Karuselin son slaytında mutlaka CTA olsun (kaydet / yorum yap / arkadaşına gönder).
5. Emoji sadece CTA satırında ve en fazla 1 tane.
6. Türkçe çeviri her zaman **parantez içinde** ve gri tonda.

### Tablo formatı

| # | Etiket | Başlık | İngilizce | Türkçe (parantez) | CTA |
|---|---|---|---|---|---|
| 1 | DURUMSAL İNGİLİZCE | OTELDE CHECK-IN | — | — | Kaydır → |
| 2 | DURUMSAL İNGİLİZCE | I HAVE A RESERVATION | I have a reservation under the name Demir. | (Demir adına bir rezervasyonum var.) | Odaya çıkalım... Kaydır → |

Onaylanan tablo `kart.json`'a geçer (şema: `marka/README.md`). Model sütunu
kalktı — kartları artık model üretmiyor.

---

## Faz 3 — Gemini ile görsel promptu üretimi  ⛔ EMEKLİ (2026-08-20)

Kart metni artık bir görüntü promptuna girmiyor; `kart.json`'dan doğruca
basılıyor (Faz 4). Bu fazın bütün işi — metni tırnak içinde birebir taşıtmak,
Gemini'nin diyakritik "düzeltmesini" engellemek — konusuz kaldı.

Aşağıdaki blok, ileride görsel bir öge (örneğin yeni bir zemin dokusu)
gerekirse referans olsun diye duruyor. **Sistem promptundaki ASCII şartı
geçersiz.**

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

## Faz 4 — Görsel üretimi

Kartlar **yerelde basılıyor**. Metin bir görüntü modelinden geçmiyor.

```powershell
powershell -File marka\kart_bas.ps1 -Spec dizi\tell-me-about-it\kart.json -Hedef dizi\tell-me-about-it
```

Şema, öge türleri, kanonik kategori etiketleri ve font seçimi: **`marka/README.md`**.

Betik basmadan önce `metin_denetle.py`'yi çalıştırır; denetim geçmezse **hiçbir
dosya yazmaz**. Yani "denetimi atlamak" diye bir ihtimal yok.

### Neden model değil

`HATA-RAPORU.md` bu sorunun defteri: `conoditional`, `değidlir`, `alablir`,
`edoceklere`, `KITAP vs GERCEX`. 2026-08-20'de tek bir kart üzerinde üç deneme
yapıldı, **ikisinde harf hatası çıktı** (`olocak`, `Kaybet`). Difüzyon modeline
"doğru yaz" demek istatistiksel bir şey; kaç kez denersen dene garanti vermiyor,
yalnızca denetimle yakalanıyor. Harfleri çizdirmek yerine basmak sorunu
kökünden kaldırıyor: çıktının metni girdinin metni.

Yan kazançlar: slayt başına üretim maliyeti sıfır, tekrar denemek bedava,
hizalama piksel piksel kontrolde, zemin her kartta aynı (arşivdeki "zemin rengi
kayıyor" sorunu kapandı) ve postun metni repoda `kart.json` olarak duruyor —
diff'lenebilir, grep'lenebilir.

### fal.ai — artık kart üretiminde kullanılmıyor

Aşağıdaki çağrılar **yeni bir zemin dokusu** gerekirse duruyor (`marka/zemin.jpg`
arşivden çıkarıldı, yenisi lazım olursa seedream'e metinsiz kâğıt üretimi
yaptırılır). Kart metni için kullanılmaz.

### seedream çağrısı

> ⛔ **Status/result URL'ini elle kurma.** fal'da submit adresi tam endpoint yolu (`fal-ai/bytedance/seedream/v5/lite/text-to-image`) ama status/result adresi sadece **uygulama kimliği** (`fal-ai/bytedance`). Tam yolu kullanırsan HTTP 405 + boş gövde döner ve polling sonsuza kadar boşa döner. Çözüm: submit yanıtındaki `status_url` ve `response_url` alanlarını olduğu gibi kullan.

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

> `image_size` custom değer limiti: toplam piksel 2560×1440 ile 4096×4096 arası olmalı. 1920×2400 = 4.6 MP ✓ geçerli.
>
> Üretim ~35 saniye sürüyor. PowerShell aracının varsayılan zaman aşımı 2 dakika — **çok slaytlı karuselde her slaytın üretimini ayrı komutta çalıştır**, hepsini tek komuta koyma yoksa timeout yersin.

### mai çağrısı + 4:5 düzeltmesi

`microsoft/mai-image-2.5-pro`'nun `aspect_ratio` enum'unda **4:5 yok** (`auto, 1:1, 4:3, 3:4, 16:9, 9:16, 3:2, 2:3`). Arşivdeki `seviye-testi/a1/7.png`, `a2/7.png`, `b1/7.png` bu yüzden 1024×1024 kare kalmış ve karuselde kırpılıyor. Çözüm: 3:4 üret, 1920 genişliğe ölçekle, üstten ve alttan 80'er piksel simetrik kırp.

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

Marka düzeni ortalanmış ve kenar boşlukları geniş olduğu için 80px kırpma içerik kaybettirmez.

### Dosya adlandırma

`furi1\<format>\<konu-slug>\1.jpg`, `2.jpg`, ... — arşivdeki `seviye-testi/a1/1.jpg`, `hikayeli/otel/1.jpg` kuralının aynısı.

`<format>` şu dokuzdan biri:

| `<format>` | Ne girer | Örnek |
|---|---|---|
| `seviye-testi` | CEFR testleri (kapak + 5 soru + cevap anahtarı) | `seviye-testi/b1/` |
| `turkce-tuzagi` | Türkçenin İngilizceye sızdığı hatalar (kapak + 4 tuzak) | `turkce-tuzagi/kibarlik-tuzagi/` |
| `kitap-vs-gercek` | Ders kitabı kalıbı vs gerçek kullanım | `kitap-vs-gercek/ofis-kaliplari/` |
| `cumleyi-tamamla` | Soru destesi + cevap anahtarı | `cumleyi-tamamla/iki-dogru/` |
| `zaman-farki` | Tek cümlenin dört zamanı, dördü de doğru (kapak + 4 zaman) | `zaman-farki/aradim/` |
| `hikayeli` | Çok slaytlı, bir sahneyi anlatan seriler | `hikayeli/havaalaninda/` |
| `dizi` | Dizi/altyazı kalıbı, tekil kart | `dizi/no-offense/` |
| `phrasal` | Günün Phrasal Verb'ü kartları | `phrasal/give-up/` |
| `karistirilan` | Sık Karıştırılanlar (X vs Y) kartları | `karistirilan/lose-vs-loose/` |

`reels` bunlardan ayrı çalışır (kart yok, `video.json` var) — `CLAUDE.md`.
`durumsal` emekli, klasörü kaldırıldı (Ek B §7).

`<konu-slug>` ASCII ve tireli olsun, konuyu tarif etsin: `give-up`, `lose-vs-loose`, `long-story-short`.

---

## Faz 5 — Yazım denetimi  ⚠️ atlanmaz

Üretilen **her** görseli `Read` ile aç ve kontrol et.

**Metin artık denetlenmiyor** — denetlenemez değil, *gerekmiyor*: harfler
`marka/kart_bas.ps1` tarafından gerçek fontla basılıyor, çıktının metni
`kart.json`'un metni. Metnin kendisi Faz 2'de ve `metin_denetle.py` ile
denetlendi. Geriye yerleşim kalıyor:

1. Boyut 1920×2400 mü?
2. Metin kenardan taşmış / kesilmiş / üst üste binmiş mi?
3. Başlık punto düşürülürken fazla küçülmüş mü? (uzun başlıklarda olur — metni kısalt)
4. Dikey denge bozulmuş mu? (çok satırlı kartlarda blok aşağı taşabilir)
5. Zemin dokusu düzgün bindi mi?

**Eşik (2026-08-20'de sertleştirildi):** yazım ve diyakritik hatası
**istisnasız** düzeltilir — yerel basımda bu zaten bir `kart.json` düzeltmesi,
bedava. Tipografik ufaklıklar (tırnak yönü, ok gliflerinin biçimi, birkaç
piksel hizalama kayması) bırakılır ve raporlanır.

> Önceki eşik "tek tük harf hatası bile yeniden üretim sebebi değil" idi; o
> kural yeniden üretimin **pahalı ve belirsiz** olduğu döneme aitti. Yerel
> basımda düzeltme bir metin değişikliği olduğu için tavizin sebebi kalmadı.

Denetim sonucunu kısa bir tabloyla özetle.

---

## Faz 6 — Caption

`furi1\<format>\<konu-slug>\caption.md` dosyasına yaz. Caption metin alanı,
görsel değil — burada da tam Türkçe kullan.

**Alt text kartın metnini birebir alıntılar.** Kart tam Türkçe basıldığı için
alt text'te ASCII kalıntısı (`DIZI INGILIZCESI`, `Kisacasi.`) bir hatadır;
alıntı ile kart aynı olmalı.

```markdown
## Açıklama
<2-4 satır. İlk satır kanca olsun. Konuyu ve kime yaradığını söyle.>

<Son satır: kaydetmeye / yorum yapmaya çağıran CTA>

## Hashtag
<10-15 etiket: genel İngilizce öğrenme + seviye/konu özel. Tek satır, boşluklu.>

## Alt text
1. <slayt 1 için erişilebilirlik metni>
2. ...
```

### Video (Reels) postunda

Şema aynı — `caption_ayristir` medyadan bağımsız çalışır. İki fark var:

1. **Alt text tek maddedir** (`1. ...`) ve **kart metnini alıntılamaz**;
   alıntılayacak kart yok. Görüntüyü betimler: kim, nerede, ekranda ne akıyor.
2. **Caption limiti 2000** (SaaS'ın limiti), 2200 değil. Video dalı bunu baştan
   zorluyor — 2000'i aşan bir caption gönderim anında elenir.

Caption'ı **her zaman burası yazar.** `subpipe`ın kendi caption üretici aşaması
furi akışında kapalı (`caption.enabled: false`): jenerik bir hook/body/cta
şeması üretiyordu ve sayfanın ev stiline oturmuyordu. subpipe genel amaçlı bir
araç olarak kalsın diye marka kuralları oraya taşınmadı, aşama susturuldu.

Video metnini yazarken kaynak, `subpipe`ın ürettiği çeviri dosyalarıdır:
`out/<video>.tr.srt` ve `out/<video>.en.srt`. Videoda **geçmeyen** bilgi uydurma.

---

## Faz 7 — Puanlama

Post bitti; şimdi ona puan ver. Puan `puan.json` olarak post klasörüne yazılır ve
içerikle **aynı commit'te** gider.

⚠ **Puan artık yayın sırasını doğrudan belirliyor:** havuz en yüksek puandan
aşağıya doğru yayınlanıyor. Yani buradaki puan "bir bilgi notu" değil, postun
kuyrukta nereye oturacağı. Puansız bırakılan post havuzun sonuna düşer ve
puanlı aday bitene kadar hiç yayınlanmaz — bu fazı atlamak postu rafa kaldırır.

```powershell
$S = ".claude\skills\insta-yayinla\scripts"
python $S\puanla.py --sema                          # dallar ve formul
python $S\puanla.py --yaz <kategori>/<slug> --kuru  # yazmadan dogrula
python $S\puanla.py --yaz <kategori>/<slug>         # JSON stdin'den
```

Beş dal, her biri 1-10 **ve zorunlu gerekçe**:

| Dal | Soru |
|---|---|
| `ilgi_cekicilik` | Kaydırmayı durdurur mu, kaydetmeye/paylaşmaya değer mi |
| `ogretici_deger` | Gerçekten bir şey öğretiyor mu, bilineni mi tekrarlıyor |
| `ozgunluk` | Önceki postlardan ve piyasadaki tipik içerikten ayrışıyor mu |
| `hedef_kitle` | Seviye, ton ve örnek seçimi takipçiye oturuyor mu |
| `gorsel_kalite` | Kompozisyon, hiyerarşi, okunabilirlik |

`toplam` script tarafından hesaplanır, elle yazma: **`ortalama(5 dal)`**.

### ⛔ Üretim kusurları puana GİRMEZ

Görseldeki harf hataları, diyakritik sızıntıları, imla ve şablon/marka sapmaları
puanlanmaz — onların defteri `HATA-RAPORU.md` ve tespit yeri Faz 5. Puanın
cevapladığı soru **"bu post iyi mi, ilgi çeker mi"**; "düzgün basılmış mı" değil.

Sınır `gorsel_kalite` dalında geçiyor:

- **Girer:** kırık başlık, kutuya sığmayan metin, bozuk dikey denge, birbiriyle
  yarışan iki odak, okunmayan kontrast — bunlar okunabilirliği bozar.
- **Girmez:** yanlış harf, eksik diyakritik, farklı font, kayan zemin rengi,
  başka bir CTA ikonu — bunlar üretim kusuru, kalite ölçüsü değil.

### Puanlarken

Üreten ile puanlayan aynı model; tek korumamız gerekçelerin kontrol edilebilir
olması. Gerekçe **boş sıfat olamaz** — "iyi", "güzel", "temiz" tek başına
yazılmaz; **neyin nerede** olduğu yazılır.

> ✅ "Başlık 'RUN OUT' dev puntoda, 'OF' çok daha küçük ikinci satırda; göz
> kalıbı tek birim olarak almıyor."
> ❌ "Görsel kalitesi düşük."

Karar geçmişi ve şema: `TODOS.md` > "Post puanlama sistemi",
`otomasyon/README.md` > "Post puanı".

---

## Faz 8 — Teslim

1. `SendUserFile` ile üretilen görselleri kullanıcıya göster (`display: "render"`).
2. Özet ver: kaç slayt, hangi model, kaç yeniden deneme, nereye kaydedildi.
3. **Commit'i sen yapma — öner ve onay iste.** Repo public; ne zaman yayınlanacağı kullanıcının kararı.

---
---

## Ek A — Marka sistemi

Arşivdeki 52 görselden çıkarılmış, değişmez sistem:

| Öge | Değer |
|---|---|
| Tuval | 1920 × 2400 px (4:5) |
| Zemin | Sıcak krem kâğıt `#FAF6E9`, üzerinde çok ince grain dokusu |
| Ana mürekkep | Koyu lacivert `#0E2038` |
| Vurgu | Turuncu-kırmızı `#EF4A18` — **sadece** üst kategori etiketinde ve ince ayraç çizgilerinde |
| İkincil metin | Orta gri `#6B7280` — çeviri ve açıklama satırlarında |
| Hizalama | Her şey ortalanmış |
| Başlık | Kalın geometrik grotesk, çok büyük punto; uzun başlıklar için sıkışık (condensed) kesim |
| Gövde | Temiz geometrik sans, orta ağırlık |
| Boşluk | Çok geniş — tuvalin üstünde ve altında büyük nefes alanı |
| Yasak | İllüstrasyon, fotoğraf, ikon, çerçeve, logo, watermark, gradyan, gölge, dekoratif obje |

Dikey sıralama (tekil kart):
```
        KATEGORİ ETİKETİ          <- kucuk, buyuk harf, turuncu
                                     (genis bosluk)
         DEV BAŞLIK               <- lacivert, cok kalin, en buyuk oge
                                     (bosluk)
     İngilizce örnek cümle        <- orta punto, lacivert, kalin
      (Türkçe çevirisi)           <- kucuk punto, gri, parantezli
                                     (genis bosluk)
          CTA satırı              <- orta punto, lacivert, kalin
```

---

## Ek B — Format iskeletleri

> Metinler **tam Türkçe** yazılır. Arşivdeki eski görsellerde bu satırlar ASCII
> görünür (`BASLAMAK ICIN KAYDIR`); o kural emekli, iskelet buradaki hâlidir.

### 1. Seviye testi — 7 slayt (`seviye-testi/a1/` … `b2/`)
| # | İçerik |
|---|---|
| 1 | Kapak: `A1 • İNGİLİZCE TESTİ` / `BU A1 TESTİNİ GEÇEBİLİR MİSİN?` / `5 soru • 1 dakika` / `BAŞLAMAK İÇİN KAYDIR →` |
| 2-6 | Soru: etiket + `SORU 01 / 05` / boşluklu cümle (`I ___ a student.`) / kutulu şıklar `A) am` `B) is` `C) are` / `Cevabını seç.` |
| 7 | **Cevap anahtarı**: `CEVAP ANAHTARI` + 5 madde (`01 - A) am` + tek satır Türkçe açıklama, aralarında ince turuncu ayraç) + `Kaç doğrun var? Yorumlara yaz ↓` |

> **Skor tablosu slaytı üretilmiyor** (2026-08-20 kararı): deste cevap
> anahtarıyla biter, yani 7 slayt. Beş destenin hepsi 2026-08-22'de bu hâle
> getirildi; arşivde artık 8 slaytlık test yok.

### 2. Türkçe Tuzağı — 5 slayt (`turkce-tuzagi/ceviri-refleksi/`, `.../kibarlik-tuzagi/`)
| # | İçerik |
|---|---|
| 1 | Kapak: `TÜRKÇE TUZAĞI` / `CÜMLEN DOĞRU TONUN KABA` / `Kibar olmak istiyorsun, emir veriyorsun.` / `Başlamak için kaydır →` |
| 2-5 | Tuzak kartı: etiket / başlık (`KAHVE İSTEMEK`) / turuncu ara etiket + yanlış cümle / turuncu ara etiket + doğru cümle / `(kuralı tek satırda)` / `Sırada: <sonraki başlık>` |

> **Özet slaytı yok** — bölüm 1'de vardı (`birebir-ceviri`, 8.2), bölüm 2'de
> kaldırıldı ve puan 8.6'ya çıktı: "beş slaytın dördü ders". Beş slaytın
> dördü ders kalsın.
>
> **Ara etiket çifti eksenin adıdır, sabit değil.** `YANLIŞ`/`DOĞRU` (gramer),
> `KABA`/`KİBAR` (ton), `ZAMAN YANLIŞ`/`ZAMAN DOĞRU` (zaman). Yeni bölüm yeni
> eksen demek — aynı çiftle üçüncü kez gelmek `ozgunluk` dalını düşürür.

### 3. Kitap vs Gerçek — 6 slayt (`kitap-vs-gercek/ofis-kaliplari/`, `.../anlamadim/`)
| # | İçerik |
|---|---|
| 1 | Kapak: `KİTAP vs GERÇEK` / `KİMSE BÖYLE MAİL YAZMAZ` / `Yanlış değil. Sadece otuz yıl geç.` / `Başlamak için kaydır →` |
| 2-6 | Karşılaştırma kartı: etiket / başlık (`ÖZÜR DİLEMEK`) / `KİTAP: I apologize for the delay.` / `GERÇEK: Sorry for the late reply.` / `(kuralı tek satırda)` / `Sırada: <sonraki başlık>` |

> **`KİTAP:` ve `GERÇEK:` satırları ≤ 36 karakter** tutulmalı, yoksa satır
> ikiye kırılır ve iki satır birbiriyle dengesizleşir. Kategorinin tek 5.0'lık
> `gorsel_kalite` puanı (`gunluk-kaliplar`) bu yüzdendi.
>
> Özet/kapanış slaytı **kullanılmıyor** (2026-09-03): deste beşinci ders
> kartıyla biter, tekrar eden bir kapanış kaydırmayı yavaşlatıyordu.

### 4. Cümleyi Tamamla — 6 slayt (`cumleyi-tamamla/iki-dogru/`, `.../siksiz/`)
| # | İçerik |
|---|---|
| 1 | Kapak: `CÜMLEYİ TAMAMLA` / `İKİSİ DE DOĞRU AMA AYNI DEĞİL` / kanca satırı / `Başlamak için kaydır →` |
| 2-5 | Soru: etiket + `SORU 01 / 04` + soru gövdesi + `Cevabını seç.` (son soruda `Cevaplar sırada →`) |
| 6 | **Cevap anahtarı**: `CEVAP ANAHTARI` + 4 madde (`01 - A) He stopped smoking.` + tek satır kural, aralarında ince turuncu ayraç) + `Kaç doğrun var? Yorumlara yaz ↓` |

> **Kapak zorunlu.** Format kapaksız doğdu (`edatlar`, `karisan-fiiller`) ve
> `ilgi_cekicilik` gerekçesinde iki kez eksi yazdı: "feed'de ilk gören kart
> çıplak bir soru, kanca cümlesi yok."
>
> **Soru mekaniği her destede değişmeli** — iskelet `seviye-testi` ile aynı
> olduğu için `ozgunluk` 6'dan 5'e düşmüştü. Denenmiş varyantlar: 4 şık
> (`edatlar`), **2 şık ve ikisi de doğru** (`iki-dogru` — soru "yanlışı ele"
> değil "anlam farkını gör"), **şık yok** (`siksiz` — `DURUM` bağlam satırı +
> boşluklu cümle + `İPUCU` Türkçe ipucu, okur cevabı kendi yazar).
>
> Şıklar kalkınca kart seyrekleşir: `siksiz` ilk basımda 1124 px'ti, bağlam
> satırı eklenerek 1262'ye çıkarıldı. Şıksız tasarımda blok yüksekliğine bak.

### 5. Durumsal İngilizce — seri, 5-6 slayt (`hikayeli/havaalaninda/`, `hikayeli/is-gorusmesinde/`)
| # | İçerik |
|---|---|
| 1 | Kapak: `DURUMSAL İNGİLİZCE` / `OTELDE HAYAT KURTARAN CÜMLELER` / `Check-in yapmak için kaydır →` |
| 2-5 | Cümle kartı: etiket / `I HAVE A RESERVATION` / tam cümle / `(Türkçe çevirisi)` / geçiş CTA'sı (`Odaya çıkalım... Kaydır →`) |
| 6 | **Kural slaytı**: `DÖRDÜNÜN ORTAK KURALI` / karşıt örnek (`I am hardworking.`) / doğru örnek (`I've been working here for five years.`) / `(Sıfat söyleme, kanıt söyle.)` / `İş arayan arkadaşına gönder ↓` |

> **Kural slaytı `ogretici_deger` tavanını kırar.** Arşivdeki ilk dört hikâyeli
> destesi son cümle + CTA ile bitiyordu ve hiçbiri o dalda 9 alamadı; gerekçe
> hep aynıydı: "ne kural var ne yanlış-doğru eşlemesi, ne söyleneceğini
> öğretiyor neden öyle söylendiğini değil." Kural slaytı eklenen iki deste
> (`is-gorusmesinde`, `sinir-kapisinda`) 8.8 aldı.
>
> **Sahnenin bahsi yüksek olmalı.** `otel` 7.0 aldı çünkü cümleleri konfor
> cümlesiydi (`extra towels`, `what time is breakfast`); `havaalaninda` 8.0
> aldı çünkü kayıp bagaj vardı. Kaybedilecek bir şey olan sahne seç.

### 6. Dizi İngilizcesi — tekil kart (`dizi/<kalip>/`)
`DİZİ İNGİLİZCESİ` / `NO OFFENSE` / `Alınma ama... / Kusura bakma ama...` / `No offense, but I don't think that'll work.` / `Sana en son kim dedi? ↓`

> **`anlam` satırı tek kelime olamaz.** Çift ifadeli (`Benim hatam! / Kusura
> bakma.`) ya da tam cümle olmalı; kısa `anlam` başlıkla aynı ağırlığa gelip
> hiyerarşiyi çökertiyor (`long-story-short` "Kısacası." → görsel 5,
> `suit-yourself` "Sen bilirsin." → görsel 6).
>
> **Türkçe çeviri satırı olmayan 5 öğeli kurulum** kategorinin en yüksek
> puanlısında var (`tell-me-about-it` 8.4); ferah kompozisyon puan getiriyor.

### 7. Durumsal İngilizce — tekil kart ⛔ EMEKLİ (`durumsal/<konu>/`)
`DURUMSAL İNGİLİZCE` / `ON THE SIDE` / `Can I have the sauce on the side?` / `(Sosu yanında verir misiniz?)` / `Daha fazla kelime için beğen ↓`

> 2026-08-22'de havuzdaki tüm `durumsal` postları silindi ve klasör kaldırıldı
> (puanları 5.20-6.40, havuzun en düşükleri). Yeni post açılmıyor; iskelet
> tarihsel kayıt olarak duruyor.

### 8. Günün Phrasal Verb'ü (`phrasal/<verb>/`)
`GÜNÜN PHRASAL VERB'Ü` / `FIGURE OUT` / `To understand or solve something.` / örnek cümle / `(Türkçe çevirisi)` / `Senin örnek cümlen nedir? ↓`

### 9. Sık Karıştırılanlar (`karistirilan/<x>-vs-<y>/`)
`SIK KARIŞTIRILANLAR` / `MAKE vs DO` / `MAKE: Ortaya çıkarmak` + `Make a new Flutter app.` / `DO: Eylemi yapmak` + `Do some coding today.` / `Bu gönderiyi kaydet ↓`

### 10. Zaman Farkı — 5 slayt (`zaman-farki/aradim/`, 2026-09-05)
| # | İçerik |
|---|---|
| 1 | Kapak: `ZAMAN FARKI` / `TEK CÜMLE DÖRT AYRI ANLAM` / omurga cümleyi adlandıran gri satır (`Aradım demenin dört yolu var, dördü ayrı.`) / `Başlamak için kaydır →` |
| 2-5 | Zaman kartı: etiket / **başlık = cümlenin o zamandaki hâli** (`I'VE BEEN CALLING HER`) / turuncu `PAST SIMPLE` gibi zaman adı / lacivert Türkçe anlam (`Sabahtan beri arayıp duruyorum.`) / `ayrac` / turuncu `NE ZAMAN` / gri kural satırı / `Sırada: <sonraki cümle>` |

> **Dört cümle de doğrudur.** Format `turkce-tuzagi`nin aynası değil: orada
> eksen `YANLIŞ`/`DOĞRU`, burada dördü de gramer olarak doğru ve iş **anlamı
> ayırt etmeye** kalıyor. Karta yanlış cümle koymak formatın sözünü bozar
> (`zaman-kaymasi` zaten o işi yapıyor).
>
> **Omurga tek fiildir ve dört kartta değişmez.** Kaydırma boyunca yalnızca
> zamanın taşıdığı kelime değişir (`I called her` → `I've called her` →
> `I've been calling her` → `I was calling her`); fark tipografik olarak da
> görünür. Fiil seçerken ölçü: dört hâli **Türkçede tek kelimeye** çöküyor mu.
> Çökmüyorsa deste konusuz kalır.
>
> **Başlık uzunluğuna bak.** Başlık hiçbir zaman bölünmez, sığmazsa punto
> düşer; perfect continuous hâli ötekilerden ~5 karakter uzun olduğu için
> deste içinde punto kayması buradan gelir. Aralık 12-21 karakterde tutuldu.
> Daralması gerekirse nesne o karttan düşürülür (`I'VE BEEN CALLING`).
>
> **Özet/kural slaytı yok.** Kural zaten dört kartın yan yana durmasında;
> `turkce-tuzagi` ve `kitap-vs-gercek`te özet slaytı kaldırıldığında puan
> yükselmişti. Beş slaytın dördü ders.

---

## Ek C — ASCII dönüşüm  ⛔ EMEKLİ (2026-08-20)

Bu bölüm kartların metnini bir görüntü modeli yazarken vardı: model
diyakritiği bozduğu için metin önce ASCII'ye çevriliyordu. **Artık geçerli
değil.** Metin `marka/kart_bas.ps1` ile gerçek fontla basılıyor; `ç ğ ı ö ş ü
İ` olduğu gibi yazılıyor.

Kuralın kendi bedeli de vardı: ASCII'de anlamsızlaşan kelimeler çıkıyordu
(`ÖLÜ` → `OLU`). İki sorun da birlikte kapandı.

Dönüşüm tablosu tek yerde hâlâ kullanılıyor: `metin_denetle.py`, caption'lardan
sözlük kurarken kelimeleri ASCII'ye katlıyor ki `lazim` ile `lazım`ı
eşleştirebilsin. Yani aynı tablo artık diyakritiği **silmek** için değil,
**eksiğini bulmak** için var.

Arşivdeki eski görseller ASCII kalmaya devam ediyor; geçiş kademeli
(`HATA-RAPORU.md` §5).

## Ek D — Bilinen tuzaklar

| Tuzak | Sonuç | Kaçınma |
|---|---|---|
| **Shell state korunmuyor** | `$env:FAL_KEY` boş gider, 403 "unregistered caller" | Her komutun başında `.env` yükle |
| **`Invoke-RestMethod` PS 5.1'de patlıyor** | `NullReferenceException`, hiçbir ipucu yok | `curl.exe` + `--data-binary "@dosya"` |
| **BOM'suz `.ps1`** | PS 5.1 dosyayı ANSI okur; UTF-8 `—` -> `â€”` olur ve `”` tırnak sayılıp dize erken kapanır, anlamsız parser hatası | `.ps1` dosyalarını **UTF-8 BOM ile** kaydet |
| **fal status URL'i tam endpoint yolu değil** | HTTP 405, boş gövde, sonsuz polling | Submit yanıtındaki `status_url` / `response_url`'i kullan |
| **`gemini-3.1-pro-preview` ücretsiz katmanda kotası 0** | 429 | `gemini-3.6-flash` kullan veya faturalandırmayı aç |
| **Üretim ~35 sn, araç timeout'u 2 dk** | Karuselde timeout | Her slaytı ayrı PowerShell komutunda üret |
| mai-image-2.5-pro'da 4:5 yok | Kare çıktı, karuselde kırpma (`seviye-testi/a1/7.png` 1024×1024) | 3:4 üret + 80px simetrik kırp |
| seedream custom boyut limiti | 400 hatası | Toplam piksel 3.69 MP – 16.78 MP arası kalsın; 1920×2400 güvenli |
| Türkçe diyakritik | `gónderiyi`, `değidlir` | ~~ASCII-only~~ → metni yerelde bas (`marka/kart_bas.ps1`) |
| Küçük puntoda yoğun metin | `conoditional`, `dogrune` | ~~mai kullan~~ → metni yerelde bas; punto ne olursa olsun harf bozulmaz |
| Gemini metni "düzeltir" | Diyakritik geri gelir, cümle değişir | Kart metni artık prompta girmiyor; Gemini yalnızca görsel yön için |
| mai `fiili` kelimesini basamıyor | `fili` / `fill` çıkıyor, üst üste 2 denemede düzelmedi | Kelimeyi cümleden çıkar. `"I" oznesi ile "am" yardimci fiili kullanilir` → `"I" oznesi her zaman "am" ile kullanilir`. Aynı promptu tekrar göndermek işe yaramıyor, metni kısaltmak yarıyor |
| mai 3:4'te 768×1024 dönüyor | Kaynak çözünürlük düşük, 1920'ye ölçeklerken 2.5x büyütme | Kaçınılmaz — mai'de çözünürlük parametresi yok. IG zaten 1080'e indirdiği için pratikte sorun çıkarmıyor |
| Windows'ta `python` çıktısı cp1252 | `İ` içeren bulgu metni `UnicodeEncodeError` ile betiği çökertir | Betiğin başında `sys.stdout.reconfigure(encoding="utf-8")` (bkz. `metin_denetle.py`) |
| `.env` public repoda | Anahtar sızıntı | `.gitignore`'da `.env`; commit öncesi `git status` kontrolü |

## Ek E — Doğrulanmış API künyesi

2026-08-11'de canlı olarak doğrulandı (break down dry-run).

| | |
|---|---|
| Gemini model (ücretsiz) | `gemini-3.6-flash` ✓ çalışıyor |
| Gemini model (ücretli) | `gemini-3.1-pro-preview` — free tier kotası 0, 429 döner |
| Gemini endpoint | `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent` |
| Gemini auth | header `x-goog-api-key: $GEMINI_API_KEY` |
| fal ana model | `fal-ai/bytedance/seedream/v5/lite/text-to-image` ✓ |
| fal yedek model | `microsoft/mai-image-2.5-pro` |
| fal submit | `POST https://queue.fal.run/fal-ai/bytedance/seedream/v5/lite/text-to-image` |
| fal durum | submit yanıtındaki `status_url` → `https://queue.fal.run/fal-ai/bytedance/requests/{id}/status` |
| fal sonuç | submit yanıtındaki `response_url` → `https://queue.fal.run/fal-ai/bytedance/requests/{id}` |
| fal auth | header `Authorization: Key $FAL_KEY` |
| seedream üretim süresi | ~35 sn (`metrics.inference_time`) |
