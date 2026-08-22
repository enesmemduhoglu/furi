# Arşivdeki bilinen hatalar

2026-08-11'de repodaki **60 görselin tamamı** tek tek okunarak çıkarıldı. Hiçbiri düzeltilmedi — bu dosya, hangi kartın yeniden üretilmesi gerektiğine sonra karar verebilmek için tutuluyor.

Yeniden üretim yapılacaksa: WORKFLOW.md Faz 4–5.

> **Alıntı kuralı:** tablolardaki "Hatalı" ve "Doğrusu" sütunları görseldeki metni **birebir** aktarır. O görseller ASCII-Türkçe üretildiği için sütunlarda ASCII yazım görmek normaldir; düz yazı ise tam Türkçe.

**Çözülenler üstü çizili işaretlenir.** 2026-08-11: dört cevap anahtarının **hepsi** yeniden üretildi (mai 3:4 → 1920×2560 ölçek → 80px kırp → 1920×2400). Üç kare dosya (`a1/7.png`, `a2/7.png`, `b1/7.png`) gitti; artık **repodaki 60 görselin tamamı 1920×2400**. Aynı turda `fill`, `fil`, `filin`, `conoditional`, `Kac dogrune var?` hataları da düzeldi.

2026-08-11, ikinci tur: kullanıcının `-` ile işaretlemediği **5 görsel** yeniden üretildi — `karistirilan/lose-vs-loose`, `karistirilan/effect-vs-affect`, `seviye-testi/{a2,b1,b2}/8.jpg`. Hedeflenen hataların **tamamı** düzeldi.

**Eşik notu:** Küçük ve göze batmayan kusurlar (baş harf büyük/küçük, tırnak yönü, `•` yerine `-`, tek tük harf hatası) için yeniden üretim yapılmıyor. Aşağıda bunlar listelense de bırakılmaları bilinçli bir karardır. Satır sonundaki `-` işareti "bu satır geçildi" demektir.

**Model notu:** `fiil` / `fiili` kelimesini iki model de güvenilir basmıyor (`fil`, `fill`, `fili` çıkıyor). Aynı şey `alabilir` için de geçerli — arşivde 3, yeni üretimde 1 kez `alablir` oldu. Çözüm promptu sıkılaştırmak değil, kelimeyi değiştirmek: `fiil` → `verb` / `past participle`, `(Fiil)` → `(Eylem)`, `alabilir miyim` → `verir misiniz`.

2026-08-18, **geriye dönük puanlama turu**: havuzdaki 27 yayınlanmamış postun
tamamı puanlanırken (TODOS.md > Post puanlama sistemi) üç yeni hata çıktı ve
aşağıdaki tabloya eklendi — ikisi `hikayeli/takside/6.jpg`'de (`odeyeblir`,
`edoceklere`), biri `kitap-vs-gercek/gunluk-kaliplar/3.jpg`'de. Sonuncusu
diğerlerinden ağır: hata **marka etiketinin kendisinde** (`KITAP vs GERCEX`).
Her üçü de bu dosyanın ilk turundan sonra üretilmiş destelerde; yani 08-11
denetimi onları hiç görmedi.

2026-08-19, **`karistirilan/effect-vs-affect/1.jpg` CTA düzeltmesi**: post 12:07
rutininde onaya gönderildikten sonra kullanıcı satırdaki iki hatayı bildirdi
(`takipte kali` ve sedilyalı `için`). Görsel **yeniden üretilmedi** — bulut
oturumunda `FAL_KEY` tanımlı değil, `.env` yalnızca yerelde duruyor. Bunun
yerine iki hata da **piksel silme** ile kapatıldı: son `i` harfi ve `ç`
sedilyası çevreden örneklenen kâğıt dokusuyla örtüldü, tüylü maskeyle
harmanlandı. Yeni harf çizilmediği için font, punto ve marka sistemi birebir
korundu; satır 9 px sola kaydı (1920 px tuvalde gözle seçilmiyor).

