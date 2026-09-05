# marka/

Kart görselleri buradan basılır. **Metin bir görüntü modelinden geçmez.**

## Neden

2026-08-20'ye kadar kartların metnini seedream/mai yazıyordu ve harfleri
"çiziyordu". Sonuç `HATA-RAPORU.md`'de: `conoditional`, `değidlir`, `alablir`,
`edoceklere`, `KITAP vs GERCEX`. Aynı gün üç denemenin ikisinde harf hatası
çıktı (`olocak`, `Kaybet`). Difüzyon modeline "doğru yaz" demek istatistiksel
bir şey — kaç kez denersen dene garanti vermiyor, sadece denetimle yakalanıyor.

Bu yüzden iş bölündü:

| Katman | Kim yapıyor | Sonuç |
|---|---|---|
| Kâğıt dokusu | `zemin.jpg` (sabit) | Her kartta aynı; zemin rengi kaymıyor |
| Metin | `kart_bas.ps1` + gerçek font | Çıktının metni girdinin metni |

Yazım hatası ve eksik Türkçe karakter artık **mümkün değil**: harfler
çizilmiyor, basılıyor.

## Dosyalar

| Dosya | Ne |
|---|---|
| `zemin.jpg` | 1920×2400 kâğıt dokusu. Arşivdeki kartların metinsiz bantlarından çıkarıldı, dikey/yatay aynalanarak dolduruldu — yani arşivle birebir aynı kâğıt. |
| `kart_bas.ps1` | Kartı basar. Basmadan önce `metin_denetle.py`'yi çağırır, denetim geçmezse **basmaz**. |
| `metin_denetle.py` | Metni denetler. Tek başına da çalışır. |

## Kullanım

```powershell
powershell -File marka\kart_bas.ps1 -Spec dizi\tell-me-about-it\kart.json -Hedef dizi\tell-me-about-it
powershell -File marka\kart_bas.ps1 -Spec seviye-testi\a2\kart.json -Hedef seviye-testi\a2
```

| Parametre | Varsayılan | Ne |
|---|---|---|
| `-Spec` | — | Slayt tanımları (aşağıdaki şema) |
| `-Hedef` | — | Çıktı klasörü; `1.jpg … N.jpg` yazılır. Göreli yol repo köküne göre çözülür. |
| `-BaslikFont` | `Impact` | Başlık/anlam/CTA fontu |
| `-GovdeFont` | `Segoe UI` | Örnek cümle fontu |
| `-Kalite` | `94` | JPEG kalitesi |

Denetim tek başına:

```bash
python marka/metin_denetle.py dizi/tell-me-about-it/kart.json
python marka/metin_denetle.py --tumu
```

## `kart.json` şeması

Her postun klasöründe durur. **Postun metni artık veri** — diff'lenebilir,
grep'lenebilir, denetlenebilir. Görsel ondan türetilir.

```json
{
  "slug": "dizi/tell-me-about-it",
  "slaytlar": [
    { "ogeler": [
      { "tur": "etiket", "metin": "DİZİ İNGİLİZCESİ" },
      { "tur": "baslik", "metin": "TELL ME ABOUT IT" },
      { "tur": "anlam",  "metin": "Sorma! / Bana mı anlatıyorsun!" },
      { "tur": "ornek",  "metin": "Tell me about it, I've been there." },
      { "tur": "cta",    "metin": "Kaydet, lazım olacak ↓" }
    ] }
  ]
}
```

### Öğe türleri

Tekil kart (tek görsel: `dizi`, `phrasal`, `karistirilan`):

| `tur` | Rol | Renk | Punto | Sınır |
|---|---|---|---|---|
| `etiket` | Üst kategori etiketi | Turuncu `#EF4A18` | 46, harf aralıklı | 30 |
| `baslik` | Dev başlık | Lacivert `#0E2038` | ≤250, genişliğe oturur | 22 |
| `anlam` | Türkçe karşılık | Lacivert | ≤108 | 70 |
| `ornek` | Örnek cümle | Gri `#6B7280` | 58 | 60 |
| `ayrac` | İnce turuncu çizgi | Turuncu | 220×4 px | — |
| `cta` | Çağrı satırı | Lacivert | 74 | 45 |

Deste slaytları (seviye testi, cümleyi tamamla, hikâyeli, kitap-vs-gerçek,
türkçe tuzağı):

