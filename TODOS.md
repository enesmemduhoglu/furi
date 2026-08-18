# TODOS

Son guncelleme: 2026-08-18.

Bu dosya furi1'in acik islerini tutar. Otomasyonun anlik durumu burada degil,
`otomasyon/durum.json` icinde.

---

## Acik isler

_Su an acik is yok._

---

## Kapanan isler

### [x] Post puanlama sistemi — Claude urettigi ve repoda duran her posta puan verir

**Neden:** 2026-08-18 sabahi rutin `karistirilan/borrow-vs-lend` postunu siraya
koydu, post onay sayfasinda "cop post" gerekcesiyle reddedildi ve SaaS kaydi
silindi. Kusur otomasyonda degil: rotasyon **sirasi gelen** postu seciyor,
**iyi olan** postu degil. Havuzdaki kalite farki bugun hicbir yerde olculmuyor,
dolayisiyla zayif bir post da guclu bir post da esit sansla onaya gidiyor. Tek
suzgec insanin onay ekraninda "hayir" demesi — yani kalite kontrolu akisin en
sonunda ve elle yapiliyor.

**Durum:** tamamlandi (2026-08-18). Kararlar verildi, kod yazildi, havuzdaki
27 yayinlanmamis postun tamami geriye donuk puanlandi.

---

#### Kararlar

**1. Saklama — post klasorunde `puan.json`.**

Her postun puani kendi klasorunde, `caption.md` yaninda durur. Icerikle birlikte
tasinir, postla ayni commit'te git gecmisine girer, post silinince puani da
gider. `aday_sec.py` zaten `postlari_tara` ile klasorleri geziyor; okuma ek
maliyet degil. Tek dosyali `otomasyon/puanlar.json` **kullanilmayacak** —
her puanlamanin ayni dosyayi degistirmesi commit cakismasi uretirdi.

Sema:

```json
{
  "olcut_surumu": 1,
  "tarih": "2026-08-18",
  "model": "claude-opus-5",
  "dallar": {
    "ilgi_cekicilik":  {"puan": 4, "gerekce": "kanca zayif, ilk slaytta soru yok"},
    "yazim":           {"puan": 8, "gerekce": "..."},
    "gorsel_kalite":   {"puan": 3, "gerekce": "..."},
    "ogretici_deger":  {"puan": 6, "gerekce": "..."},
    "ozgunluk":        {"puan": 5, "gerekce": "..."},
    "hedef_kitle":     {"puan": 7, "gerekce": "..."}
  },
  "kontroller": {
    "gorselde_harf_hatasi":   true,
    "sablon_tutarli":         false,
    "caption_imla_temiz":     true,
    "turkce_ingilizce_dogru": true
  },
  "toplam": 2.5
}
```

**2. Dallar — alti dal, hepsi 1-10.**

| dal | ne olcer |
| --- | --- |
| `ilgi_cekicilik` | konu ve kanca kaydirmayi durdurur mu, kaydetmeye/paylasmaya deger mi |
| `yazim` | caption ve slayt metinlerinde imla, dilbilgisi, Turkce-Ingilizce dogruluk |
| `gorsel_kalite` | sablon tutarliligi, okunabilirlik, gorseldeki harf hatalari |
| `ogretici_deger` | gercekten bir sey ogretiyor mu, yoksa bilineni mi tekrarliyor |
| `ozgunluk` | hesabin onceki postlarindan ve piyasadaki tipik icerikten ayrisiyor mu |
| `hedef_kitle` | seviye ve ton sayfanin takipcisine oturuyor mu |

Her dal puani yaninda kisa bir **gerekce** metni tasir; ciplak sayi "neden
dusuk" sorusunu cevaplamiyor. `HATA-RAPORU.md` bulgulari `gorsel_kalite` ve
`yazim` dallarinin girdisidir.

**3. Ikili kontroller — yargi degil, evet/hayir.**

Dal puanlarinin yaninda `kontroller` blogunda tutulur. Bunlar somut ve
denetlenebilir sorular; puanlayan ile ureten ayni model oldugu icin
oz-degerlendirmenin yumusak davranma riskini bunlar dengeler. Baslangic seti
yukaridaki dort soru; olcut surumu artirilarak cogaltilabilir.

**4. Toplam — duz ortalama, kontroller ceza.**

```
toplam = ortalama(alti dal puani) - 1.5 * (basarisiz kontrol sayisi)
```

Basarisiz kontrol = kusurun **var** oldugu durum (`gorselde_harf_hatasi: true`,
`sablon_tutarli: false`, ...). Dallar esit agirlikli; objektif kusur yargiya
degil sabit cezaya bagli oldugu icin model kalibrasyonundaki kayma siralamayi
daha az bozar. Agirlikli ortalama ve "en zayif dal belirler" secenekleri
degerlendirildi ve elendi.

