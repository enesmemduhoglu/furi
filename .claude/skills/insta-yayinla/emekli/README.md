# emekli/ — kullanimdan kalkmis parcalar

Buradaki hicbir sey **normal akista calismaz**. Silinmediler cunku geri donus
yolunun acik kalmasi, dosyanin yok olmasindan daha degerli: bir gun SaaS
kapanirsa ya da yayin oraya tasinmadan onceki davranis gerekirse, calisir
haldeki kod burada duruyor.

Bugunku akis: [`../SKILL.md`](../SKILL.md) ·
mimari gerekce: [`../SAAS-ENTEGRASYON-PLANI.md`](../SAAS-ENTEGRASYON-PLANI.md)

---

## `apps-script/` — Gmail onay tetikleyicisi

**Emeklilik tarihi:** 2026-08-16 · **Yerine gecen:** content-approval-saas

### Ne yapiyordu

```
Sen: [FURI-ONAY] mailine "EVET" yanitla
   |
   v  <= 60 sn
Apps Script (Google sunucusunda, dakikada bir)
   Gmail'i tarar, EVET/HAYIR okur, GitHub issue #1'e yorum atar
   |
   v
GitHub issue_comment webhook -> Claude rutini -> Instagram'a yayin
```

### Neden emekli oldu

Zincirin son halkasi **hicbir zaman guvenilir calismadi**. Webhook teslimati dort
ayri yapilandirmada denendi, hicbiri rutini tetiklemedi. Apps Script kendi isini
14 saniyede yapiyordu ama Claude rutini calismadigi icin yayin olmuyordu.

Cozum zinciri onarmak degil, **kaldirmak** oldu: yayin cagrisi onayin gerceklestigi
yere — SaaS'in onay endpoint'ine — tasindi. Onay ve yayin artik ayni HTTP
isteginde oluyor, olculen sure ~11 saniye. Tetiklenecek bir sey kalmadigi icin
tetikleme sorunu da kalmadi.

### Nasil devre disi birakildi

- `onay-tetikleyici.gs` icinde `var EMEKLI = true;` — bayrak true oldugu surece
  `onayKontrol()`, `zamanlayiciKur()` ve `baglantiTesti()` oldugu yerde durur.
  Dosya kazayla deploy edilse bile Gmail taranmaz, GitHub'a yorum atilmaz.
- `KURULUM-APPS-SCRIPT.md` basina "uygulama" uyarisi kondu.

**Google tarafinda ne kaldi:** bu repo Apps Script projesini kaldiramaz. Eger
proje hala deploy'daysa dakikalik zamanlayicisi bos yere calisiyordur — zararsiz,
ama temizlemek istersen asagidaki "Google tarafini kapatmak" adimlarina bak.

### Google tarafini kapatmak (elle, opsiyonel)

1. [script.google.com](https://script.google.com) > `furi-onay-tetikleyici` projesi
2. Sol menu **Triggers** (saat ikonu) > `onayKontrol` tetikleyicisini sil
3. **Project Settings > Script Properties** > `FURI_GITHUB_TOKEN` degerini sil
4. GitHub'da tetikleyici issue (#1) kapatilabilir

> Adim 3'u atlama: o property canli bir GitHub token'i tutuyor. Zincir
> kullanilmiyorsa token da durmamali.

### Geri donus

Gmail/Apps Script yoluna donmek gerekirse:

1. `onay-tetikleyici.gs` icinde `EMEKLI = false` yap
2. Dosyayi script.google.com'daki projeye yapistir,
   `KURULUM-APPS-SCRIPT.md` adimlarini uygula (Script Properties + zamanlayici)
3. `SKILL.md` Faz 2'yi eski haline dondur: `saas_gonder.py` yerine onay maili
   gonderme + Gmail'de `EVET`/`HAYIR` ayristirma
4. Yayin adimini geri ekle: `ig_yayinla.py --isaretle` -> `--slug` -> `--dogrula`
   (script'ler duruyor, silinmediler)

Bu adimlarin tamaminin git gecmisinde calisir hali var:

```bash
git show fd265d7^:.claude/skills/insta-yayinla/SKILL.md   # yayin yapan surum
git show fd265d7                                          # gecisin kendisi
```

---

## Emekli olmayan ama normal akista cagrilmayan komutlar

Bunlar `emekli/` icinde **degil** — `scripts/` altinda duruyorlar ve calisir
haldeler. Skill onlari kendiliginden cagirmaz; elle teshis/kurtarma icindirler.

| Komut | Ne zaman |
|---|---|
| `ig_yayinla.py --kontrol` | Instagram token'i saglam mi |
| `ig_yayinla.py --dogrula K/S` | Yarida kalmis bir yayin gercekten atilmis mi |
| `ig_yayinla.py --slug K/S` | SaaS calismiyorken elle yayin (son care) |
| `ig_token.py --kontrol/--yenile` | Token kac gun gecerli / yenile |

`ig_yayinla.py --paket` bir istisna: ciktisini **yalnizca** emekli Apps Script
zinciri tuketiyordu. Komut duruyor ama uyari basiyor.