> **Yöntem notu:** bu yol yalnızca düzeltme *silme* olduğunda çalışır (fazla
> harf, sızmış diyakritik). Eksik ya da yanlış harf için yeni glif çizmek
> gerekir ve arşivdeki font serbest bir eşdeğeriyle tam eşleşmiyor — o durumda
> WORKFLOW.md Faz 4'e dönüp görseli yeniden üretmek gerekiyor.
>
> **Ek (08-20):** üçüncü bir yol daha var — *aynı görselden glif ödünç almak*.
> `dizi/tell-me-about-it/1.jpg`'de CTA `Kaybet` çıktı (`Kaydet` olacaktı). `d`,
> geometrik sans'ta `b`'nin yatay aynası olduğu için `b` glifinin kutusu
> (x=639..686, antialias dahil, iki yanında 4'er piksel boşluk) yerinde
> aynalandı. Font, punto, ağırlık ve konum birebir korundu; yeni glif
> çizilmedi. Ayna simetrisi olan harf çiftlerinde (b/d, p/q) çalışır.

2026-08-20, **Türkçe diyakritik denemesi — `dizi/tell-me-about-it/1.jpg`**:
§5'teki "bazı diyakritikler hayatta kalıyor" gözlemi ilk kez kontrollü olarak
sınandı. Kart tam Türkçe metinle yeniden üretildi (`Bana mi anlatiyorsun` →
`Bana mı anlatıyorsun`, `lazim` → `lazım`); risk yüzeyi üç adet `ı` (U+0131),
başka diyakritik yok. Üst kategori etiketi bilinçli olarak ASCII bırakıldı
(`DIZI INGILIZCESI`) — 60 görselde sabit olduğu için marka parçası.

**Sonuç: seedream üçünü de doğru bastı, üç denemede de.** `ı` hiçbir denemede
`i`'ye dönmedi, nokta eklenmedi. Yani `ı` model için sorun değil; §5'teki
"rastgele düşüyor" gözlemi en azından bu harf için geçerli değil. `ş ğ ü ö`
aynı şekilde sınanmadı.

Denemelerde çıkan kusurlar diyakritikle değil, her zamanki harf hatasıyla ilgili:

| Deneme | Tipografi | Metin |
|---|---|---|
| 1 | Başlık ince kesim, anlam satırı iki satıra kırıldı | Kusursuz |
| 2 | Ağırlık doğru, başlık iki satıra kırıldı | `olocak` (olacak) |
| 3 | Marka kesimi birebir, tek satır başlık | `Kaybet` (Kaydet) → glif aynalamayla düzeltildi |

Yayına giren: 3. deneme + aynalama. mai'ye hiç gerek kalmadı.

2026-08-20, **`seviye-testi/a2` yerel basıma geçti**: destenin metni
`seviye-testi/a2/kart.json`'a girildi ve yedi slayt `marka/kart_bas.ps1` ile
yeniden basıldı. Harfleri artık gerçek font basıyor, yani bu destede yazım
hatası ve eksik diyakritik **mümkün değil**. Kapanan kayıtlar:

- §1 `a2/8.jpg` > `dara` — slayt yayından kaldırıldı (skor tablosu artık
  üretilmiyor), kalan altı slayt + cevap anahtarı yeniden basıldı
- §4 "şık kutuları slayttan slayta farklı genişlikte" — kutu genişliği artık
  sabit (700 px), yedi slaytta aynı
- §4 "etiket rengi kayıyor" (a2'de 3. slayttan itibaren laciverde dönüyordu) —
  etiket tek yerden basılıyor, kaymıyor
- §5 ASCII kalıntıları (`BASLAMAK IÇIN KAYDIR`, `Cevabini sec.`, cevap
  anahtarının tamamı) — deste baştan sona tam Türkçe

Aynı turda `marka/metin_denetle.py`'de üç yanlış alarm çıktı ve düzeltildi:
büyük harfli `ANAHTARI`/`KAYDIR` "diyakritiksiz" sayılıyordu (Türkçede `ı`nın
büyüğü zaten `I`), `iyi` ise caption'lardaki `İyi`nin Python `.lower()` çıktısı
(`i` + U+0307) yüzünden bozuk bir sözlük girdisiyle eşleşiyordu. Denetim artık
büyük harfli kelimeyi adayların **Türkçe büyük hali** ile karşılaştırıyor;
`GECEBILIR` -> `GEÇEBİLİR` gibi gerçek hataları yakalamaya devam ediyor.

2026-08-22, **puanı 7.0'ın altındaki 11 post silindi**: `durumsal`ın tamamı
(5), `phrasal`dan 5 (`break-down`, `put-off`, `run-out-of`, `come-up-with`,
`figure-out`) ve `karistirilan/make-vs-do`. Havuzun yerel basıma geçmemiş kısmı
tam olarak bu 11 postu kapsıyordu, yani **repoda artık görüntü modelinin metin
yazdığı hiçbir kart kalmadı**. Bu bölümdeki açık kayıtların büyük kısmı bu
yüzden konusuz kaldı; altları çizilerek işaretlendi.

2026-08-22, **`a1`, `b1`, `b2` skor slaytları silindi ve desteler yerel basıma
geçti**: 2026-08-20'de alınan "sonuç slaytı üretilmiyor" kararı bu üç destede
uygulanmamıştı. `8.jpg` dosyaları silindi, 7. slaytın CTA'sı `Sonucun için
kaydır →` yerine `Kaç doğrun var? Yorumlara yaz ↓` oldu (deste artık orada
bitiyor) ve üç deste `marka/kart_bas.ps1` ile yeniden basıldı. Kapanan kayıtlar
§1'de ve §2'de üstü çizili işaretlendi — hepsi silinen slayttaydı.

Aynı turda `karistirilan/borrow-vs-lend` repodan silindi (2026-08-18'de onayda
reddedilmişti); postun görselindeki kayıt kalmadı.

2026-08-11, `hikayeli/doktorda` üretimi: kapakta `CUMLELERS` ve 5. slaytta `alablir` + etiketin tırnak içine alınması çıktı, ikisi de birer tekrarla düzeldi. Kalan tek kusur aşağıda.

| Dosya | Hatalı | Doğrusu |
|---|---|---|
| `hikayeli/doktorda/5.jpg` | `Yurt disiina` | Yurt disina | -

---

## 1. Anlam bozan yazım hataları — en yüksek öncelik

Bunlar diyakritik eksiği değil, gerçek harf hatası. Yayındaki bir postta göze çarpar.

| Dosya | Hatalı | Doğrusu |
|---|---|---|
| ~~`karistirilan/lose-vs-loose/1.jpg`~~ | ~~`Kaybestmek`~~ | ✅ **çözüldü** |
| ~~`karistirilan/effect-vs-affect/1.jpg`~~ | ~~`AFFECT: Etkilemek (Fill)`~~ | ✅ **çözüldü** — `(Eylem)` olarak yazıldı |
| ~~`hikayeli/otel/3.jpg`~~ | ~~`alablir`~~ | ✅ **çözüldü** (08-22) — deste yerel basıma geçti, harfleri gerçek font basıyor |
| ~~`durumsal/no-veggies/1.jpg`~~ | ~~`alablir`~~ | ⛔ **konusuz kaldı** (08-22) — post silindi |
| ~~`durumsal/without-peppers/1.jpg`~~ | ~~`alablir`~~ | ⛔ **konusuz kaldı** (08-22) — post silindi |
| ~~`hikayeli/otel/5.jpg`~~ | ~~`Seyahat edoceklere gonder`~~ | ✅ **çözüldü** (08-22) — deste yerel basıma geçti, harfleri gerçek font basıyor |
| ~~`hikayeli/otel/2.jpg`~~ | ~~`reservasyonum`~~ | ✅ **çözüldü** (08-22) — deste yerel basıma geçti, harfleri gerçek font basıyor |
| ~~`seviye-testi/a1/7.png`~~ | ~~`fill -s takisi`~~ | ✅ **çözüldü** — 7.jpg olarak yeniden üretildi |
| ~~`seviye-testi/a1/7.png`~~ | ~~`I" oznesi`~~ | ✅ **çözüldü** — aynı üretimde |
| ~~`seviye-testi/b1/7.png`~~ | ~~`would + fil` / `filin 3. hali`~~ | ✅ **çözüldü** — `would + verb` / `past participle` |
| ~~`seviye-testi/b2/7.jpg`~~ | ~~`Third conoditional`~~ | ✅ **çözüldü** — parantezli terim kaldırıldı |
| ~~`seviye-testi/b2/7.jpg`~~ | ~~`Kac dogrune var?`~~ | ✅ **çözüldü** |
| `seviye-testi/b2/7.jpg` | `sora` (yeni üretimde) | sonra | -
| `seviye-testi/b2/7.jpg` | `tamahen` (yeni üretimde) | tamamen | -
| `seviye-testi/b2/7.jpg` | `vera` (yeni üretimde) | veya | -
| ~~`seviye-testi/a2/8.jpg`~~ | ~~`guulu`~~ | ✅ **çözüldü** |
| ~~`seviye-testi/a2/8.jpg`~~ | ~~`gorunuıyorsun`~~ | ✅ **çözüldü** |
| ~~`seviye-testi/b1/8.jpg`~~ | ~~`seviyesnde`~~ | ✅ **çözüldü** |
| ~~`seviye-testi/b1/8.jpg`~~ | ~~`gudu`~~ | ✅ **çözüldü** |
| ~~`seviye-testi/b2/8.jpg`~~ | ~~`seviyesende`~~ | ✅ **çözüldü** |
| ~~`seviye-testi/a1/8.jpg`~~ | ~~`değidlir`~~ | ✅ **çözüldü** (08-22) — 8. slayt yayından kaldırıldı, deste yeniden basıldı |
| ~~`seviye-testi/a2/8.jpg`~~ | ~~`dara`~~ | ✅ **çözüldü** (08-20) — slayt yayından kaldırıldı, deste yeniden basıldı |
| ~~`seviye-testi/{b1,b2}/8.jpg`~~ | ~~`dara`~~ | ✅ **çözüldü** (08-22) — 8. slayt yayından kaldırıldı, deste yeniden basıldı |
| ~~`seviye-testi/b1/8.jpg`~~ | ~~`bir az`~~ | ✅ **çözüldü** (08-22) — 8. slayt yayından kaldırıldı, deste yeniden basıldı |
| ~~`seviye-testi/b2/8.jpg`~~ | ~~`guclendirelem`~~ | ✅ **çözüldü** (08-22) — 8. slayt yayından kaldırıldı, deste yeniden basıldı |
| ~~`karistirilan/effect-vs-affect/1.jpg`~~ | ~~`takipte kali` (yeni üretimde)~~ | ✅ **çözüldü** (08-19) — fazla `i` silindi |
| `hikayeli/takside/6.jpg` | `odeyeblir` | odeyebilir | -
| `hikayeli/takside/6.jpg` | `edoceklere` | edeceklere | -
| `kitap-vs-gercek/gunluk-kaliplar/3.jpg` | `KITAP vs GERCEX` | KITAP vs GERCEK | -

**Not:** aynı kelime her destede farklı bozulmuş — `guclu` → `guulu` (a2), `gudu` (b1), doğru (b2). Tek bir arama-değiştirme ile yakalanmaz.

~~`hikayeli/otel/2.jpg` ayrıca **zaman uyumsuzluğu** taşıyordu: İngilizce `I have a reservation` (geniş zaman) ama Türkçe `rezervasyonum vardi` (geçmiş).~~ ✅ **çözüldü** (08-22) — kart `(Demir adına bir rezervasyonum var.)` olarak basıldı.

## 2. Yabancı diyakritik sızıntısı

Modelin Türkçe olmayan aksanlı harf basması. Kelime yanlış görünüyor.

| Dosya | Hatalı | Doğrusu |
|---|---|---|
| ~~`karistirilan/make-vs-do/1.jpg`~~ | ~~`gónderiyi` (ó)~~ | ⛔ **konusuz kaldı** (08-22) — post silindi |
| ~~`durumsal/no-veggies/1.jpg`~~ | ~~`nasĭl` (ĭ)~~ | ⛔ **konusuz kaldı** (08-22) — post silindi |
| ~~`seviye-testi/a2/8.jpg`~~ | ~~`bìraz` (ì)~~ | ✅ **çözüldü** |
| ~~`seviye-testi/a2/8.jpg`~~ | ~~`Asagĭya` (ĭ)~~ | ✅ **çözüldü** |
| ~~`seviye-testi/b2/8.jpg`~~ | ~~`kísa`, `bír` (í)~~ | ✅ **çözüldü** (08-22) — 8. slayt yayından kaldırıldı, deste yeniden basıldı |

## 3. Yapısal hatalar

| Dosya | Sorun | Etki |
|---|---|---|
| ~~`seviye-testi/a1/7.png`~~ | ~~1024×1024 kare~~ | ✅ **çözüldü** — `a1/7.jpg`, 1920×2400 |
| ~~`seviye-testi/a2/7.png`~~ | ~~1024×1024 kare~~ | ✅ **çözüldü** — `a2/7.jpg`, 1920×2400 |
| ~~`seviye-testi/b1/7.png`~~ | ~~1024×1024 kare~~ | ✅ **çözüldü** — `b1/7.jpg`, 1920×2400 |
| ~~`phrasal/run-out-of/1.jpg`~~ | ~~Başlık `RUN OUT` / `OF` şeklinde iki farklı puntoda kırılmış~~ | ⛔ **konusuz kaldı** (08-22) — post silindi |
| `seviye-testi/b2/3.jpg` | Soru ve CTA **serif** fontta | 60 görselin tek serif'i, marka dışı | -
| `seviye-testi/b2/2.jpg` | `SORU 01 / 05` sayacı başlıktan kopmuş, soruya yapışmış | Üst blok dağılmış | -

`seviye-testi/b2/7.jpg` dört cevap anahtarından **tek 4:5 olanı** — yani format hatası setin kendi içinde bile tutarsız. -

## 4. Marka tutarsızlıkları — düşük öncelik

Hata değil, ama yan yana paylaşılınca göze çarpar. Yeniden üretim yapılırsa birlikte düzeltilebilir.

- **Etiket rengi kayıyor:** `a1` ve `a2` destelerinde üst etiket 3. slayttan itibaren turuncudan laciverde dönüyor; `b1` ve `b2` boyunca turuncu kalıyor.
- **Zemin rengi kayıyor:** `a1` 5. slayttan itibaren sarıya, `b1` 4. slayttan itibaren şeftali tonuna kayıyor. `phrasal/cut-down-on` daha sarı, `karistirilan/lose-vs-loose` daha pembe.
- **CTA ikonu her kartta farklı:** düz `↓`, dolu daire içinde `⬇`, çizgili daire, gri daire, turuncu ok, `⌄` chevron, ve iki kartta hiç ok yok (sadece emoji).
- **Şablon sapması:** `phrasal/look-forward-to` tek `EXAMPLE SENTENCE` ara etiketi olan kart; `karistirilan/remember-vs-remind` tek ayraç çizgisi olan kart.
- **Şık kutuları** slayttan slayta farklı genişlikte (en belirgin `seviye-testi/a2/5.jpg`); `b2/4.jpg` tek çift çizgili kutuya sahip.
- **Emoji rengi:** ~~`seviye-testi/b2/8.jpg` sarı emoji kullanıyor~~ (08-22: slayt kaldırıldı), diğerleri tek renk glif. ~~`hikayeli/otel/5.jpg`'deki balon emoji gri-laciverde dönüşmüş.~~ (08-22: kart yeniden basıldı, CTA'da emoji yok.)
- **Kesme işareti:** ~~`hikayeli/otel/5.jpg` başlığında `I'D` açılış tırnağı olarak basılmış (`I‘D`)~~ — 08-22'de kart yeniden basıldı, kesme işareti doğru.

## 5. Genel diyakritik politikası

Görsellerdeki Türkçe **tutarsız** — arşiv, ASCII-only kuralının yürürlükte olduğu dönemde üretildi ama kurala kendisi de uymuyor. `ç` ve noktalı `i` genelde hayatta kalıyor, `ı ş ğ ü ö` ise rastgele düşüyor; üstelik **aynı cümle içinde**:

- `Kahvalti saat kaçta servis ediliyor?` (`hikayeli/otel/4.jpg`)
- ~~`Daha fazla kelime için begen` (`durumsal/on-the-side/1.jpg`)~~ — post silindi (08-22)
- `Motivasyon için arkadasina gonder` (`phrasal/give-up/1.jpg`)
- `BASLAMAK IÇIN KAYDIR` (dört kapak slaytının hepsinde)
- ~~`Ogrenmek için takipte kal` (`karistirilan/effect-vs-affect/1.jpg`)~~ — ✅ **çözüldü** (08-19): sedilya silinip `icin` yapıldı, satırın geri kalanı zaten ASCII'ydi

Üst etiketler de her kartta ASCII: `DURUMSAL INGILIZCE`, `GUNUN PHRASAL VERB'U`, `SIK KARISTIRILANLAR`, `A1 • INGILIZCE TESTI`.

**ASCII kuralı emekli oldu.** Kartlar artık `marka/kart_bas.ps1` ile yerelde
basılıyor; harfleri görüntü modeli değil gerçek font çiziyor, yani diyakritik
kaybı fiziksel olarak mümkün değil. Yeni ve yeniden basılan postlarda kural
**tam Türkçe** (`marka/README.md`). Bu bölümdeki kayıtlar yalnızca hâlâ eski
görselle duran postlar için geçerli; bir post yerel basıma geçtiğinde
kayıtları kapanıyor.

**08-20 notu:** `dizi/tell-me-about-it/1.jpg` bu geçişin ilk örneğiydi — henüz
görüntü modeliyle, ama bilinçli olarak tam Türkçe metinle basıldı (yukarıdaki
deneme kaydı). Yerel basım geldiği için `ş ğ ü ö`nin modelde sınanması artık
gereksiz kaldı.
