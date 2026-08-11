# Arsivdeki bilinen hatalar

2026-08-11'de repodaki **60 gorselin tamami** tek tek okunarak cikarildi. Hicbiri duzeltilmedi — bu dosya, hangi kartin yeniden uretilmesi gerektigine sonra karar verebilmek icin tutuluyor.

Yeniden uretim yapilacaksa: ayni prompt + farkli `seed`, WORKFLOW.md Faz 4–5.

---

## 1. Anlam bozan yazim hatalari — en yuksek oncelik

Bunlar diyakritik eksigi degil, gercek harf hatasi. Yayindaki bir postta goze carpar.

| Dosya | Hatali | Dogrusu |
|---|---|---|
| `karistirilan/lose-vs-loose/1.jpg` | `Kaybestmek` | Kaybetmek |
| `karistirilan/effect-vs-affect/1.jpg` | `AFFECT: Etkilemek (Fill)` | `(Fiil)` |
| `hikayeli/otel/3.jpg` | `alablir` | alabilir |
| `durumsal/no-veggies/1.jpg` | `alablir` | alabilir |
| `durumsal/without-peppers/1.jpg` | `alablir` | alabilir |
| `hikayeli/otel/5.jpg` | `Seyahat edoceklere gonder` | edeceklere |
| `hikayeli/otel/2.jpg` | `reservasyonum` | rezervasyonum |
| `seviye-testi/a1/7.png` | `fill -s takisi` | `fiil -s takisi` |
| `seviye-testi/a1/7.png` | `I" oznesi` (acilis tirnagi yok) | `"I" oznesi` |
| `seviye-testi/b1/7.png` | `would + fil` / `filin 3. hali` | fiil / fiilin |
| `seviye-testi/b2/7.jpg` | `Third conoditional` | conditional |
| `seviye-testi/b2/7.jpg` | `Kac dogrune var?` | `Kac dogrun var?` |
| `seviye-testi/a2/8.jpg` | `guulu` | guclu |
| `seviye-testi/a2/8.jpg` | `gorunuıyorsun` (fazladan `ı` + hayalet glif) | gorunuyorsun |
| `seviye-testi/b1/8.jpg` | `seviyesnde` | seviyesinde |
| `seviye-testi/b1/8.jpg` | `gudu` | guclu |
| `seviye-testi/b2/8.jpg` | `seviyesende` | seviyesinde |
| `seviye-testi/{a1,a2,b1,b2}/8.jpg` | `değidlir` / `degidlir` | degildir |

**Not:** ayni kelime her deste farkli bozulmus — `guclu` → `guulu` (a2), `gudu` (b1), dogru (b2). Tek bir arama-degistirme ile yakalanmaz.

`hikayeli/otel/2.jpg` ayrica **zaman uyumsuzlugu** tasiyor: Ingilizce `I have a reservation` (genis zaman) ama Turkce `rezervasyonum vardi` (gecmis). Dogrusu `var`.

## 2. Yabanci diyakritik sizintisi

Modelin Turkce olmayan aksanli harf basmasi. Kelime yanlis gorunuyor.

| Dosya | Hatali | Dogrusu |
|---|---|---|
| `karistirilan/make-vs-do/1.jpg` | `gónderiyi` (ó) | gonderiyi |
| `durumsal/no-veggies/1.jpg` | `nasĭl` (ĭ) | nasil |
| `seviye-testi/a2/8.jpg` | `bìraz` (ì) | biraz |
| `seviye-testi/a2/8.jpg` | `Asagĭya` (ĭ) | Asagiya |
| `seviye-testi/b2/8.jpg` | `kísa`, `bír` (í) | kisa, bir |

## 3. Yapisal hatalar

| Dosya | Sorun | Etki |
|---|---|---|
| `seviye-testi/a1/7.png` | **1024×1024 kare** (digerleri 1920×2400) | Karuselde kirpilir — en yuksek oncelikli yapisal hata |
| `seviye-testi/a2/7.png` | 1024×1024 kare | Ayni |
| `seviye-testi/b1/7.png` | 1024×1024 kare | Ayni |
| `phrasal/run-out-of/1.jpg` | Baslik `RUN OUT` / `OF` seklinde **iki farkli puntoda** kirilmis | Otomatik sigdirma artefakti, baslik bozuk goruluyor |
| `seviye-testi/b2/3.jpg` | Soru ve CTA **serif** fontta | 60 gorselin tek serif'i, marka disi |
| `seviye-testi/b2/2.jpg` | `SORU 01 / 05` sayaci basliktan kopmus, soruya yapismis | Ust blok dagilmis |

`seviye-testi/b2/7.jpg` dort cevap anahtarindan **tek 4:5 olani** — yani format hatasi setin kendi icinde bile tutarsiz.

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
