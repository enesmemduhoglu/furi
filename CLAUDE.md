# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Bu repo bir Instagram İngilizce öğrenme sayfasının (`@furkanteacherteaching`)
içerik deposu. Kod ikincil: asıl varlık `<format>/<slug>/` klasörlerindeki
postlar. Repo public — `.env` asla commit edilmez, prompt'a girmez, log'a yazılmaz.

## Zorunlu okumalar

| Dosya | Ne anlatır |
|---|---|
| `WORKFLOW.md` | Post üretim akışının tamamı, 8 faz. `insta-ingilizce` skill'i buraya işaret eder. |
| `marka/README.md` | `kart.json` şeması, öğe türleri, kanonik kategori etiketleri, marka renkleri |
| `otomasyon/README.md` | `durum.json` / `yayinlananlar.json` alan alan |
| `TODOS.md` | Açık işler + **kapanmış kararların gerekçeleri**. Bir kuralı değiştirmeden önce buraya bak. |
| `HATA-RAPORU.md` | Arşivdeki bilinen görsel kusurların defteri |

## Mimarinin iki temel kararı

**1. Kart metni bir görüntü modelinden geçmez.** Postun metni `kart.json`'da
veri olarak durur; `marka/kart_bas.ps1` harfleri gerçek fontla basar. 2026-08-20
öncesi metni seedream/mai "çiziyordu" ve yazım hatası üretiyordu
(`conoditional`, `alablir`, `KITAP vs GERCEX` — hepsi `HATA-RAPORU.md`'de).
Sonuçları:

- Yazım hatası ve eksik Türkçe karakter **mümkün değil**; çıktının metni girdinin metni
- ASCII-only kuralı **emekli**. Metin tam Türkçe yazılır (`ç ğ ı ö ş ü İ`)
- Üretim maliyeti sıfır, tekrar basmak bedava — düzeltmede tereddüt etme
- `caption.md`'nin "Alt text" bölümü kartı **birebir alıntılar**; kartla alt
  text arasındaki fark bir hatadır

**2. Yayının doğruluk kaynağı Instagram hesabı, bu repo değil.** Yayını
`content-approval-saas` yapıyor (onay maili → kullanıcı telefondan onaylar →
~11 sn'de yayın). Repo yayın anını görmüyor; `otomasyon/*.json` **türetilmiş**
bir defter ve düzenli olarak bayat. Bulut rutininin defter commit'leri bazen
`claude/*` dallarında kalıp main'e girmiyor.

> **Durum sorulduğunda deftere bakıp cevap verme.** Sırayla: `git fetch origin`
> → `esitle.py --kuru` → `esitle.py` → `aday_sec.py --durum`.
>
> `bekleyen` alanının dolu olması "onay bekliyor" demek **değildir** — o alan
> gönderim anında yazılır ve yayınla kapanmaz, kapatan `esitle.py`'dir.
> `esitle.py --kuru` çıktısındaki `bekleyen.sonuc` gerçeği verir. `esitle.py`
> kapatırken `son_yayin`i ve `bugun.yayinlanan`ı kendisi günceller, ama
> `sonraki` alanına dokunmaz: yayınlanmış bir slug orada kalırsa rutin onu
> tekrar sıraya koyar, elle temizle.
>
> **`yayin_zamani` bir postun yayın anıdır, eşitlemenin çalıştığı an değil** —
> kaynak SaaS'in `publishedAt` alanı (Instagram'dan gelen kayıtlarda IG'nin
> `timestamp`i). Kayıtta `zaman_kaynagi: "tespit"` ya da `not` alanında "tespit
> ani yazildi" görürsen o damga tahmindir, "dün mü bugün mü" sorusuna cevap
> olarak kullanma. 2026-08-26 öncesi SaaS yolundan düşen kayıtlar (24–26.08)
> bu yüzden bir gün ileri; geriye dönük düzeltilmediler.

## İki skill, iki ayrı iş

- **`insta-ingilizce`** (`WORKFLOW.md`) — post üretir. Onay noktaları: Faz 2
  (slayt metni) ve Faz 8 (commit). Commit'i kendin yapma, öner.
- **`insta-yayinla`** (`.claude/skills/insta-yayinla/`) — sıradakini seçip
  onaya gönderir, defteri tutar. Gözetimsiz çalışır: `AskUserQuestion`
  çağırmaz, yalnızca `otomasyon/*.json` commit eder, Instagram'a yazmaz.

## Komutlar

```powershell
# Kart bas (Hedef klasörüne 1.jpg … N.jpg). Basmadan önce metin_denetle.py'yi
# çağırır; denetim geçmezse hiçbir dosya yazmaz.
powershell -File marka\kart_bas.ps1 -Spec seviye-testi\a2\kart.json -Hedef seviye-testi\a2
```

```bash
python marka/metin_denetle.py <kart.json>   # tek kart
python marka/metin_denetle.py --tumu        # repodaki tüm kart.json'lar

S=.claude/skills/insta-yayinla/scripts
python $S/medya_yukle.py <mp4> --slug reels/<slug>  # video Blob'a, video.json yaz
python $S/esitle.py --kuru                  # defteri Instagram'la karşılaştır, yazma
python $S/esitle.py                         # farkları uygula
python $S/aday_sec.py --durum               # havuz istatistiği + tam yayın sırası
python $S/aday_sec.py --slug hikayeli/otel  # tek postun yayına hazırlık verisi
python $S/puanla.py --sema                  # puan dalları ve formül
python $S/puanla.py --yaz <slug> --kuru     # yazmadan doğrula
python $S/ig_token.py --kontrol             # token kalan süresi (kaynak: SaaS)
```

Env gerektiren script'ler (`esitle`, `saas_gonder`, `ig_*`) `.env` ister:
`GEMINI_API_KEY`, `FAL_KEY`, `FURI_SAAS_URL`, `FURI_CLIENT_ID`, `FURI_API_KEY`.
Shell state çağrılar arasında korunmadığı için her PowerShell komutunun başında
`.env` yükle (blok `WORKFLOW.md` başında).

## Windows tuzakları

- `python` çıktısı cp1252 — `İ` içeren metin `UnicodeEncodeError` ile çökertir.
  `PYTHONIOENCODING=utf-8` ver ya da script başında `sys.stdout.reconfigure`.
- `Invoke-RestMethod` PS 5.1'de bu API'lerde `NullReferenceException` fırlatıyor;
  `curl.exe` + `--data-binary "@dosya"` kullan.
- `.ps1` dosyaları **UTF-8 BOM** ile kaydedilmeli, yoksa PS 5.1 ANSI okur.
- Diğerleri: `WORKFLOW.md` > Ek D.

## Post klasörü

`<format>/<slug>/` = `1.jpg … N.jpg` + `caption.md` + `kart.json` + `puan.json`.
Formatlar: `seviye-testi` (7 slayt), `hikayeli` (seri), `dizi` (tekil kart),
`kitap-vs-gercek` (kapak + karşılaştırma kartları), `turkce-tuzagi` (kapak +
4 tuzak kartı, 2026-08-28), `cumleyi-tamamla` (soru destesi + cevap anahtarı,
2026-08-28), `zaman-farki` (kapak + aynı cümlenin 4 zamanı, 2026-09-05),
`phrasal` (tekil kart), `karistirilan` (tekil kart).
`<slug>` ASCII ve tireli.

> `zaman-farki` ile `turkce-tuzagi/zaman-kaymasi` aynı konuya bakar, aynı işi
> yapmaz: `zaman-kaymasi` yanlış cümleyi düzeltir, `zaman-farki`nin dört
> cümlesi de doğrudur ve iş anlamı ayırt etmektir. Karta yanlış cümle koymak
> yeni kategoriyi eskisinin kopyasına çevirir. İskelet: `WORKFLOW.md` Ek B §10.

> `durumsal` **emekli** — 2026-08-22'de havuzdaki tüm `durumsal` postları
> silindi, klasör de kaldırıldı. `WORKFLOW.md` Ek B'de iskeleti hâlâ duruyor
> ama yeni post açılmıyor; tekil kart ihtiyacı `dizi` ve `karistirilan` ile
> karşılanıyor.

**Deste formatlarının iskeleti sabit değil, karar noktası.** `cumleyi-tamamla`
kapaksız doğdu (`edatlar`, `karisan-fiiller`) ama kapaksızlık `ilgi_cekicilik`
dalında iki kez eksi yazdırdı; 2026-09-03'te üretilen `iki-dogru` ve `siksiz`
kapaklı. Aynı şekilde `kitap-vs-gercek` özet slaytıyla doğdu, sonra özet
kaldırıldı. İskeleti kopyalamadan önce o kategorinin son postunun
`puan.json`'undaki gerekçeleri oku — neyin neden değiştiği orada yazılı.

**`reels` formatı ayrı çalışır** (2026-08-29). Klasör `caption.md` + `puan.json` +
`video.json`; kart yok, `1.jpg` yok. **Video dosyası repoya asla commit edilmez** —
`.git` zaten 96 görselle 103MB, her Reel 10–70MB. Dosya Vercel Blob'a yükleniyor,
repoda yalnızca URL ve ölçümler kalıyor:

```powershell
# Videoyu Blob'a yükler ve reels/<slug>/video.json'i yazar (ffprobe gerekir).
python .claude\skills\insta-yayinla\scripts\medya_yukle.py <video.mp4> --slug reels/<slug>
python .claude\skills\insta-yayinla\scripts\medya_yukle.py <video.mp4> --slug reels/x --kuru
```

Video `subpipe` ile üretiliyor (`C:\Users\enesm\visual studio\subtitle-pipeline`);
o projenin caption aşaması furi akışında **kapalı** — caption'ı `insta-ingilizce`
ev stiliyle yazıyor.

**Reels otomatik sıraya girmez.** Günlük kota, puan sırası ve kategori rotasyonu
yalnızca karusel havuzunu yönetir (`aday_sec.otomatik_havuz`); Reel'ler elle
`saas_gonder.py --slug reels/...` ile gönderilir.

`puan.json` yayın sırasını **doğrudan** belirliyor: havuz en yüksek puandan
aşağıya yayınlanıyor. Kategorinin iki rolü var — eşit puanlıları ayırmak, ve
**en son yayınlanan kategoriyi bir tur bekletmek** (2026-08-28; puanın üstünde
bir kısıt, havuzun tepesindeki post da atlanır ve bir gün kayar). Sıranın tek
kaynağı `aday_sec.adaylari_sirala`; `--durum` çıktısındaki `bekleyen_kategori`
o an hangi kategorinin beklediğini söyler. Puansız post havuzun
sonuna düşer ve puanlı aday bitene kadar hiç yayınlanmaz — Faz 7'yi atlamak
postu fiilen rafa kaldırır. Puan postun **kalitesini** ölçer; görseldeki harf
hatası ve marka sapması puana girmez (defteri `HATA-RAPORU.md`).

## Yazım eşiği

Yazım ve diyakritik hatası **istisnasız** düzeltilir — yerel basımda bu bir
`kart.json` düzeltmesi, bedava. Tipografik ufaklıklar (tırnak yönü, ok glifi,
birkaç piksel kayma) bırakılır ve raporlanır.