**5. Aday secimi — kategori rotasyonu kalir, puan kategori icinde siralar.**

Dis siralama bugunku gibi: en uzun suredir yayinlanmamis kategori once. Degisen
tek sey, o kategori icinde "en eski commit" yerine "en yuksek puan" secilmesi.
Feed cesitliligi bozulmaz, stok tukenmez (27 adaylik havuzda ve 2 postluk
`kitap-vs-gercek` kategorisinde esik altini eleme riskliydi — **eleme yok**).

```python
sira_anahtari = (
    kategori_son_yayin,     # en eski kategori once  (degismedi)
    kategori,               #                        (degismedi)
    -toplam_puan,           # kategori icinde en iyi post  <-- YENI
    ilk_commit_zamani,      # esitlik bozucu
    ad,
)
```

Puani olmayan post elenmez; kategorisi icinde puanlilarin **arkasina** siralanir
(`toplam` yoksa `-inf` sayilir). Geriye donuk puanlama havuzu bir kere
tarayacagi icin bu durum gecici.

**5b. Sablon sapmasinda esik.** `sablon_tutarli` kontrolu ikili oldugu icin
her sapmaya ayni cezayi (1.5) veriyor. Bu yuzden kontrol yalnizca **ilk bakista
goze carpan** sapmalar icin `false` isaretlenir: font ya da olcek degisimi,
eksik standart oge, renk kaymasi, deste icinde eksik slayt. Ince ayrac cizgisi
gibi dekoratif ayrintilar `gorsel_kalite` dalindan dusulur, kontrole yazilmaz.
Aksi halde `karistirilan/remember-vs-remind` (tek hairline cizgi) ile
`dizi/suit-yourself` (butun font ailesi farkli) ayni cezayi alirdi.

**6. Bayatlama — olcut surumune bagli.**

`puan.json` icindeki `olcut_surumu`, koddaki guncel surumden kucukse puan bayat
sayilir ve yeniden puanlanir. Olcutler (dal tanimlari, kontrol sorulari, ceza
katsayisi) degistiginde surum artirilir. Takvime bagli bayatlama **yok** —
icerik ve olcut degismediyse puani yeniden hesaplamak bosa is. Baslangic
surumu: `1`.

---

#### Yapilanlar

1. **[x] Uretim akisina puanlama fazi.** WORKFLOW.md'ye **Faz 7 — Puanlama**
   eklendi (eski Faz 7 Teslim, Faz 8 oldu). Faz 5'te tespit edilip duzeltilmeden
   birakilan kusurlarin puana yansimasi kural olarak yazildi.
2. **[x] Havuz geriye donuk puanlandi.** 27 yayinlanmamis postun tamami
   puanlandi; her birinin klasorunde `puan.json` var. Puanlar 2.83 ile 8.50
   arasinda, ortalama 5.91 — havuzdaki kalite farkinin gercek oldugunu ve
   olculebildigini gosteriyor.
3. **[x] `aday_sec.py` puani okuyor.** `sira_anahtari` kategori icinde once
   puanlilari, sonra en yuksek puani aliyor; puansiz post arkaya dusuyor ama
   elenmiyor. `--durum` ciktisina `puan_dagilimi`, `puan_ortalamasi`,
   `en_dusuk_puan` ve `en_yuksek_puan` eklendi.
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

#### Puanlamanin ilk ciktisi

Sistem calisir calismaz rotasyonun davranisi degisti: `karistirilan` sirasi
geldiginde eski kural `effect-vs-affect`'i (5.00, gorselde `takipte kali` harf
hatasi) secerdi; yeni kural ayni kategoriden `remember-vs-remind`'i (7.67, hatasiz)
seciyor.

Puanlama sirasinda ayrica **HATA-RAPORU.md'de kayitli olmayan uc harf hatasi**
bulundu ve o dosyaya islendi: `hikayeli/takside/6.jpg` (`odeyeblir`,
`edoceklere`) ve `kitap-vs-gercek/gunluk-kaliplar/3.jpg` (`KITAP vs GERCEX` —
hata markanin kendi etiketinde).

En dusuk uc post — `hikayeli/otel` (2.83), `seviye-testi/b2` (3.33),
`durumsal/plain` (3.83) — su an aday havuzunda duruyor ve sirasi gelince onaya
gidecek. Puan elemedigi icin bu tasarim geregi; yeniden uretim ya da arsivleme
karari ayri bir is.
