# TODOS

Son guncelleme: 2026-08-18.

Bu dosya furi1'in acik islerini tutar. Otomasyonun anlik durumu burada degil,
`otomasyon/durum.json` icinde.

---

## Acik isler

### [ ] Post puanlama sistemi — Claude urettigi ve repoda duran her posta puan verir

**Neden:** 2026-08-18 sabahi rutin `karistirilan/borrow-vs-lend` postunu siraya
koydu, post onay sayfasinda "cop post" gerekcesiyle reddedildi ve SaaS kaydi
silindi. Kusur otomasyonda degil: rotasyon **sirasi gelen** postu seciyor,
**iyi olan** postu degil. Havuzdaki kalite farki bugun hicbir yerde olculmuyor,
dolayisiyla zayif bir post da guclu bir post da esit sansla onaya gidiyor. Tek
suzgec insanin onay ekraninda "hayir" demesi — yani kalite kontrolu akisin en
sonunda ve elle yapiliyor.

**Yapilacak:**

1. **Yeni uretilen postlar puanlanir.** `insta-ingilizce` akisi (WORKFLOW.md) bir
   postu bitirdiginde Claude o posta puan verir; puan post ile birlikte commit
   edilir.
2. **Repoda hazirda duran postlar da puanlanir.** Bir session icinde havuzdaki
   yayinlanmamis postlar taranip geriye donuk puanlanir; boylece rotasyon ilk
   gunden puanli bir havuz uzerinde calisir.
3. **Puan tek sayi degil, dallara ayrilir.** En az su dallar:
   - `ilgi_cekicilik` — konu ve kanca kaydirmayi durdurur mu, kaydetmeye/paylasmaya deger mi
   - `yazim` — caption ve slayt metinlerinde imla, dilbilgisi, Turkce-Ingilizce dogruluk
   - `gorsel_kalite` — sablon tutarliligi, okunabilirlik, gorseldeki harf hatalari
     (bkz. `HATA-RAPORU.md` — bu dosyadaki bulgular puanin girdisi olmali)
   - dallar cogaltilabilir: ogretici deger, ozgunluk, hedef kitleye uygunluk
   Dal puanlarinin yaninda kisa bir gerekce metni de tutulmali; ciplak sayi
   "neden dusuk" sorusunu cevaplamiyor.

**Karara baglanmasi gerekenler (uygulamadan once):**

- **Nerede saklanir?** Post klasorunde `puan.json` (icerikle birlikte tasinir,
  git gecmisinde gorunur) mu, yoksa `otomasyon/puanlar.json` (tek dosya, toplu
  okuma kolay) mi? Ilki icerige daha yakin, ikincisi otomasyonun okumasi icin
  daha ucuz.
- **Aday secimini etkiler mi?** Uc secenek: (a) sadece bilgi, rotasyon aynen
  kalir; (b) esigin altindaki post aday havuzundan elenir; (c) rotasyon icinde
  siralamayi puan belirler. Elemeye gidilirse esik ve "elenen post ne olur"
  (yeniden uretim mi, arsiv mi) tanimlanmali.
- **Yeniden puanlama ne zaman?** Puan model ve olcut degistikce kayar; eski
  puanin ne zaman bayat sayilacagi ve kimin tazeleyecegi belirsiz.
- **Puanlayan ile ureten ayni model.** Kendi urettigine puan veren bir sistem
  yumusak davranabilir; olcutlerin somut ve kontrol edilebilir olmasi
  (ornek: "gorselde harf hatasi var mi" gibi ikili sorular) bu riski azaltir.

**Dokunacagi yerler:** `WORKFLOW.md` (uretim akisina puanlama fazi),
`.claude/skills/insta-yayinla/scripts/aday_sec.py` (puan aday secimine
girecekse), `otomasyon/README.md` (yeni bir state dosyasi eklenirse semasi).
