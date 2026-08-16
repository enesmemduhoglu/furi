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

Instagram'a **gercekten yuklenmis** postlarin kalici kaydi. "Bu post daha once atildi mi?"
sorusunun tek dogruluk kaynagi. Buradan bir kayit silmek, o postun tekrar yayinlanabilir
hale gelmesi demektir.

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
| `bekleyen` | Onay maili gonderilmis ama henuz yanit gelmemis post. Bosta iken `null`. |
| `yayin_denemesi` | `media_publish` cagrisindan hemen once yazilir, basarili olunca silinir. Dolu kalmissa bir onceki calisma yayin sirasinda kesilmis demektir — bir sonraki calisma once Instagram'a sorup gercekten atilip atilmadigini kontrol eder. **Cift yayini engelleyen mekanizma budur, elle silinmemeli.** |
| `son_yayin` | Son basarili yayinin zamani. Iki postun ayni saate yigilmamasi icin kullanilir (min 4 saat ara). |
| `bugun` | Takvim gunu basina yayin sayaci. Tarih degisince sifirlanir. |
| `son_stok_uyarisi` | "Post stogu azaliyor" mailinin gunde birden fazla gitmemesi icin. |
| `sure_dolanlar` | Onay maili yanitsiz kalip suresi dolan postlarin sayaci (`{"slug": 2}`). Suresi dolmak postu **elemez** — post havuzda kalir, sirasi gelince yeniden onerilir. Ancak sayac 3'e ulasirsa `atlananlar`'a gecer. Post yayinlaninca sayaci silinir. |
| `atlananlar` | Onay mailine "HAYIR" yaniti verilen ya da 3 kez ust uste yanitsiz kalan postlar. Bir daha aday olarak secilmezler. Tekrar siraya girmesi icin buradan silmek yeterli. |

## Elle mudahale

**Bir postu tekrar yayinlanabilir yapmak** — `yayinlananlar.json` icindeki kaydi sil.

**Atlanmis bir postu geri almak** — `durum.json` > `atlananlar` icindeki kaydi sil.

**Bekleyen onayi iptal etmek** — `durum.json` > `bekleyen` degerini `null` yap.

**Kilitlenmis bir yayin denemesini temizlemek** — once Instagram'da postun gercekten atilip
atilmadigina **bak**, sonra `yayin_denemesi` degerini `null` yap. Atilmissa ayrica
`yayinlananlar.json`'a elle kayit ekle, yoksa post ikinci kez atilir.
