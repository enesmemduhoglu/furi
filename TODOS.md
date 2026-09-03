# TODOS

Son guncelleme: 2026-08-20.

Bu dosya furi1'in acik islerini tutar. Otomasyonun anlik durumu burada degil,
`otomasyon/durum.json` icinde.

---

## Acik isler

### [x] Havuzu yerel basima gecir — **bitti (2026-08-22)**

**Repoda artik goruntu modelinin metin yazdigi hicbir kart yok.** Havuzun 7.0 ve
uzeri kismi (22 post) yerel basima cevrildi; altinda kalan 11 post ise
cevrilmek yerine silindi (asagida). Ikisi birlikte isi kapatti.

**Karar (2026-08-20) neydi:** toplu tur yok, her gun yalnizca ertesi gunun
postu donusturulur. Maliyet zamana yayilsin, hic yayinlanmayacak posta hic
harcanmasin diye. Pratikte 22 post tek turda cevrildi ve kalan zayif kuyruk
silindi, yani kural konusuz kaldi. Yeni post uretiminde zaten yerel basim
varsayilan (WORKFLOW.md Faz 4).

Cevirmek yerine **silinen 13 post** (hepsi 2026-08-22):

| Post | Puan | Sebep |
|---|---|---|
| `karistirilan/borrow-vs-lend` | — | Onayda reddedilmisti (2026-08-18) |
| `kitap-vs-gercek/native-kaliplar` | 8.40 | Kullanici posta isinamadi |
| `phrasal/break-down` | 6.80 | 7.0 altı |
| `phrasal/put-off` | 6.80 | 7.0 altı |
| `durumsal/hold-the-onions` | 6.60 | 7.0 altı |
| `karistirilan/make-vs-do` | 6.60 | 7.0 altı |
| `durumsal/on-the-side` | 6.40 | 7.0 altı |
| `durumsal/without-peppers` | 6.40 | 7.0 altı |
| `phrasal/run-out-of` | 6.40 | 7.0 altı |
| `phrasal/come-up-with` | 6.00 | 7.0 altı |
| `phrasal/figure-out` | 6.00 | 7.0 altı |
| `durumsal/no-veggies` | 5.60 | 7.0 altı |
| `durumsal/plain` | 5.20 | 7.0 altı |

Havuz 34'ten **21 posta** dustu. `durumsal` kategorisi tamamen bosaldi;
`kitap-vs-gercek`te tek post kaldi. Gunde 1 post temposuyla eldeki stok
yaklasik uc hafta — sonrasi icin yeni uretim gerekiyor.

> Yontem, ileride bir posta gerekirse: `kart.json`'a tam Turkce metin →
> `python marka/metin_denetle.py <kart.json>` →
> `powershell -File marka\kart_bas.ps1 -Spec <kart.json> -Hedef <format>/<slug>`
> → gorselleri yerlesim icin denetle → `caption.md` alt text'ini kartla esitle.
>
> Gunun postu elle secilebiliyor: `durum.json > sonraki` alanina slug yazilirsa
> rutin onu siraya koyar (puan sirasini bir kereligine ezer, gonderimden sonra
> kendini temizler).

Deste slaytlari icin gereken oge turleri **eklendi** (`kapak`, `sayac`, `soru`,
`sik`, `madde`, `aciklama` + `ayrac`in `en` degeri, `alt` bosluk ezmesi) — sema
`marka/README.md`. Bes testin hepsi ayni semayla basiliyor.

**Sonuc slayti (skor tablosu) artik uretilmiyor.** 2026-08-20 karari: o slayt
yayinlanmiyor, deste cevap anahtariyla bitiyor. `skor` ve `uyari` oge turleri
bu yuzden hic yazilmadi. 2026-08-22'de karar `a1`, `b1`, `b2`'de de uygulandi:
`8.jpg`'ler silindi, 7. slaytin CTA'si kapanis CTA'si oldu, uc deste yeniden
basildi. Bes testin hepsi artik 7 slayt.

