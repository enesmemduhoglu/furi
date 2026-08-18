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
**iyi olan** postu degil. Havuzdaki kalite farki hicbir yerde olculmuyordu,
dolayisiyla zayif bir post da guclu bir post da esit sansla onaya gidiyordu. Tek
suzgec insanin onay ekraninda "hayir" demesiydi — yani kalite kontrolu akisin en
sonunda ve elle yapiliyordu.

**Durum:** tamamlandi (2026-08-18). Olcut surumu 2 yayinda; havuzdaki 27
yayinlanmamis postun tamami puanli.

---

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

**5. Aday secimi — kategori rotasyonu kalir, puan kategori icinde siralar.**

Dis siralama eskisi gibi: en uzun suredir yayinlanmamis kategori once. Degisen
tek sey, o kategori icinde "en eski commit" yerine "en yuksek puan" secilmesi.
Feed cesitliligi bozulmaz, stok tukenmez (27 adaylik havuzda ve 2 postluk
`kitap-vs-gercek` kategorisinde esik altini eleme riskliydi — **eleme yok**).

```python
sira_anahtari = (
    kategori_son_yayin,     # en eski kategori once  (degismedi)
    kategori,               #                        (degismedi)
    0 if puanli else 1,     # puansiz/bayat kategorinin sonuna  <-- YENI
    -toplam_puan,           # kategori icinde en iyi post       <-- YENI
    ilk_commit_zamani,      # esitlik bozucu
    ad,
)
```

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
3. **[x] `aday_sec.py` puani okuyor.** `sira_anahtari` kategori icinde once
   puanlilari, sonra en yuksek puani aliyor. `--durum` ciktisina
   `puan_dagilimi`, `puan_ortalamasi`, `en_dusuk_puan`, `en_yuksek_puan` eklendi.
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

Kategori ici siralama (2026-08-18, olcut surumu 2):

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

Sistem calisir calismaz rotasyonun davranisi degisti: `karistirilan` sirasi
geldiginde eski kural `effect-vs-affect`'i secerdi (repoya once eklendigi icin);
yeni kural ayni kategoriden `remember-vs-remind`'i seciyor (7.60 vs 7.00).

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