| `tur` | Rol | Renk | Punto | Sınır |
|---|---|---|---|---|
| `kapak` | Deste kapağının başlığı — cümle olduğu için **en fazla iki satır** | Lacivert | ≤250 | 40 |
| `sayac` | `SORU 01 / 05` | Gri | 54 | 16 |
| `soru` | Boşluklu soru cümlesi, gerekirse satıra bölünür | Lacivert, kalın | 92 | 70 |
| `sik` | Çerçeveli şık — 700 px kutu | Lacivert | 64 | 24 |
| `madde` | Cevap anahtarı satırı (`01 - B) saw`) | Lacivert | 92 | 30 |
| `aciklama` | Maddenin altındaki tek satırlık gerekçe | Gri | 52 | 85 |

Her iki biçimde de kullanılabilen iki öğe:

| `tur` | Rol | Renk | Punto | Sınır |
|---|---|---|---|---|
| `cumle` | Lacivert kalın cümle satırı — phrasal örneği, `KİTAP:`/`GERÇEK:` satırı, hikâyeli kartın İngilizce cümlesi. Sığmazsa satıra bölünür | Lacivert | 84 | 70 |
| `araetiket` | Kart ortasındaki turuncu ara başlık (`EXAMPLE SENTENCE`) — kanonik liste denetimine **girmez**, `etiket` ile karıştırma | Turuncu | 40, harf aralıklı | 24 |

`ayrac` deste slaytlarında `"en": 1400` ile tam genişlikte çizilir. Her öğeye
`"alt": <px>` verilebilir; o öğenin altındaki boşluğu türün varsayılanının
yerine geçirir (son şıkkın altındaki nefes böyle açılıyor).

Başlık **hiçbir zaman iki satıra kırılmaz**: sığmıyorsa punto küçülür. İki
satıra düşen başlık hiyerarşiyi bozuyordu (08-20 denemeleri). `kapak`, `soru`,
`aciklama` ve `cta` bölünebilir — onlar terim değil cümle. Bölünen metin
**dengelenir**: aynı satır sayısında en geniş satırı en dar tutan bölünme
seçilir, yani son satırda tek kelime kalmaz (`playing the piano.` → `She is
very good ___` / `playing the piano.`).

Blok sayfaya sığmıyorsa (beş maddelik cevap anahtarı) punto ve boşluklar
**birlikte** küçülür; taşma sessizce kırpılmış metin demek olurdu.

### Kategori etiketleri — kanonik liste

Bunlar sabittir; `metin_denetle.py` birebir eşleşme arar. Her kartın en
üstünde durdukları için tek harf sapması tüm feed'de göze çarpar.

```
DİZİ İNGİLİZCESİ
DURUMSAL İNGİLİZCE
GÜNÜN PHRASAL VERB'Ü
SIK KARIŞTIRILANLAR
KİTAP vs GERÇEK
TÜRKÇE TUZAĞI
CÜMLEYİ TAMAMLA
ZAMAN FARKI
A1 • İNGİLİZCE TESTİ          (A1/A2/B1/B2/C1/C2)
```

> Arşivdeki 60 görselde bu etiketler ASCII (`DIZI INGILIZCESI`). Yeni kartlar
> tam Türkçe basılıyor; geçiş kademeli.

### `"dil": "en"` — İngilizce öğeler

Sözlük Türkçe caption'lardan türediği için içine İngilizce kelimeler de
karışıyor. Büyük harf `I`/`İ` kuralı bu yüzden `STOP SAYING THIS` gibi
İngilizce bir başlıkta `SAYİNG` diye uydurma bulgu üretiyordu.

Dil **tahmin edilmiyor, veride yazıyor**: İngilizce bir öğeye `"dil": "en"`
eklenir, denetim o öğede diyakritik ve `I`/`İ` kontrolünü atlar. Uzunluk
sınırı ve kanonik etiket denetimi yine geçerlidir.

```json
{ "tur": "baslik", "metin": "I'M STARVING", "dil": "en" }
```

Kural: karta basılan her İngilizce satır (`baslik`, İngilizce `kapak`,
`KİTAP: ...` satırı, test soruları) işaretlenir. İşaretlemeyi unutmak sessiz
değil gürültülü bir hata — denetim yanlış bulgu verir, kart basılmaz.

