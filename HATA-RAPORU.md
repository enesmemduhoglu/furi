# Arsivdeki bilinen hatalar

2026-08-11'de repodaki **60 gorselin tamami** tek tek okunarak cikarildi. Hicbiri duzeltilmedi — bu dosya, hangi kartin yeniden uretilmesi gerektigine sonra karar verebilmek icin tutuluyor.

Yeniden uretim yapilacaksa: WORKFLOW.md Faz 4–5.

**Cozulenler ustu cizili isaretlenir.** 2026-08-11: dort cevap anahtarinin **hepsi** yeniden uretildi (mai 3:4 → 1920×2560 olcek → 80px kirp → 1920×2400). Uc kare dosya (`a1/7.png`, `a2/7.png`, `b1/7.png`) gitti; artik **repodaki 60 gorselin tamami 1920×2400**. Ayni turda `fill`, `fil`, `filin`, `conoditional`, `Kac dogrune var?` hatalari da duzeldi.

2026-08-11, ikinci tur: kullanicinin `-` ile isaretlemedigi **5 gorsel** yeniden uretildi — `karistirilan/lose-vs-loose`, `karistirilan/effect-vs-affect`, `seviye-testi/{a2,b1,b2}/8.jpg`. Hedeflenen hatalarin **tamami** duzeldi.

**Esik notu:** Kucuk ve goze batmayan kusurlar (bas harf buyuk/kucuk, tirnak yonu, `•` yerine `-`, tek tuk harf hatasi) icin yeniden uretim yapilmiyor. Asagida bunlar listelense de birakilmalari bilincli bir karardir. Satir sonundaki `-` isareti "bu satir gecildi" demektir.

**Model notu:** `fiil` / `fiili` kelimesini iki model de guvenilir basmiyor (`fil`, `fill`, `fili` cikiyor). Cozum promptu sikilastirmak degil, kelimeyi degistirmek: `fiil` → `verb` / `past participle`, `(Fiil)` → `(Eylem)`.

---

## 1. Anlam bozan yazim hatalari — en yuksek oncelik

Bunlar diyakritik eksigi degil, gercek harf hatasi. Yayindaki bir postta goze carpar.

| Dosya | Hatali | Dogrusu |
|---|---|---|
| ~~`karistirilan/lose-vs-loose/1.jpg`~~ | ~~`Kaybestmek`~~ | ✅ **cozuldu** |
| ~~`karistirilan/effect-vs-affect/1.jpg`~~ | ~~`AFFECT: Etkilemek (Fill)`~~ | ✅ **cozuldu** — `(Eylem)` olarak yazildi |
| `hikayeli/otel/3.jpg` | `alablir` | alabilir | -
| `durumsal/no-veggies/1.jpg` | `alablir` | alabilir | -
| `durumsal/without-peppers/1.jpg` | `alablir` | alabilir | -
| `hikayeli/otel/5.jpg` | `Seyahat edoceklere gonder` | edeceklere | -
| `hikayeli/otel/2.jpg` | `reservasyonum` | rezervasyonum |-
| ~~`seviye-testi/a1/7.png`~~ | ~~`fill -s takisi`~~ | ✅ **cozuldu** — 7.jpg olarak yeniden uretildi |
| ~~`seviye-testi/a1/7.png`~~ | ~~`I" oznesi`~~ | ✅ **cozuldu** — ayni uretimde |
| ~~`seviye-testi/b1/7.png`~~ | ~~`would + fil` / `filin 3. hali`~~ | ✅ **cozuldu** — `would + verb` / `past participle` |
| ~~`seviye-testi/b2/7.jpg`~~ | ~~`Third conoditional`~~ | ✅ **cozuldu** — parantezli terim kaldirildi |
| ~~`seviye-testi/b2/7.jpg`~~ | ~~`Kac dogrune var?`~~ | ✅ **cozuldu** |
| `seviye-testi/b2/7.jpg` | `sora` (yeni uretimde) | sonra | -
| `seviye-testi/b2/7.jpg` | `tamahen` (yeni uretimde) | tamamen | -
| `seviye-testi/b2/7.jpg` | `vera` (yeni uretimde) | veya | -
| ~~`seviye-testi/a2/8.jpg`~~ | ~~`guulu`~~ | ✅ **cozuldu** |
| ~~`seviye-testi/a2/8.jpg`~~ | ~~`gorunuıyorsun`~~ | ✅ **cozuldu** |
| ~~`seviye-testi/b1/8.jpg`~~ | ~~`seviyesnde`~~ | ✅ **cozuldu** |
| ~~`seviye-testi/b1/8.jpg`~~ | ~~`gudu`~~ | ✅ **cozuldu** |
| ~~`seviye-testi/b2/8.jpg`~~ | ~~`seviyesende`~~ | ✅ **cozuldu** |
| `seviye-testi/a1/8.jpg` | `değidlir` | degildir — **a1'e dokunulmadi**, a2/b1/b2'de yeni uretimde duzeldi | -
| `seviye-testi/{a2,b1,b2}/8.jpg` | `dara` (yeni uretimde) | daha | -
| `seviye-testi/b1/8.jpg` | `bir az` (yeni uretimde) | biraz | -
| `seviye-testi/b2/8.jpg` | `guclendirelem` (yeni uretimde) | guclendirelim | -
| `karistirilan/effect-vs-affect/1.jpg` | `takipte kali` (yeni uretimde) | takipte kal | -