### [ ] `TODOS.md` duz yaziyi tam Turkce'ye cevir

`WORKFLOW.md` ve `HATA-RAPORU.md` 2026-08-22'de cevrildi (asagida). Geriye bu
dosya kaldi. Ayni gerekce: ASCII kurali emekli, yarim cevrilmis dokuman daha
kotu — tumu birden cevrilmeli.

`~/.claude/skills/insta-ingilizce/SKILL.md` de ASCII; repo disinda oldugu icin
ayri bir is. Frontmatter'i (`name`, `description`) iki dosyada da ASCII kalmali,
yoksa skill eslesmesi ayrisir.

---

## Kapanan isler

### [x] Denetim sozlugu kendi alt text'iyle zehirleniyordu — **duzeltildi (2026-09-03)**

**Belirti:** `metin_denetle.py --tumu` uc karta birden yanlis bulgu verdi ve
uc kartin da metni DOGRUYDU: `hikayeli/sinir-kapisinda` kapaginda `SINIR` icin
"SİNİR olmali", `KAPISINDA` icin "KAPİSİNDA olmali"; `kitap-vs-gercek/ofis-kaliplari`
kapaginda `ATMIYOR` icin "ATMİYOR olmali". Uc kelime de dotless `ı` ile dogru
yazilmisti (sınır, kapısında, atmıyor).

**Neden:** Sozluk `caption.md`'lerden turetiliyor, `WORKFLOW.md` Faz 6 ise alt
text'in karti **birebir** alintilamasini zorunlu kiliyor — yani her kart basligi
caption'a BUYUK harfle dusuyor. Buyuk harfte `ı`/`i` ayrimi geri getirilemedigi
icin `sozluk_kur`un iki-okunus denemesi (`SINIR` → `sınır` mi `sinir` mi?)
ikisi de gercek kelime oldugunda yanlis olani `nokta` sozlugune yaziyordu.
Sonuc: **kart kendi alt text'i yuzunden bulgu uretiyor.** Kusur post yazarken
degil, postun caption'i yazildiktan SONRA ortaya cikiyor; ilk basim geciyor,
ikinci basim reddediliyor.

**Duzeltme:** ASCII `I` iceren BUYUK harfli kelime sozluge girmiyor. Eleme
bilerek dar — belirsizligin tek kaynagi o harf; `TESTİ` gibi zaten noktali
yazilmis buyuk kelime sozlukte kaliyor, yoksa `TESTI` bulgusu kaybolurdu
(dosyanin kendi ornegi). Ayrica `ESSESLI` muafiyeti eklendi: katlaninca baska
bir gercek Turkce kelimeye esitlenen `onu`/`önü`, `ise`/`işe`, `iste`/`işte`.
Ucu de ayni gun kart yazarken carpisti. `SORU_EKI` ile ayni mantik.

**Ilke:** sozlugun icerigi degistikce denetimin sonucu degismemeli. Bir kartin
basilip basilmamasi, baska bir postun caption'inda hangi kelimelerin gectigine
bagli olamaz. Ayni ilke satir ici yorumda `SIK KARISTIRILANLAR` icin de yazili.

**Nerede:** `marka/metin_denetle.py` > `sozluk_kur` ve `ESSESLI`; anlatimi
`marka/README.md` > "Uc bilincli susturma".


### [x] `WORKFLOW.md` ve `HATA-RAPORU.md` tam Turkce'ye cevrildi

2026-08-22. Duz yazinin tamami cevrildi. Cevrilmeyenler bilincli:

- Kod bloklari, dosya yollari, slug'lar, JSON anahtarlari
- `HATA-RAPORU.md` tablolarindaki "Hatali"/"Dogrusu" sutunlari — bunlar
  gorseldeki metnin **birebir alintisi**, o gorseller ASCII uretildi
