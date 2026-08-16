# content-approval-saas → Instagram yayın entegrasyonu

> Bu plan **başka bir session'da uygulanmak** üzere yazıldı. Çalışılacak repo:
> `enesmemduhoglu/content-approval-saas` (branch: `master`). İkinci repo
> `enesmemduhoglu/furi` tarafında da küçük bir değişiklik var, o da sonda.

---

## Neden

`furi` reposunda Instagram postları üretiliyor ve `insta-yayinla` skill'i bunları
onaydan geçirip yayınlıyor. Akışın tamamı çalışıyor **tek bir halka hariç**: onay
geldiği anda yayını tetikleyecek mekanizma yok.

Denenen ve elenen yollar:

| Yol | Sonuç |
|---|---|
| Claude cloud routine + GitHub webhook (`issue_comment`, `repository_dispatch`, `@claude`, filtreli) | Dört yapılandırma denendi, **hiçbiri teslim edilmedi** |
| Cron sıklaştırma | Zamanlanmış rutinlerin **minimum aralığı 1 saat** — 2 dk şartını veremez |
| Gmail Apps Script | Onayı **14 saniyede** yakalıyor ✓ ama Claude rutinini tetikleyemiyor ✗ |

Hedef: onaydan yayına geçen süre **2 dakikanın altında**.

Çözüm: yayın çağrısını Claude rutininden çıkarıp **onayın gerçekleştiği yere**
taşımak. Onay zaten bu SaaS'ta yapılabiliyor; yayını da oraya koyunca aradaki
tetikleme sorunu tamamen ortadan kalkıyor — onay ve yayın aynı HTTP isteğinde olur.

**Beklenen gecikme: ~2-10 saniye.**

---

## Mevcut durum (bu oturumda doğrulandı, varsayım değil)

### content-approval-saas

Next.js 15 + Prisma + Postgres, Vercel'de canlı: https://content-approval-saas.vercel.app

Elimize yarayan, **hazır** olanlar:

- `src/lib/scoped-db.ts` → `createWithApprovalLink({ clientId, imageUrls, caption })`
  **`imageUrls` zaten `string[]`** — Blob'a yükleme yapmadan `raw.githubusercontent.com`
  URL'lerini doğrudan verebiliriz. `PostImage.url` sadece bir string.
- `src/app/api/approve/[token]/route.ts` → onay `POST`'u `$transaction` içinde
  `updateMany({ where: { id, status: "pending" } })` ile yapılıyor. Bu **koşullu
  UPDATE** aynı anda gelen ikinci kararı 409 ile kesiyor. Çift yayın koruması
  buradan bedavaya geliyor.
- `ApprovalAudit` — IP + aksiyon + zaman damgası zaten yazılıyor.
- Token 7 gün geçerli, süresi dolan link 410 dönüyor.
- Rate limit: public onay endpoint'i IP başına dakikada 10 istek.

**Eksik olanlar** (bu planın konusu):

1. **Makine erişimi yok.** `POST /api/posts` `auth()` ile NextAuth/Google oturumu
   istiyor. Bulut rutini OAuth akışı yürütemez.
2. **Onay sonrası hiçbir şey olmuyor.** Route karar veriyor, audit yazıyor,
   `{ status }` dönüyor. Dışarı bildirim yok, yayın yok.

### furi

- 34 post, `<kategori>/<slug>/{1.jpg…N.jpg, caption.md}`
- Görseller **public raw URL'de**, 200 dönüyor, JPEG, 1920×2400 (4:5)
- Instagram Graph API ile yayın **çalışıyor ve kanıtlandı**:
  https://www.instagram.com/p/DcGQsbviHtT/ — 1920×2400 kaynak, Instagram 1440×1800'e
  küçültüyor, **oran korunuyor, kırpma yok**. Ek görsel işleme gerekmiyor.
