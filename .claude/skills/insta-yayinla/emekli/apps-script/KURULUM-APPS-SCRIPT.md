> # ⛔ EMEKLI — bu kurulum artik yapilmiyor
>
> Onay ve yayin `content-approval-saas`'a tasindi (2026-08-16). Onaya basildigi
> an yayin ayni HTTP isteginde yapiliyor, yani Gmail'i izleyip Claude rutinini
> tetikleyen bu zincire gerek kalmadi.
>
> Belge **silinmedi**: geri donus yolu acik kalsin diye burada duruyor.
> Bugunku akis ve geri donus adimlari: [`../README.md`](../README.md)
>
> Asagidaki adimlari **uygulama**. Yalnizca tarihsel referans.

---

# Anlik onay tetikleyicisi — kurulum

Amac: maile **"EVET"** yazdigin an postun yayinlanmasi. Claude'un saatlerce beklemesi
ya da bos yere yoklama yapmasi gerekmiyor.

```
Sen: maile "EVET" yanitla
   |
   v  <= 60 saniye        Google'in sunucusunda, bedava
Apps Script
   - Gmail'de [FURI-ONAY] konulu thread'leri tarar
   - alintilanmis kismi atip yaniti okur
   - EVET/HAYIR yakalarsa GitHub issue #1'e yorum atar
   |
   v  saniyeler
GitHub issue_comment webhook -> Claude rutini
   |
   v
Rutin: onayi Gmail'den KENDI dogrular -> Instagram'a yayinlar
```

Zincirdeki her halka kendi isini bagimsiz dogrular. Apps Script yanlislikla tetiklese
bile rutin Gmail'de gercek bir "EVET" bulamazsa yayin yapmaz.

**Zaten kurulu olanlar** (bunlari yapmana gerek yok):

- Claude rutini `furi-insta-yayinla` — https://claude.ai/code/routines/trig_01TtprvNfdZd5DDEfR8uDCRj
- GitHub webhook baglantisi (`issue_comment` + `repository_dispatch`)
- Tetikleyici issue — https://github.com/enesmemduhoglu/furi/issues/1
- Claude GitHub App (sen kurdun)

Asagidaki iki adim kaldi.

---

## Adim 2 — GitHub token'i

Apps Script'in issue'ya yorum atabilmesi icin bir token gerekiyor. **Fine-grained**
token kullaniyoruz; sadece bu repoya ve sadece issue yazmaya yetkili olacak.

1. [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new)
2. Alanlari doldur:

   | Alan | Deger |
   |---|---|
   | **Token name** | `furi-apps-script` |
   | **Expiration** | 1 year (ya da No expiration) |
   | **Resource owner** | `enesmemduhoglu` |
   | **Repository access** | **Only select repositories** -> `furi` |

3. **Permissions** > *Repository permissions* bolumunde tek bir izin ver:

   | Izin | Deger |
   |---|---|
   | **Issues** | **Read and write** |

   Baska hicbir izne dokunma. (`Metadata: Read` otomatik eklenir, normal.)

4. **Generate token** > cikan `github_pat_...` degerini kopyala.

> Token sadece bu repoda issue yorumu yazabiliyor. Sizsa bile kimse kodunu
> degistiremez, repoya push edemez, baska repolarini goremez.

---

## Adim 3 — Apps Script projesi