- `WORKFLOW.md` frontmatter'i — SKILL.md ile birebir ayni kalmali

Ayni turda iki bayat kayit duzeltildi: `HATA-RAPORU.md` §5 hala "yeni
postlarda tam ASCII" diyordu (kural 08-20'de emekli oldu), `WORKFLOW.md` Ek B
iskeleti hala 8 slaytli test ve ASCII slayt metni gosteriyordu.


### [x] Post puanlama sistemi — Claude urettigi ve repoda duran her posta puan verir

**Neden:** 2026-08-18 sabahi rutin `karistirilan/borrow-vs-lend` postunu siraya
koydu, post onay sayfasinda "cop post" gerekcesiyle reddedildi ve SaaS kaydi
silindi. Kusur otomasyonda degil: rotasyon **sirasi gelen** postu seciyor,
**iyi olan** postu degil. Havuzdaki kalite farki hicbir yerde olculmuyordu,
dolayisiyla zayif bir post da guclu bir post da esit sansla onaya gidiyordu. Tek
suzgec insanin onay ekraninda "hayir" demesiydi — yani kalite kontrolu akisin en
sonunda ve elle yapiliyordu.

**Durum:** tamamlandi (2026-08-18). Olcut surumu 2 yayinda; havuzdaki 27
yayinlanmamis postun tamami puanli.

---

#### Karar (2026-08-28): arka arkaya ayni kategori cikmaz

**Kural:** en son yayinlanan postun kategorisi bir tur bekler. Kisit **puanin
ustunde** duruyor, yani havuzun tepesindeki post da atlanir ve sirasi bir gun
kayar. `durum.json > sonraki` ile elle secim bu kisiti de ezer.

**Neden:** 28.08'de `turkce-tuzagi/birebir-ceviri` yayinlandi. Ayni gun serinin
ikinci bolumu (`ceviri-refleksi`, 8.60) uretildi ve havuzun tepesine oturdu —
yani ertesi gun de ayni konu cikacakti. Feed'de art arda iki ayni tur post
seriyi tuketiyor: ikinci bolumun degeri ilkinden bir gun sonra degil, birkac
gun sonra cikmasinda.

**2026-08-18 karariyla celismiyor.** O karar kategori rotasyonunu *birincil
olcut* olmaktan cikardi, cunku rotasyon "sirasi gelen"i seciyordu ve guclu bir
postu gunlerce bekletebiliyordu (`borrow-vs-lend` onayda "cop post" diye
reddedilmisti). Buradaki kisit tek adimlik ve yon degistirmiyor: kalite sirasi
hem kategorinin icinde hem disinda aynen korunuyor, yalnizca son cikan tur bir
gun bekliyor.

**Nerede:** `aday_sec.adaylari_sirala` — siralamanin tek dogruluk kaynagi,
`saas_gonder` de oradan okuyor. `--durum` ciktisina `bekleyen_kategori` alani
eklendi; o alan olmadan "en yuksek puanli post neden sirada degil" sorusu
ciktinin icinde cevapsiz kaliyordu.

**Sinir durumu:** havuzda tek kategori kalirsa hepsi ayni cezayi alir, yani
kilitlenme olmaz — sira kendi icinde puana gore isler.

#### Kararlar

**1. Saklama — post klasorunde `puan.json`.**

Her postun puani kendi klasorunde, `caption.md` yaninda durur. Icerikle birlikte
tasinir, postla ayni commit'te git gecmisine girer, post silinince puani da
gider. `aday_sec.py` zaten `postlari_tara` ile klasorleri geziyor; okuma ek
maliyet degil. Tek dosyali `otomasyon/puanlar.json` **kullanilmadi** — her
puanlamanin ayni dosyayi degistirmesi commit cakismasi uretirdi.

**2. Puan postun KALITESINI olcer, uretim kusurunu degil.**