Bir satırda hem İngilizce terim hem Türkçe karşılığı varsa (`REMIND:
Hatırlatmak`, `NATİVE GİBİ KONUŞ`) `"dil": "karisik"` kullanılır: büyük harf
`I`/`İ` kuralı atlanır, diyakritik denetimi Türkçe kelimeler için sürer.

## Denetim neyi yakalar

1. **Eksik diyakritik** — `lazim` → `lazım`, `icin` → `için`. Sözlük elle
   tutulmuyor: repodaki `caption.md` dosyalarından türetiliyor (caption'lar
   baştan beri düzgün Türkçe yazıldığı için doğal referans).
2. **Kanonik olmayan kategori etiketi.**
3. **Büyük harf `I`/`İ`** — Türkçe'de küçük `i`nin büyüğü `İ`dir (`TESTI` →
   `TESTİ`). Buna karşılık `KAYDIR` ve `ANAHTARI` doğrudur; küçükleri `ı`.
4. **Uzunluk sınırları** — `WORKFLOW.md` Faz 2.

### Üç bilinçli susturma

Üçü de aynı sebepten: **ASCII katlaması iki farklı doğruyu tek torbaya
atıyor.** Sözlük türetilmiş olduğu için hangisinin kastedildiğini bilemez.

1. **Soru eki** (`SORU_EKI`) — `mi/mı/mu/mü` + şahıs eki paradigmasının dört
   uyum varyantından ikisi (`misiniz`, `musunuz`) zaten diyakritiksizdir ve
   ikisi de doğrudur; hangisinin geleceğini önceki hecenin ünlüsü belirler.
   Katlama olmadan `durur musunuz` → `müsünüz` gibi uydurma bulgu çıkıyordu.

2. **Eşsesli çiftler** (`ESSESLI`) — katlanınca başka bir gerçek Türkçe
   kelimeye eşitlenen kelimeler: `onu`/`önü`, `ise`/`işe`, `iste`/`işte`.
   Sözlüğe çiftin yalnızca diyakritikli yarısı girdiği için doğru yazılmış
   diğer yarı "eksik diyakritik" diye işaretleniyordu. Liste bilerek dar —
   her giriş bir denetim körlüğü; yalnızca fiilen çarpışan çift ekleniyor.

3. **ASCII `I` içeren BÜYÜK harfli kelime sözlüğe girmez** (`sozluk_kur`).
   Sebep caption şemasının kendisi: "Alt text" bölümü kartı birebir alıntılar
   (`WORKFLOW.md` Faz 6), yani **her kart başlığı caption'a BÜYÜK harfle
   düşer**. Büyük harfte `ı`/`i` ayrımı geri getirilemediği için sözlük
   kelimeyi yanlış okuyup kartın kendisini suçlayabiliyordu: `SINIR` hem
   `sınır` hem `sinir` diye okunur, ikisi de gerçek kelimedir, ve düz okunuş
   sözlüğe girip **doğru yazılmış kartı** "SİNİR olmalı" diye işaretliyordu.
   2026-09-03'te üç kart birden böyle patladı (`hikayeli/sinir-kapisinda`
   `SINIR`+`KAPISINDA`, `kitap-vs-gercek/ofis-kaliplari` `ATMIYOR`) — üçü de
   kendi alt text'inin sözlüğe soktuğu kelimeyle. Eleme dar: yalnızca ASCII
   `I` içerenler düşer, `TESTİ` gibi zaten noktalı yazılmış büyük kelime
   sözlükte kalır (yoksa 3 numaralı kontrol kapsam kaybederdi).

> Ortak ilke: **sözlüğün içeriği değiştikçe denetimin sonucu değişmemeli.**
> Bir kartın basılıp basılmaması, başka bir postun caption'ında hangi
> kelimelerin geçtiğine bağlı olamaz.

Yakalayamadığı: sözlükte hiç geçmeyen bir kelimenin yanlış yazılması. Faz 2'de
metni okumanın yerini tutmaz, onu tamamlar.

## Font

`Impact` seçildi çünkü arşivdeki başlık kesimine en yakın olan o — geçiş
feed'de fark edilmiyor. `Franklin Gothic Heavy` daha geniş ve yumuşak bir
alternatif; `-BaslikFont` ile tek parametrede değişir. İkisi de Windows'ta
kurulu ve tam Türkçe destekli.