**Not:** ayni kelime her deste farkli bozulmus — `guclu` → `guulu` (a2), `gudu` (b1), dogru (b2). Tek bir arama-degistirme ile yakalanmaz.

`hikayeli/otel/2.jpg` ayrica **zaman uyumsuzlugu** tasiyor: Ingilizce `I have a reservation` (genis zaman) ama Turkce `rezervasyonum vardi` (gecmis). Dogrusu `var`. -

## 2. Yabanci diyakritik sizintisi

Modelin Turkce olmayan aksanli harf basmasi. Kelime yanlis gorunuyor.

| Dosya | Hatali | Dogrusu |
|---|---|---|
| `karistirilan/make-vs-do/1.jpg` | `gónderiyi` (ó) | gonderiyi | -
| `durumsal/no-veggies/1.jpg` | `nasĭl` (ĭ) | nasil | -
| ~~`seviye-testi/a2/8.jpg`~~ | ~~`bìraz` (ì)~~ | ✅ **cozuldu** |
| ~~`seviye-testi/a2/8.jpg`~~ | ~~`Asagĭya` (ĭ)~~ | ✅ **cozuldu** |
| `seviye-testi/b2/8.jpg` | `kísa`, `bír` (í) | kisa, bir | -

## 3. Yapisal hatalar

| Dosya | Sorun | Etki |
|---|---|---|
| ~~`seviye-testi/a1/7.png`~~ | ~~1024×1024 kare~~ | ✅ **cozuldu** — `a1/7.jpg`, 1920×2400 |
| ~~`seviye-testi/a2/7.png`~~ | ~~1024×1024 kare~~ | ✅ **cozuldu** — `a2/7.jpg`, 1920×2400 |
| ~~`seviye-testi/b1/7.png`~~ | ~~1024×1024 kare~~ | ✅ **cozuldu** — `b1/7.jpg`, 1920×2400 |
| `phrasal/run-out-of/1.jpg` | Baslik `RUN OUT` / `OF` seklinde **iki farkli puntoda** kirilmis | Otomatik sigdirma artefakti, baslik bozuk goruluyor | -
| `seviye-testi/b2/3.jpg` | Soru ve CTA **serif** fontta | 60 gorselin tek serif'i, marka disi | -
| `seviye-testi/b2/2.jpg` | `SORU 01 / 05` sayaci basliktan kopmus, soruya yapismis | Ust blok dagilmis | -

`seviye-testi/b2/7.jpg` dort cevap anahtarindan **tek 4:5 olani** — yani format hatasi setin kendi icinde bile tutarsiz. -

## 4. Marka tutarsizliklari — dusuk oncelik

Hata degil, ama yan yana paylasilinca goze carpar. Yeniden uretim yapilirsa birlikte duzeltilebilir.

- **Etiket rengi kayiyor:** `a1` ve `a2` destelerinde ust etiket 3. slayttan itibaren turuncudan laciverte donuyor; `b1` ve `b2` boyunca turuncu kaliyor.
- **Zemin rengi kayiyor:** `a1` 5. slayttan itibaren sariya, `b1` 4. slayttan itibaren seftali tonuna kayiyor. `phrasal/cut-down-on` daha sari, `karistirilan/lose-vs-loose` daha pembe.
- **CTA ikonu her kartta farkli:** duz `↓`, dolu daire icinde `⬇`, cizgili daire, gri daire, turuncu ok, `⌄` chevron, ve iki kartta hic ok yok (sadece emoji).
- **Sablon sapmasi:** `phrasal/look-forward-to` tek `EXAMPLE SENTENCE` ara etiketi olan kart; `karistirilan/remember-vs-remind` tek ayrac cizgisi olan kart.
- **Sik kutulari** slayttan slayta farkli genislikte (en belirgin `seviye-testi/a2/5.jpg`); `b2/4.jpg` tek cift cizgili kutuya sahip.
- **Emoji rengi:** `seviye-testi/b2/8.jpg` sari emoji kullaniyor, digerleri tek renk glif. `hikayeli/otel/5.jpg`'deki balon emoji gri-laciverte donusmus.
- **Kesme isareti:** `hikayeli/otel/5.jpg` basliginda `I'D` acilis tirnagi olarak basilmis (`I‘D`), govdede dogru.

## 5. Genel diyakritik politikasi

Gorsellerdeki Turkce **tutarsiz** — WORKFLOW.md Faz 2 ASCII-only diyor ama arsiv buna uymuyor. `ç` ve noktali `i` genelde hayatta kaliyor, `ı ş ğ ü ö` ise rastgele dusuyor; ustelik **ayni cumle icinde**:

- `Kahvalti saat kaçta servis ediliyor?` (`hikayeli/otel/4.jpg`)
- `Daha fazla kelime için begen` (`durumsal/on-the-side/1.jpg`)
- `Motivasyon için arkadasina gonder` (`phrasal/give-up/1.jpg`)
- `BASLAMAK IÇIN KAYDIR` (dort kapak slaytinin hepsinde)

Ust etiketler de her kartta ASCII: `DURUMSAL INGILIZCE`, `GUNUN PHRASAL VERB'U`, `SIK KARISTIRILANLAR`, `A1 • INGILIZCE TESTI`.

Yeni postlarda WORKFLOW.md Faz 2 kurali gecerli: **tam ASCII**. Eski arsivi hizaya cekmek isterse, en gorunur olanlar kapak slaytlarindaki `BASLAMAK IÇIN KAYDIR`.