- Instagram hesabı: `furkanteacherteaching`, IG_USER_ID `17841441566401393`
- Token: Instagram Login yolu (`IGAA…`/`IGAG…`), 60 gün ömürlü,
  `GET /refresh_access_token` ile yenileniyor

---

## Tasarım kararları

### 1. Instagram kimlik bilgisi `Client` üzerinde tutulur, env'de değil

Env değişkeni tek bir hesaba bağlar. `Client` üzerine koyunca ajans modeli bozulmaz:
her müşterinin kendi Instagram'ı olur, bu da ürünün doğal bir sonraki özelliği.

Ayrıca **güvenli varsayılan** sağlar: `instagramUserId` boş olan müşterilerde onay
hiçbir şey yayınlamaz, sadece bugünkü gibi durumu `approved` yapar. Mevcut
kullanıcılar için davranış aynen korunur.

### 2. Yayın onay transaction'ından SONRA, ayrı adımda yapılır

Onay kaydı **asla** Instagram hatası yüzünden kaybolmamalı. Sıra:

```
$transaction:  status = approved  +  audit          ← burası commit olur
sonra:         Instagram API çağrısı                ← başarısız olabilir
sonra:         publishStatus + igMediaId güncellenir
```

Yayın patlarsa onay yerinde durur, `publishStatus = "failed"` olur, tekrar denenebilir.
Tersi olsaydı (yayın transaction içinde) bir Instagram hatası onayı da geri alırdı.

### 3. Çift yayın koruması `publishStatus` üzerinden koşullu UPDATE

Mevcut `status` koruması gibi:

```ts
updateMany({ where: { id, publishStatus: "idle" }, data: { publishStatus: "publishing" } })
// count === 0  →  başkası zaten yayınlıyor, çık
```

`furi` tarafındaki `ig_yayinla.py --dogrula` de emniyet ağı olarak kalır: takılı
kalmış bir `publishing` kaydı için Instagram'a sorup gerçekten atılıp atılmadığını
kontrol eder.

### 4. Kullanıcı yayını bekler (arka plana atılmaz)

Karusel için 8 görsel = ~10 API çağrısı, tahminen 5-15 saniye. Onay sayfasında
"Yayınlanıyor…" göstermek, arka plan işi kurmaktan hem basit hem güvenilir: hata
anında kullanıcıya görünür. `export const maxDuration = 60` gerekir.

---

## SaaS tarafında yapılacaklar

### A. Şema — `prisma/schema.prisma`

```prisma
model Client {
  // … mevcut alanlar
  instagramUserId      String?   // IG professional account id
  instagramAccessToken String?   // long-lived token (60 gün)
  instagramTokenExpiry DateTime?
}

enum PublishStatus {
  idle        // yayın hedefi yok ya da henüz sıra gelmedi
  publishing  // devam ediyor (çift yayın kilidi)
  published
  failed
  skipped     // müşteride Instagram bağlı değil
}

model Post {
  // … mevcut alanlar
  publishStatus PublishStatus @default(idle)
  igMediaId     String?
  igPermalink   String?
  publishError  String?
  publishedAt   DateTime?
}
```

Migration: `npx prisma migrate dev --name instagram_publishing`

`PostImage.url` **değişmiyor** — raw URL'ler oraya olduğu gibi yazılacak.

### B. Makine erişimi — API anahtarı

**Yeni dosya: `src/lib/api-key.ts`**

```ts
// Authorization: Bearer <key>  →  { agencyId } | null
// Anahtar env'den okunur: FURI_API_KEY + FURI_API_AGENCY_ID
// Dönen nesne getScopedDb()'nin beklediği ScopedSession şeklinde olmalı;
// böylece IDOR koruması aynen geçerli kalır.
export async function authenticateApiKey(request: Request): Promise<ScopedSession | null>
```

