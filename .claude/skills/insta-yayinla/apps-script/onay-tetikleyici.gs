/**
 * FURI — Instagram yayin onayi tetikleyicisi
 *
 * Gmail'de [FURI-ONAY] konulu maillere gelen "EVET" / "HAYIR" yanitlarini yakalar
 * ve Claude rutinini tetikler. Google'in sunucusunda dakikada bir calisir; Claude
 * tarafinda hicbir bosa calisma olmaz.
 *
 * Kurulum: bu klasordeki KURULUM-APPS-SCRIPT.md
 */

// ---------------------------------------------------------------- ayarlar

/**
 * Tetikleme GitHub uzerinden gider: bu script issue #1'e yorum birakir, GitHub'in
 * `issue_comment` webhook'u Claude rutinini calistirir.
 *
 * GitHub token'i Script Properties'te durur, koda gomulmez.
 */
var GH_REPO  = 'enesmemduhoglu/furi';
var GH_ISSUE = 1;

function githubToken_() {
  var t = PropertiesService.getScriptProperties().getProperty('FURI_GITHUB_TOKEN');
  if (!t) {
    throw new Error(
      'FURI_GITHUB_TOKEN tanimli degil. Project Settings > Script Properties ' +
      'altina GitHub token\'ini ekle. (KURULUM-APPS-SCRIPT.md adim 2)'
    );
  }
  return t;
}

var KONU_ETIKETI  = '[FURI-ONAY]';
var ISLENDI_LABEL = 'furi-islendi';   // ayni yaniti iki kez tetiklememek icin
var ARAMA_PENCERE = '2d';             // bu kadar eskiye kadar bakilir

var ONAY_SOZLERI  = ['EVET', 'OK', 'TAMAM', 'YAYINLA', 'ONAY'];
var RET_SOZLERI   = ['HAYIR', 'YOK', 'ATLA', 'IPTAL', 'GECE'];

// ------------------------------------------------------------ ana dongu

/**
 * Zamanlayicinin cagirdigi fonksiyon. Dakikada bir calisir.
 */
function onayKontrol() {
  var label = etiketiAl_(ISLENDI_LABEL);
  var sorgu = 'subject:"' + KONU_ETIKETI + '" newer_than:' + ARAMA_PENCERE +
              ' -label:' + ISLENDI_LABEL;

  var threadler = GmailApp.search(sorgu, 0, 20);
  if (!threadler.length) return;

  threadler.forEach(function (thread) {
    var karar = kararOku_(thread);
    if (!karar) return;   // henuz yanit yok ya da belirsiz yanit — dokunma

    var konu = thread.getFirstMessageSubject();
    Logger.log('Karar: ' + karar + '  |  ' + konu);

    if (tetikle_(karar, konu, thread.getId())) {
      thread.addLabel(label);   // sadece tetikleme BASARILIYSA isaretle
    }
  });
}

/**
 * Thread'deki yaniti okur. 'onay' | 'ret' | null doner.
 *
 * Onay maili kullanicinin kendi hesabindan kendine gidiyor, yani gonderen
 * bilgisi ayirt edici degil. Bu yuzden ilk mesaj (bizim gonderdigimiz) atlanir,
 * sonrakilere bakilir.
 */
function kararOku_(thread) {
  var mesajlar = thread.getMessages();
  if (mesajlar.length < 2) return null;   // henuz yanit gelmemis

  // En son yaniti dikkate al
  for (var i = mesajlar.length - 1; i >= 1; i--) {
    var satir = ilkAnlamliSatir_(mesajlar[i].getPlainBody());
    if (!satir) continue;

    var sozcuk = satir.toLocaleUpperCase('tr-TR').replace(/[^A-ZÇĞİÖŞÜ]/g, '');
    if (ONAY_SOZLERI.indexOf(sozcuk) !== -1) return 'onay';
    if (RET_SOZLERI.indexOf(sozcuk)  !== -1) return 'ret';

    // Belirsiz yanit: onay sayilmaz. Isaretlemeden birakiyoruz ki
    // kullanici net bir "EVET" yazdiginda yakalansin.
    return null;
  }
  return null;
}

/**
 * Alintilanmis bolumu atarak ilk anlamli satiri dondurur.
 */