> Bu, olcut surumu 2 ile gelen ve sistemin tamamini sekillendiren karar.
> Ilk surumde `gorselde_harf_hatasi`, `caption_imla_temiz`, `sablon_tutarli` ve
> `turkce_ingilizce_dogru` diye dort ikili kontrol ve bir `yazim` dali vardi;
> her basarisiz kontrol toplamdan 1.5 dusuyordu.

Kaldirildi. Puanin cevapladigi soru **"bu post iyi mi, ilgi ceker mi"**;
"duzgun basilmis mi" degil. Uretim kusurlarinin defteri zaten `HATA-RAPORU.md`
ve tespit yeri WORKFLOW.md Faz 5. Iki defterin ayni seyi iki kez tutmasi
siralamayi bulaniklastiriyordu: **temiz basilmis siradan bir post, tek harf
hatasi olan cok daha iyi bir postun onune geciyordu.**

Somut ornek — `hikayeli/otel` surum 1'de havuzun en dusuguydu (2.83), cunku uc
harf hatasi ve bir ceviri hatasi toplamdan 3.0 goturuyordu. Surum 2'de 7.00:
icerik olarak ortalama ustu bir post ve zaten oyleydi; sorun basimdaydi, fikirde
degil. O sorun HATA-RAPORU.md'de kayitli ve orada kalmali.

**3. Bes dal, hepsi 1-10, hepsi gerekceli.**

| Dal | Ne olcer |
| --- | --- |
| `ilgi_cekicilik` | Konu ve kanca kaydirmayi durdurur mu, kaydetmeye/paylasmaya deger mi |
| `ogretici_deger` | Gercekten bir sey ogretiyor mu, yoksa bilineni mi tekrarliyor |
| `ozgunluk` | Hesabin onceki postlarindan ve piyasadaki tipik icerikten ayrisiyor mu |
| `hedef_kitle` | Seviye, ton ve ornek secimi sayfanin takipcisine oturuyor mu |
| `gorsel_kalite` | Kompozisyon, hiyerarsi, okunabilirlik |

`gorsel_kalite` dalinin siniri onemli:

- **Girer:** kirik baslik, kutuya sigmayan metin, bozuk dikey denge, birbiriyle
  yarisan iki odak — bunlar okunabilirligi bozar, yani postun kalitesini dusurur.
- **Girmez:** yanlis harf, eksik diyakritik, farkli font, kayan zemin rengi,
  baska bir CTA ikonu — bunlar uretim kusuru.

Her dal puani yaninda kisa ve **somut** bir gerekce tasir; ciplak sayi "neden
dusuk" sorusunu cevaplamiyor, bos sifat ("iyi", "temiz") da cevaplamiyor.

**4. Toplam — duz ortalama, ceza yok.**

```
toplam = ortalama(5 dal)      -> her zaman 1-10 arasi
```

Agirlikli ortalama ve "en zayif dal belirler" secenekleri degerlendirildi ve
elendi. Cezali formul (surum 1) kaldirildi; toplamin dal puanlariyla ayni
olcekte kalmasi puani okunur yapiyor.

**5. Aday secimi — en yuksek puandan asagiya.**

> Bu karar iki adimda olustu. Ilk hali: kategori rotasyonu birincil, puan
> kategori icinde siralayici. 2026-08-18'de degistirildi.

Havuzun **tamami** puana gore siralanir ve tepeden baslanir. Kategori birincil
olcut degil, yalnizca **esit puanlilar** arasinda konusur.

```python
sira_anahtari = (
    0 if puanli else 1,     # puansiz/bayat HAVUZUN sonuna
    -toplam_puan,           # EN YUKSEK PUAN ONCE  <-- birincil
    # asagisi yalnizca esit puanlilar arasinda konusur
    kategori_son_yayin,     # ayni puanda: uzun suredir gorunmeyen kategori
    kategori,
    ilk_commit_zamani,
    ad,
)
```