Kritik: **`getScopedDb()` bypass edilmeyecek.** API anahtarı sadece `agencyId`
üretir, sorgular yine scoped db üzerinden gider. `src/lib/scoped-db.ts`'deki
"route handler'lar ham `db.*` çağırmaz" kuralı korunur.

Anahtar karşılaştırması timing-safe olmalı (`crypto.timingSafeEqual`).

**Değişiklik: `src/app/api/posts/route.ts`**

`POST` handler'ının başındaki oturum kontrolü şuna dönüşür:

```ts
const session = (await auth()) ?? (await authenticateApiKey(request));
if (!session?.agencyId) return 401;
```

Ayrıca **JSON gövde desteği** eklenir (mevcut `multipart/form-data` yolu aynen kalır):

```jsonc
// Content-Type: application/json
{
  "clientId": "…",
  "caption": "…",
  "imageUrls": ["https://raw.githubusercontent.com/…/1.jpg", "…"],
  "externalRef": "dizi/long-story-short"   // opsiyonel, furi slug'ı
}
```

`imageUrls` geldiğinde `uploadPostImage()` **atlanır** ve URL'ler doğrudan
`createWithApprovalLink`'e geçer. Doğrulama: her URL `https://`, izinli host
(`raw.githubusercontent.com`), en fazla `MAX_IMAGES_PER_POST`.

> `externalRef` alanı `Post`'a eklenirse (`String?`, indexli) furi tarafı
> "bu slug daha önce gönderildi mi" diye sorabilir. Zorunlu değil ama tavsiye edilir.

### C. Yayın çekirdeği — `src/lib/instagram.ts` (yeni)

`furi/.claude/skills/insta-yayinla/scripts/ig_api.py` ve `ig_yayinla.py`'nin
TypeScript karşılığı. **Referans olarak o dosyalara bak** — akış ve hata yönetimi
orada çalışır halde duruyor.

```ts
const HOST = "graph.instagram.com";
const VERSION = "v23.0";

// Tek görsel:
//   POST /{igUserId}/media          image_url, caption, alt_text        → creationId
//   POST /{igUserId}/media_publish  creation_id                         → mediaId
//
// Karusel (N>1):
//   her slayt: POST /{igUserId}/media  image_url, is_carousel_item=true, alt_text
//   containerBekle(childId)  ← status_code === "FINISHED" olana kadar
//   POST /{igUserId}/media          media_type=CAROUSEL, children=<ids>, caption
//   containerBekle(carouselId)
//   POST /{igUserId}/media_publish  creation_id
//   GET  /{mediaId}?fields=permalink
export async function publishToInstagram(input: {
  igUserId: string;
  accessToken: string;
  imageUrls: string[];
  caption: string;
  altTexts?: string[];
}): Promise<{ mediaId: string; permalink: string }>;
```

Uyulması gereken sınırlar (hepsi doğrulandı):

| Sınır | Değer |
|---|---|
| Format | yalnızca JPEG |
| Public URL | zorunlu — Instagram görseli kendisi çeker |
| En-boy | 4:5 – 1.91:1 (bizimkiler 4:5, sorunsuz) |
| Azami genişlik | 1440 px (fazlası otomatik küçültülür, kırpılmaz) |
| Dosya | 8 MB |
| Karusel | en fazla 10 görsel |
| Yayın kotası | 24 saatte 100 post |

`containerBekle` atlanmamalı: Instagram görseli çekmeden `media_publish` çağrılırsa
"Media ID is not available" hatası gelir. Poll aralığı 2s'den başlayıp 10s'e kadar
büyütülür, azami ~90 saniye.

Hatalar `IGError` olarak sarılıp Meta'nın tam JSON'u (`code`, `error_subcode`,
`fbtrace_id`) korunmalı — teşhis için gerekli.

### D. Onay akışına bağlama — `src/app/api/approve/[token]/route.ts`

Mevcut `$transaction` bloğuna **dokunma**. Ondan sonra, `NextResponse.json` dönmeden
önce şu ekleniyor:

```
newStatus === "approved" değilse       → mevcut davranış, dokunma
client.instagramUserId yoksa           → publishStatus = "skipped", dön
publishStatus'u koşullu "publishing" yap
  count === 0 ise                      → başkası yayınlıyor, dön
publishToInstagram(...)
  başarılı → publishStatus="published", igMediaId, igPermalink, publishedAt
  hata     → publishStatus="failed", publishError = mesaj
dönen JSON'a publishStatus + igPermalink eklenir
```

Ve dosyanın başına:

```ts
export const maxDuration = 60;
```

Alt text: `PostImage`'a `altText String?` eklenip API'den alınabilir. Erişilebilirlik
için değerli ama **v1'de opsiyonel** — `furi` tarafında alt text'ler zaten
`caption.md` içinde hazır duruyor.

### E. Onay sayfası — `src/app/approve/[token]/`

- Onaya basınca "Yayınlanıyor…" durumu (istek 5-15 sn sürebilir)
- Yanıt geldiğinde: `published` → permalink'e link; `failed` → hata mesajı +
  "tekrar dene"; `skipped` → sadece onaylandı bilgisi
- Bu müşteride Instagram bağlıysa buton metni "Onayla ve Yayınla" olabilir

### F. Ortam değişkenleri

| Değişken | Nerede | Ne için |
|---|---|---|
| `FURI_API_KEY` | Vercel env | Makine erişimi anahtarı |
| `FURI_API_AGENCY_ID` | Vercel env | Anahtarın hangi ajansa ait olduğu |

Instagram token'ı env'e **girmiyor** — `Client` kaydında duruyor (karar 1).

`.env.example` güncellenmeli.

### G. Testler

Repo Vitest + Playwright kullanıyor, mevcut `route.test.ts` desenini izle.

- `api-key.ts`: geçerli/geçersiz/eksik anahtar, timing-safe karşılaştırma
- `posts` JSON yolu: `imageUrls` ile post oluşuyor, host allowlist'i dışı reddediliyor,
  API anahtarıyla gelen istek **başka ajansın** `clientId`'sine yazamıyor (IDOR)
- `instagram.ts`: `fetch` mock'lanarak tek görsel + karusel akışı, `FINISHED`
  beklemesi, hata sarmalama
- `approve` route: Instagram'sız müşteride `skipped`; başarılı yayında alanların
  dolması; **aynı anda iki onay isteğinde tek yayın** (en kritik test)

---

## furi tarafında yapılacaklar

`.claude/skills/insta-yayinla/` içinde:

1. **SKILL.md** — Faz 2 değişir. Artık Gmail ile onay maili göndermek yerine
   SaaS'a post oluşturuluyor:

   ```
   POST https://content-approval-saas.vercel.app/api/posts
   Authorization: Bearer $FURI_API_KEY
   Content-Type: application/json
   { clientId, caption, imageUrls, externalRef: <slug> }
   ```

   Onay maili SaaS tarafından gidiyor. `durum.json > bekleyen` alanına SaaS'ın
   dönen `post.id`'si yazılır.

2. **Faz 1 ve Faz 3 sadeleşir.** Gmail'de yanıt ayrıştırma, `EVET`/`HAYIR` eşleştirme,
   6 saatlik süre kontrolü, `ig_yayinla.py --isaretle/--slug` — hepsi gereksizleşir.
   Yayını SaaS yapıyor. Rutin sadece `GET /api/posts` ile durumu okuyup
   `yayinlananlar.json` defterine işler.

3. **Silinecek/emekliye ayrılacak:** `apps-script/` klasörünün tamamı. Gmail
   tetikleme zinciri bu tasarımda gereksiz.

4. **Korunacak:** `aday_sec.py` (kategori rotasyonu, caption ayrıştırma, URL
   doğrulama) ve `furi_ortak.py`. Bunlar hâlâ seçimi yapan taraf.
   `ig_yayinla.py --dogrula` emniyet ağı olarak kalır.