function ilkAnlamliSatir_(govde) {
  var satirlar = (govde || '').split(/\r?\n/);
  for (var i = 0; i < satirlar.length; i++) {
    var s = satirlar[i].trim();
    if (!s) continue;
    if (s.charAt(0) === '>') break;                      // alinti basladi
    if (/^On .* wrote:$/.test(s)) break;                 // Gmail (EN)
    if (/tarihinde .* şunları yazdı:$/.test(s)) break;   // Gmail (TR)
    if (/^-{2,}\s*(Forwarded|Original)/i.test(s)) break;
    return s;
  }
  return null;
}

/**
 * GitHub issue'suna yorum birakarak Claude rutinini tetikler. Basarili mi doner.
 *
 * Yoruma "@claude" YAZILMAZ — o ifade GitHub App'in ayri bir davranisini
 * tetikler; bize sadece issue_comment olayinin dogmasi yeterli.
 */
function tetikle_(karar, konu, threadId) {
  var govde =
    'Onay yaniti yakalandi.\n\n' +
    '| alan | deger |\n|---|---|\n' +
    '| karar | **' + karar + '** |\n' +
    '| mail konusu | `' + konu + '` |\n' +
    '| thread | `' + threadId + '` |\n' +
    '| zaman | ' + new Date().toISOString() + ' |\n\n' +
    '_Gmail Apps Script tarafindan otomatik birakildi. Rutin onayi Gmail\'den ' +
    'bagimsiz olarak yeniden dogrular._';

  var yanit = UrlFetchApp.fetch(
    'https://api.github.com/repos/' + GH_REPO + '/issues/' + GH_ISSUE + '/comments', {
      method: 'post',
      contentType: 'application/json',
      headers: {
        Authorization: 'Bearer ' + githubToken_(),
        Accept: 'application/vnd.github+json'
      },
      payload: JSON.stringify({ body: govde }),
      muteHttpExceptions: true
    });

  var kod = yanit.getResponseCode();
  if (kod >= 200 && kod < 300) {
    Logger.log('Rutin tetiklendi (GitHub yorumu eklendi, HTTP ' + kod + ')');
    return true;
  }

  // Basarisizsa etiketlemiyoruz — bir sonraki calisma tekrar dener.
  Logger.log('TETIKLEME BASARISIZ HTTP ' + kod + ': ' + yanit.getContentText().slice(0, 300));
  return false;
}

function etiketiAl_(ad) {
  return GmailApp.getUserLabelByName(ad) || GmailApp.createLabel(ad);
}

// ------------------------------------------------------------ kurulum / test

/**
 * BIR KEZ calistir: dakikalik zamanlayiciyi kurar.
 * Tekrar calistirirsan eskisini silip yenisini kurar, cift tetikleme olmaz.
 */
function zamanlayiciKur() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'onayKontrol') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('onayKontrol').timeBased().everyMinutes(1).create();
  etiketiAl_(ISLENDI_LABEL);
  Logger.log('Zamanlayici kuruldu: onayKontrol her dakika calisacak.');
}

/**
 * Baglantiyi dogrular — Gmail'e dokunmadan sadece GitHub'a yorum atar.
 * Rutini gercekten tetikler; bekleyen bir post yoksa rutin hicbir sey yapmaz.
 */
function baglantiTesti() {
  var t = githubToken_();
  Logger.log('Token okundu (' + t.length + ' karakter), hedef: ' + GH_REPO + ' issue #' + GH_ISSUE);
  Logger.log('Sonuc: ' + (tetikle_('test', 'baglanti testi', 'yok') ? 'OK' : 'BASARISIZ'));
}

/**
 * Gmail tarafini dogrular — webhook cagirmadan sadece ne okudugunu gosterir.
 */
function kuruTest() {
  var threadler = GmailApp.search(
    'subject:"' + KONU_ETIKETI + '" newer_than:' + ARAMA_PENCERE, 0, 20);
  Logger.log(threadler.length + ' thread bulundu.');
  threadler.forEach(function (t) {
    Logger.log('  [' + (kararOku_(t) || 'yanit yok') + ']  ' + t.getFirstMessageSubject());
  });
}
