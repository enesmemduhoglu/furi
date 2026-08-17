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
| `sure_dolanlar` | SaaS onay linki yanitsiz kalip suresi dolan postlarin sayaci (`{"slug": 2}`). Suresi dolmak postu **elemez** — post havuzda kalir, sirasi gelince yeniden onerilir. Ancak sayac 3'e ulasirsa `atlananlar`'a gecer. Post yayinlaninca sayaci silinir. |
| `atlananlar` | Onay sayfasinda reddedilen ya da 3 kez ust uste yanitsiz kalan postlar. Bir daha aday olarak secilmezler. Tekrar siraya girmesi icin buradan silmek yeterli. |
| `token` | Instagram token'inin yenileme/bitis tarihleri (`ig_token.py` yazar). Yayini SaaS yaptigi icin **bu kayit SaaS'taki kopyayi takip etmez** — token yenilenince SaaS'taki `Client.instagramAccessToken` da elle guncellenmeli. |

## Elle mudahale

**Bir postu tekrar yayinlanabilir yapmak** — Instagram'dan sil, sonra `esitle.py`
calistir. Defterden kaydi kendisi dusurur ve post havuza doner. *Sadece defterden
silmek yetmez: post hala Instagram'da duruyorsa `esitle.py` kaydi geri ekler.*

**Atlanmis bir postu geri almak** — `durum.json` > `atlananlar` icindeki kaydi sil.

**Bekleyen onayi iptal etmek** — `durum.json` > `bekleyen` degerini `null` yap.
SaaS tarafindaki post kaydi durmaya devam eder; istersen orada da sil.

**Defter ile Instagram ayristiginda** — `esitle.py --kuru` ile once farki gor,
sonra `esitle.py` ile uygula. Iki yonlu calisir.