5. **Bir kerelik kurulum:** SaaS'ta bir `Client` oluştur (`Furkan Teacher`,
   `eneshan034@gmail.com`) ve `instagramUserId` + `instagramAccessToken` alanlarını
   doldur. `clientId`'yi furi tarafında `.env`'e yaz.

---

## Doğrulama

Sırayla, her adım bir öncekini kanıtlar:

1. **Şema** — `npx prisma migrate dev`, ardından `npx prisma studio` ile yeni
   alanları gör.
2. **API anahtarı** — anahtarsız `POST /api/posts` 401; yanlış anahtar 401; doğru
   anahtar 201. Farklı ajansın `clientId`'siyle 403.
3. **URL'li post oluşturma** — furi'nin raw URL'leriyle post oluştur, panelde
   görsellerin göründüğünü doğrula. Blob'a hiçbir şey yazılmamalı.
4. **Instagram bağlı değilken** — onayla, `publishStatus === "skipped"`, hiçbir şey
   yayınlanmamalı. *Bu adım mevcut kullanıcıların davranışının bozulmadığını kanıtlar.*
5. **Tek görsel yayını** — Instagram bağlı bir müşteride onayla, post gerçekten
   çıksın, `igPermalink` dolsun. Instagram'dan elle sil.
6. **Karusel** — 6 slaytlık bir postla tekrarla (`hikayeli/takside` uygun).
   Slayt sırasının doğru olduğunu gözle kontrol et.
7. **Çift onay yarışı** — aynı token'a iki eşzamanlı `POST`. Biri 409 almalı,
   Instagram'da **tek** post olmalı.
8. **Uçtan uca** — furi rutinini çalıştır → mail gelsin → telefondan onayla →
   süreyi ölç. **Hedef: 2 dakikanın altı.**

---

## Riskler

**Vercel fonksiyon süresi.** 8 slaytlık karusel `maxDuration`'ı zorlayabilir.
Adım 6'da gerçek süreyi ölç. Aşarsa yayını `after()` ile yanıt sonrasına al ve
onay sayfası `GET /api/approve/{token}` ile durumu yoklasın.

**Token ömrü.** 60 gün. `Client.instagramTokenExpiry` alanı bunun için var; son 10
günde ajansa uyarı gösterecek küçük bir kontrol eklenmeli, yoksa bir gün sessizce
durur. `furi/scripts/ig_token.py` yenileme çağrısının nasıl yapıldığını gösteriyor.

**Kapsam kayması.** Bu SaaS müşteri onayı için bir ürün; Instagram yayını onu bir
"yayınlama aracına" dönüştürüyor. Karar 1 (kimlik bilgisi `Client`'ta, boşsa
`skipped`) bunu bilinçli olarak **opt-in** tutuyor — mevcut kullanıcılar için hiçbir
şey değişmiyor. Bu ayrımı korumakta fayda var.

**Onay ≠ yayın ayrımı.** `status: approved` ile `publishStatus` ayrı alanlar. Bir
post onaylanmış ama yayınlanmamış olabilir (skipped/failed). Panelde bu ikisi ayrı
gösterilmeli, yoksa "onayladım ama çıkmamış" karışıklığı doğar.

---

## Sonuç olarak

- **SaaS'a eklenen:** 2 yeni dosya (`api-key.ts`, `instagram.ts`), 1 migration,
  `posts/route.ts` ve `approve/[token]/route.ts`'e dokunuş, onay sayfasında durum
  gösterimi, testler.
- **furi'den çıkan:** Apps Script zinciri, Gmail yanıt ayrıştırma, yayın tetikleme
  mantığı.
- **Kazanılan:** onaydan yayına ~2-10 saniye, tek tıkla mobil onay, audit kaydı,
  çift yayın koruması veritabanı seviyesinde.