**Takas bilincli:** feed'de arka arkaya ayni turden iki post cikabilir. Nitekim
su anki havuzda 3. ve 4. siralar `dizi/my-bad` ve `dizi/speak-of-the-devil` —
ikisi de ayni kategoriden. Onceki kural bunu engelliyordu ama iyi bir postu
sirasi gelmedigi icin bekletiyordu; yeni kuralda yayin sirasi kaliteyi izler,
cesitliligi degil.

Rotasyon esitlik bozucu olarak tutuldu cunku bedava: ilk iki post da 8.40 ve
`kitap-vs-gercek` hic yayinlanmadigi icin `native-kaliplar` `tell-me-about-it`in
onune geciyor.

**Yan etki — puansiz post artik gercekten bekler.** Eskiden puani olmayan post
kendi kategorisinin sonuna duserdi, yani kategori sirasi geldiginde yine
gorunurdu. Simdi havuzun tamaminin sonuna dusuyor: puanli tek bir aday kaldigi
surece puansiz post secilmez. Uretim akisi her postu puanladigi icin
(WORKFLOW.md Faz 7) bu gecici olmali, ama Faz 7'yi atlamak postu fiilen rafa
kaldirir. `puanla.py` puansiz kalanlari listeler.

**Puan hala ELEMEZ:** hicbir post puani yuzunden havuzdan cikmiyor, sadece
sirasi geriye gidiyor. 2 postluk `kitap-vs-gercek` gibi kategorilerde esik
koyup elemek stok tukenmesi riski tasiyordu — o karar degismedi.

**6. Bayatlama — olcut surumune bagli.**

`puan.json` icindeki `olcut_surumu`, koddaki guncel surumden kucukse puan bayat
sayilir. Bayat puanin `toplam`i **kullanilmaz**: eski surum farkli bir formulle
hesaplandigi icin yenilerle kiyaslanamaz, bu yuzden post siralamada puansiz gibi
arkaya duser. Takvime bagli bayatlama **yok** — icerik ve olcut degismediyse
puani yeniden hesaplamak bosa is.

Surum 1'den 2'ye gecerken mekanizma kendini sinadi: 27 puanin tamami
`puanla.py --bayat` ile tek komutta bayat olarak isaretlendi ve yeniden
puanlandi.

---

#### Yapilanlar

1. **[x] Uretim akisina puanlama fazi.** WORKFLOW.md'ye **Faz 7 — Puanlama**
   eklendi (eski Faz 7 Teslim, Faz 8 oldu). "Uretim kusurlari puana girmez"
   kurali ve gerekce yazma standardi orada.
2. **[x] Havuz puanlandi.** 27 yayinlanmamis postun tamami; her birinin
   klasorunde `puan.json` var. Puanlar 5.20 ile 8.40 arasinda, ortalama 7.19.
3. **[x] `aday_sec.py` sirayi puana gore kuruyor.** `sira_anahtari`nin birincil
   olcutu artik puan; kategori esitlik bozucuya indi. `--durum` ciktisina
   `puan_dagilimi`, `puan_ortalamasi`, `en_dusuk_puan`, `en_yuksek_puan` ve
   havuzun tamamini yayin sirasinda veren `yayin_sirasi` eklendi.
4. **[x] `puanla.py` yazildi.** `--eksik`, `--bayat`, `--tumu`, `--slug`,
   `--sema`, `--yaz` (+ `--kuru`, `--dosya`, `--malzeme`). Puani Claude verir;
   script tarama, sema dogrulamasi ve yazma isini gorur. `toplam` tek yerde
   (`furi_ortak.toplam_hesapla`) hesaplanir.
5. **[x] Semalar belgelendi.** `otomasyon/README.md` > "Post puani",
   `.claude/skills/insta-yayinla/SKILL.md` > "Aday secimi".

