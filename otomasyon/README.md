# otomasyon/

Bu klasor `insta-yayinla` skill'inin **durumunu** tutar. Iceriginin tamami makine tarafindan
yazilir; elle duzenlemek gerekirse skill calismiyorken yapilmali.

Skill'in kendisi: `.claude/skills/insta-yayinla/SKILL.md`

## Neden repo icinde?

Zamanlanmis calisma (cloud routine) her seferinde repoyu temiz klonlayarak baslar. Yerel diskte
tutulan bir state dosyasi bir sonraki calismada yok olur. Bu yuzden durum repoya commit edilir —
state'in hayatta kalmasinin tek yolu bu.

## Dosyalar

### `yayinlananlar.json` — yayin defteri

Instagram'a **gercekten yuklenmis** postlarin kaydi. "Bu post daha once atildi mi?"
sorusunun cevabi burada.

Yayini artik bu repo yapmiyor — `content-approval-saas` onay geldigi anda yayinliyor,
yani defter yayin anini goremiyor. Bu yuzden defter **turetilmis** bir kayit: her
calismanin basinda `esitle.py` Instagram'a bakip guncelliyor. Asil dogruluk kaynagi
Instagram hesabinin kendisi.

Elle bir kayit silersen `esitle.py` bir sonraki calismada geri ekler (post hala
Instagram'da duruyorsa). Bir postu gercekten havuza dondurmek istiyorsan once
Instagram'dan sil.

```json
{
  "guncelleme": "2026-08-15T09:13:00+03:00",
  "kayitlar": [
    {
      "slug": "hikayeli/takside",
      "kategori": "hikayeli",
      "slayt": 6,
      "ig_media_id": "18012345678901234",
      "permalink": "https://www.instagram.com/p/Cxyz/",
      "yayin_zamani": "2026-08-15T09:13:00+03:00"
    }
  ]
}
```

### `durum.json` — anlik durum

| Alan | Anlami |
|---|---|
| `bekleyen` | SaaS'a gonderilmis, onay bekleyen post. `saas_post_id` ve `onay_url` icerir. Bosta iken `null`. Post yayinlaninca `esitle.py` kapatir. |
| `yayin_denemesi` | **Artik kullanilmiyor.** Yayin bu repodan yapilirken cift yayini engelliyordu; o is SaaS'a gecti ve orada veritabani seviyesinde kosullu UPDATE ile cozuluyor. Alan geriye donuk uyumluluk icin duruyor, `null` kalmali. Sadece `ig_yayinla.py --slug` ile elle yayin yapilirsa dolar. |
| `son_yayin` | Son basarili yayinin **fark edildigi** an (gercek yayin ani degil — `esitle.py` bir sonraki calismada ogreniyor). Sadece bilgi; siraya koymayi engellemez. |
| `son_gonderim` | Son postun SaaS'a gonderildigi an. Iki gonderimin ayni saate yigilmamasi icin kullanilir (min 4 saat ara). |
| `bugun` | Takvim gunu sayaclari. `siraya_konan` gunluk kotayi belirler (max 2), `yayinlanan` sadece bilgi. Tarih degisince ikisi de sifirlanir. |
| `son_stok_uyarisi` | "Post stogu azaliyor" mailinin gunde birden fazla gitmemesi icin. |
| `sonraki` | Elle secilmis "gunun postu". Doluysa aday siralamasi bir kereligine ezilir ve o slug siraya konur; gonderim yapilinca `saas_gonder.py` alani temizler. Bosta iken `null`. Havuzdaki postlar gunu gunune yerel basima cevrildigi icin var: cevrilen post ertesi gun yayina girmeli, ama puan sirasi baska bir postu one alabiliyor. |
| `sure_dolanlar` | SaaS onay linki yanitsiz kalip suresi dolan postlarin sayaci (`{"slug": 2}`). Suresi dolmak postu **elemez** — post havuzda kalir, sirasi gelince yeniden onerilir. Ancak sayac 3'e ulasirsa `atlananlar`'a gecer. Post yayinlaninca sayaci silinir. |
| `atlananlar` | Onay sayfasinda reddedilen ya da 3 kez ust uste yanitsiz kalan postlar. Bir daha aday olarak secilmezler. Tekrar siraya girmesi icin buradan silmek yeterli. |

> Eskiden burada bir `token` blogu (Instagram token'inin yenileme/bitis tarihleri)
> vardi. **Kaldirildi:** token da son kullanma tarihi de artik yalnizca SaaS'ta
> duruyor ve SaaS'in gunluk cron'u yeniliyor — buradaki tarih o yenilemeleri
> gormedigi icin bayat bir kopyaydi. Kalan sureyi ogrenmek icin:
> `python .claude/skills/insta-yayinla/scripts/ig_token.py --kontrol`

## Post puani — `<kategori>/<slug>/puan.json`

Bu klasorde **degil**, her postun kendi klasorunde durur; yine de otomasyonun
okudugu bir state oldugu icin semasi burada. Karar gecmisi: `TODOS.md` >
"Post puanlama sistemi".

**Puan postun kalitesini olcer** — ilgi cekiyor mu, ogretiyor mu, ayrisiyor mu.
Uretim kusurlari (gorseldeki harf hatalari, imla, sablon ve marka sapmalari)
puana **girmez**; onlarin defteri `HATA-RAPORU.md`. Iki defterin ayni seyi iki
kez tutmasi "hangi post daha iyi" sorusunu bulaniklastiriyordu: temiz basilmis
siradan bir post, tek harf hatasi olan cok daha iyi bir postun onune geciyordu.

Puani Claude verir, `puanla.py` yazar. Elle duzenlenmemeli: `toplam` formulden
turetilir ve `aday_sec.py` her okuyusta yeniden hesaplar.

```json
{
  "olcut_surumu": 2,
  "tarih": "2026-08-18",
  "model": "claude-opus-5",
  "dallar": {
    "ilgi_cekicilik": {"puan": 8, "gerekce": "kanca guclu, ilk slaytta soru var"},
    "ogretici_deger": {"puan": 9, "gerekce": "..."},
    "ozgunluk":       {"puan": 7, "gerekce": "..."},
    "hedef_kitle":    {"puan": 9, "gerekce": "..."},
    "gorsel_kalite":  {"puan": 8, "gerekce": "..."}
  },
  "toplam": 8.2
}
```

| Alan | Anlami |
|---|---|
| `olcut_surumu` | Puanin hangi olcut setiyle verildigi. Koddaki `OLCUT_SURUMU`'nden kucukse puan **bayat** sayilir; eski surum farkli bir formulle hesaplandigi icin toplami yenilerle kiyaslanamaz, bu yuzden siralamada puansiz gibi arkaya duser. Takvime bagli bayatlama yok. |
| `dallar` | Bes dal, her biri 1-10 **ve zorunlu bir gerekce**. Gerekcesiz puan dogrulamadan gecmez; gerekce bos sifat degil, neyin nerede oldugu olmali. |
| `toplam` | `ortalama(5 dal)`. Her zaman 1-10 arasi — ceza yok. |

### Dallar

| Dal | Ne olcer |
|---|---|
| `ilgi_cekicilik` | Konu ve kanca kaydirmayi durdurur mu, kaydetmeye/paylasmaya deger mi |
| `ogretici_deger` | Gercekten bir sey ogretiyor mu, yoksa bilineni mi tekrarliyor |
| `ozgunluk` | Hesabin onceki postlarindan ve piyasadaki tipik icerikten ayrisiyor mu |
| `hedef_kitle` | Seviye, ton ve ornek secimi sayfanin takipcisine oturuyor mu |
| `gorsel_kalite` | Kompozisyon, hiyerarsi, okunabilirlik. **Harf hatasi ve sablon/marka sapmasi bu dala girmez** — kirik bir baslik ya da tasan bir metin girer, cunku onlar okunabilirligi bozar |

**Puan yayin sirasini belirler.** Havuzun tamami puana gore siralanir ve
tepeden baslanir; kategori yalnizca esit puanlilar arasinda konusur. Puan
**elemez** — hicbir post puani yuzunden havuzdan cikmaz — ama puani olmayan
ya da bayatlamis post havuzun tamaminin sonuna duser, yani puanli tek bir
aday kaldigi surece secilmez. Bozuk bir `puan.json` de secimi durdurmaz:
post puansiz muamelesi gorur ve `aday_sec.py --durum` ciktisinda
`puan_dagilimi.bozuk` altinda sayilir.

### Kullanim

```bash
S=.claude/skills/insta-yayinla/scripts
python $S/puanla.py                  # puansiz + bozuk + bayat postlar
python $S/puanla.py --bayat          # olcut surumu eskimis olanlar
python $S/puanla.py --sema           # dallar ve formul
python $S/puanla.py --slug dizi/my-bad --malzeme   # tek postun puani + caption
python $S/aday_sec.py --durum        # havuzun puan dagilimi ve ortalamasi
```

## Elle mudahale

**Bir postu tekrar yayinlanabilir yapmak** — Instagram'dan sil, sonra `esitle.py`
calistir. Defterden kaydi kendisi dusurur ve post havuza doner. *Sadece defterden
silmek yetmez: post hala Instagram'da duruyorsa `esitle.py` kaydi geri ekler.*

**Atlanmis bir postu geri almak** — `durum.json` > `atlananlar` icindeki kaydi sil.

**Yarinin postunu elle secmek** — `durum.json` > `sonraki` alanina slug yaz
(`"sonraki": "seviye-testi/a2"`). Bir sonraki calisma puan sirasina bakmadan
onu siraya koyar ve alani temizler. Post yine dogrulamadan gecmek zorunda:
gecemezse sabit durur, sira normal isler.

**Bekleyen onayi iptal etmek** — `durum.json` > `bekleyen` degerini `null` yap.
SaaS tarafindaki post kaydi durmaya devam eder; istersen orada da sil.

**Defter ile Instagram ayristiginda** — `esitle.py --kuru` ile once farki gor,
sonra `esitle.py` ile uygula. Iki yonlu calisir.