1. [script.google.com](https://script.google.com) > **New project**
2. Proje adini `FURI onay tetikleyici` yap (sol ustteki "Untitled project"e tikla).
3. Soldaki `Code.gs` dosyasinin **icindekileri tamamen sil**, yerine bu klasordeki
   [`onay-tetikleyici.gs`](onay-tetikleyici.gs) dosyasinin tamamini yapistir. Kaydet
   (Ctrl+S).
4. Sol menu **Project Settings** (disli ikonu) > en altta **Script Properties** >
   **Add script property**:

   | Property | Value |
   |---|---|
   | `FURI_GITHUB_TOKEN` | adim 2'de kopyaladigin `github_pat_...` |

   **Save script properties**.

   > Token'i koda yapistirma. Script Properties'te durursa kod paylasilsa bile
   > token disari sizmaz.

5. Editore don. **Kodun hemen ustundeki** arac cubugundan fonksiyonu sec ve calistir:

   ```
    ↩  ↪   💾 Kaydet   ▷ Calistir   🐞 Hata Ayikla   [ zamanlayiciKur ▾ ]   Yurutme gunlugu
                           ↑                              ↑
                       buna bas                    once buradan sec
   ```

   > **"Dagit" (Deploy) butonuna DOKUNMA.** O sag ust kosede, ayri bir menu ve
   > web uygulamasi / API / eklenti / kitaplik yayinlamak icin. Bu script bunlarin
   > hicbiri degil — arka planda kendi kendine calisan bir zamanlayici. Dagitim
   > yapmana gerek yok.

   - Google izin isteyecek: **Izinleri inceleyin** > hesabini sec > "Google bu
     uygulamayi dogrulamadi" ekraninda **Gelismis** > **FURI onay tetikleyici
     sayfasina git (guvenli degil)** > **Izin ver**.
     (Uyari normal: kendi yazdigin, Google'a dogrulatilmamis bir script'e kendi
     hesabinda izin veriyorsun. Istedigi yetki: Gmail okuma + disari istek atma.)
   - **Yurutme gunlugu** panelinde sunu gormelisin:
     `Zamanlayici kuruldu: onayKontrol her dakika calisacak.`
   - Dogrulamak icin: sol menu **saat ikonu (Tetikleyiciler)** > listede
     `onayKontrol` / Zamana dayali / Dakika zamanlayici satiri gorunmeli.

Bu kadar. Script artik dakikada bir Gmail'ine bakiyor.

**Arayuz karsiliklari** (Google hesabin Turkce ise):

| Ingilizce | Turkce |
|---|---|
| Run | Calistir |
| Deploy | Dagit — *kullanilmiyor* |
| Project Settings | Proje Ayarlari |
| Script Properties | Komut Dosyasi Ozellikleri |
| Triggers | Tetikleyiciler |
| Execution log | Yurutme gunlugu |

---

## Dogrulama

Sirayla, her biri bir oncekini kanitlar:

**1. Gmail tarafi** — fonksiyon listesinden `kuruTest` > **Calistir**.
Hicbir sey tetiklemez, sadece ne okudugunu gosterir. Henuz onay maili yoksa
`0 thread bulundu.` yazar; bu dogru sonuc.

**2. GitHub tarafi** — `baglantiTesti` > **Calistir**.
[issue #1](https://github.com/enesmemduhoglu/furi/issues/1)'e bir test yorumu duser ve
rutin gercekten calisir. Bekleyen post olmadigi icin rutin bir sey yayinlamaz.
Calistigini [rutin sayfasindan](https://claude.ai/code/routines/trig_01TtprvNfdZd5DDEfR8uDCRj)
gorebilirsin.

**3. Ucdan uca** — rutin acildiktan sonra ilk onay maili geldiginde "EVET" yanitla ve
bir dakika icinde postun cikmasini bekle.

---

## Sorun giderme

**`FURI_GITHUB_TOKEN tanimli degil`** — adim 3.4 atlanmis ya da property adi yanlis
yazilmis. Buyuk/kucuk harfe duyarli.

**`TETIKLEME BASARISIZ HTTP 403`** — token'in **Issues: Read and write** izni yok ya da
repository access `furi`'yi kapsamiyor. Adim 2.3'u kontrol et.

**`TETIKLEME BASARISIZ HTTP 404`** — token dogru repoyu gormuyor (genelde
*Repository access* "Only select repositories" secilmis ama `furi` isaretlenmemis).

**Yorum dusuyor ama rutin calismiyor** — Claude GitHub App'in `furi` reposunda kurulu
oldugunu dogrula: [github.com/apps/claude](https://github.com/apps/claude/installations/select_target).
Ayrica rutinin **enabled** oldugundan emin ol.

**"EVET" yazdim ama tetiklenmedi** — script islenmis thread'leri `furi-islendi`
etiketiyle isaretliyor. Ayni thread'i tekrar denemek icin Gmail'de o etiketi thread'den
kaldir. Belirsiz yanitlar (`bence olur` gibi) bilerek tetiklemez; net `EVET` yaz.

**Cok fazla tetikleme** — `zamanlayiciKur`'u tekrar calistir; eski zamanlayicilari
silip tek bir tane birakir.

**Script'i durdurmak** — Apps Script > sol menu **Tetikleyiciler** (saat ikonu) >
`onayKontrol` satirinin sagindaki uc nokta > **Tetikleyiciyi sil**.

**"Dagit" menusunde tur secmemi istiyor** — yanlis butondasin. Dagitim yapilmiyor;
fonksiyonu kodun ustundeki **Calistir** ile calistiriyorsun. Bkz. adim 3.5.

---

## Gizlilik notu

- GitHub token'i Script Properties'te, Instagram token'i `.env` ve bulut ortami
  secret'inda durur. Ikisi de repoya girmez (repo public).
- Apps Script sadece `[FURI-ONAY]` konulu mailleri okur; baska maillerine bakmaz.
- GitHub issue'sundaki yorumlar mail konusunu ve karari icerir, caption veya gorsel
  icermez.