**Dokunulan yerler:** `WORKFLOW.md`, `HATA-RAPORU.md`, `otomasyon/README.md`,
`.claude/skills/insta-yayinla/SKILL.md`,
`.claude/skills/insta-yayinla/scripts/{furi_ortak,aday_sec,puanla}.py`,
`<kategori>/<slug>/puan.json` (27 dosya).

---

#### Puanlamanin ciktisi

> ⚠ **Bu blok 2026-08-18 tarihli bir fotograf, guncel havuz DEGIL.** Sistemin
> ilk turunda ne cikti onu gosteriyor; o gunden beri postlar yayinlandi,
> silindi ve eklendi. Asagidaki listede artik var olmayan postlar geciyor
> (`kitap-vs-gercek/native-kaliplar` cope atildi, `durumsal/*` klasoruyle
> birlikte silindi, `karistirilan/make-vs-do` ve dort `phrasal` elendi).
>
> **Guncel sira icin tek kaynak:** `python .claude/skills/insta-yayinla/scripts/aday_sec.py --durum`
> — `yayin_sirasi` alani. Buraya bakip "siradaki post su" deme.

Puanlar kategori kategori (2026-08-18, olcut surumu 2). Yayin sirasi artik
kategoriden bagimsiz, tepeden asagiya — asagida ayrica veriliyor.

```
dizi:            tell-me-about-it 8.40 | speak-of-the-devil 8.20 | my-bad 8.20 | suit-yourself 7.00
kitap-vs-gercek: native-kaliplar 8.40 | gunluk-kaliplar 7.80
hikayeli:        takside 7.80 | doktorda 7.60 | otel 7.00
seviye-testi:    c1 7.80 | a1 7.80 | a2 7.60 | b2 7.40
karistirilan:    remember-vs-remind 7.60 | lose-vs-loose 7.00 | effect-vs-affect 7.00 | make-vs-do 6.60
phrasal:         look-forward-to 7.40 | cut-down-on 7.40 | give-up 7.00 | put-off 6.80
                 run-out-of 6.40 | figure-out 6.00 | come-up-with 6.00
durumsal:        without-peppers 6.40 | on-the-side 6.40 | plain 5.20
```

Yayin sirasi (ilk sekiz):

```
1. kitap-vs-gercek/native-kaliplar   8.40
2. dizi/tell-me-about-it             8.40
3. dizi/my-bad                       8.20
4. dizi/speak-of-the-devil           8.20
5. kitap-vs-gercek/gunluk-kaliplar   7.80
6. seviye-testi/a1                   7.80
7. seviye-testi/c1                   7.80
8. hikayeli/takside                  7.80
```

Tamami `aday_sec.py --durum` > `yayin_sirasi` alaninda.

**Havuzun sekli:** puanlar 5.20-8.40 arasinda toplanmis, ortalama 7.19. Yani
havuzda "cop" yok; fark var ama dar. En zayif uc (`durumsal/plain` 5.20,
`phrasal/come-up-with` 6.00, `phrasal/figure-out` 6.00) ayni sorunu paylasiyor:
konu fazla basit ya da ornek fazla nis, ozgunluk dusuk. En guclu uc
(`dizi/tell-me-about-it` 8.40, `kitap-vs-gercek/native-kaliplar` 8.40,
`dizi/speak-of-the-devil` 8.20) ise ortak bir sey yapiyor — bir yanilgiyi once
kurup sonra duzeltiyor.

Puanlama sirasinda ayrica **HATA-RAPORU.md'de kayitli olmayan uc harf hatasi**
bulundu ve o dosyaya islendi: `hikayeli/takside/6.jpg` (`odeyeblir`,
`edoceklere`) ve `kitap-vs-gercek/gunluk-kaliplar/3.jpg` (`KITAP vs GERCEX` —
hata markanin kendi etiketinde). Bunlar puani etkilemiyor; yeniden uretim ayri
bir karar.
