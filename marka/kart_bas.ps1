<#
.SYNOPSIS
  Marka kartini YERELDE basar. Metin bir goruntu modelinden gecmez.

.DESCRIPTION
  Yazim hatasi ve eksik Turkce karakter sorununu kokunden bitirir: harfleri
  difuzyon modeli "cizmez", gercek bir fontla biz basariz. Ciktinin metni
  girdinin metnidir; dogrulamaya gerek kalmaz.

  Zemin marka\zemin.jpg — arsivdeki kartlarin metinsiz bantlarindan cikarilmis
  gercek kagit dokusu, tum kartlarda ayni. Arsivdeki "zemin rengi kayiyor"
  sorunu (HATA-RAPORU §4) boylece kendiliginden kapaniyor.

  Iki kart bicimi var:
    - tekil kart   : etiket / baslik / anlam / ornek / cta
    - deste slayti : kapak, soru slayti (sayac + soru + sik), cevap anahtari
                     (madde + aciklama + ayrac)

.PARAMETER Spec
  Slayt tanimlarini iceren JSON dosyasi (UTF-8). Sema: marka\README.md

.EXAMPLE
  powershell -File marka\kart_bas.ps1 -Spec taslak.json -Hedef dizi\tell-me-about-it
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$Spec,
  [Parameter(Mandatory)][string]$Hedef,
  [string]$Zemin,
  [string]$BaslikFont = 'Impact',
  [string]$GovdeFont  = 'Segoe UI',
  [int]$Kalite = 94
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$kok = Split-Path -Parent $PSScriptRoot
if (-not $Zemin) { $Zemin = Join-Path $PSScriptRoot 'zemin.jpg' }

# --- Marka sabitleri (WORKFLOW.md Ek A) ---
$EN = 1920; $BOY = 2400; $KENAR = 150
$METIN_EN = $EN - 2 * $KENAR
$ISLEK_BOY = $BOY - 2 * $KENAR      # blogun tasmadan sigabilecegi en buyuk yukseklik
$LACIVERT = [System.Drawing.Color]::FromArgb(14, 32, 56)
$TURUNCU  = [System.Drawing.Color]::FromArgb(239, 74, 24)
$GRI      = [System.Drawing.Color]::FromArgb(107, 114, 128)
$SIK_EN   = 700                     # sik kutusunun genisligi
$SIK_PAY  = 46                      # sik kutusunda metnin ustunde/altinda kalan bosluk

# Oge tipi -> (font rolu, hedef punto, renk, harf araligi, alt bosluk)
#   Kalin : bold kesim
#   Sar   : sigmayan metin satira bolunur (punto sabit kalir)
#   Satir : en fazla kac satira bolunebilir; punto o sayiya sigana kadar kucultulur
#   Kutu  : metin cerceve icine alinir
$STIL = @{
  'etiket'   = @{ Font='baslik'; Punto=46;  Renk=$TURUNCU;  Aralik=10; Bosluk=120 }
  'sayac'    = @{ Font='govde';  Punto=54;  Renk=$GRI;      Aralik=0;  Bosluk=170 }
  'baslik'   = @{ Font='baslik'; Punto=250; Renk=$LACIVERT; Aralik=0;  Bosluk=175 }
  'kapak'    = @{ Font='baslik'; Punto=250; Renk=$LACIVERT; Aralik=0;  Bosluk=150; Satir=2 }
  'anlam'    = @{ Font='baslik'; Punto=108; Renk=$LACIVERT; Aralik=0;  Bosluk=90  }
  'soru'     = @{ Font='govde';  Punto=92;  Renk=$LACIVERT; Aralik=0;  Bosluk=170; Kalin=$true; Sar=$true }
  'sik'      = @{ Font='govde';  Punto=64;  Renk=$LACIVERT; Aralik=0;  Bosluk=44;  Kutu=$true }
  'madde'    = @{ Font='baslik'; Punto=92;  Renk=$LACIVERT; Aralik=0;  Bosluk=12  }
  'aciklama' = @{ Font='govde';  Punto=52;  Renk=$GRI;      Aralik=0;  Bosluk=46;  Sar=$true }
  'cumle'    = @{ Font='govde';  Punto=84;  Renk=$LACIVERT; Aralik=0;  Bosluk=100; Kalin=$true; Sar=$true }
  'araetiket'= @{ Font='baslik'; Punto=40;  Renk=$TURUNCU;  Aralik=10; Bosluk=70  }
  'ornek'    = @{ Font='govde';  Punto=58;  Renk=$GRI;      Aralik=0;  Bosluk=240 }
  'ayrac'    = @{ Font='baslik'; Punto=0;   Renk=$TURUNCU;  Aralik=0;  Bosluk=64  }
  'cta'      = @{ Font='baslik'; Punto=74;  Renk=$LACIVERT; Aralik=0;  Bosluk=0;   Sar=$true }
}

$biz = [System.Drawing.StringFormat]::GenericTypographic

function Olc($g, $metin, $font, $aralik) {
  $w = $g.MeasureString($metin, $font, [System.Drawing.PointF]::new(0,0), $biz).Width
  if ($aralik -gt 0 -and $metin.Length -gt 1) { $w += $aralik * ($metin.Length - 1) }
  return $w
}

function YeniFont($aile, $punto, $kalin) {
  $kesim = if ($kalin) { [System.Drawing.FontStyle]::Bold } else { [System.Drawing.FontStyle]::Regular }
  return New-Object System.Drawing.Font($aile, [float]$punto, $kesim, [System.Drawing.GraphicsUnit]::Pixel)
}

function Sigdir($g, $metin, $aile, $punto, $aralik, $kalin) {
  # Punto, metin KENAR bosluklarina sigana kadar kucultulur. Tekil kartta satir
  # kirilmasi yok: basligin iki satira dusmesi hiyerarsiyi bozuyordu.
  $p = $punto
  while ($p -gt 12) {
    $f = YeniFont $aile $p $kalin
    if ((Olc $g $metin $f $aralik) -le $METIN_EN) { return $f }
    $f.Dispose(); $p -= 2
  }
  return YeniFont $aile 12 $kalin
}

function Dengele($g, $kelimeler, $font, $satirSayisi) {
  # Ayni satir sayisinda, en genis satiri en dar tutan bolunmeyi arar. Acgozlu
  # doldurma son satirda tek kelime birakabiliyor ("piano.") ve o yetim satir
  # hiyerarsiyi bozuyor. Iki ve uc satir icin tum bolunme noktalari denenir —
  # kart metinleri kisa, maliyet yok.
  $adet = $kelimeler.Count
  if ($satirSayisi -lt 2 -or $satirSayisi -gt 3 -or $adet -le $satirSayisi) { return $null }
  $bolunmeler = New-Object System.Collections.ArrayList
  for ($i = 1; $i -lt $adet; $i++) {
    if ($satirSayisi -eq 2) {
      [void]$bolunmeler.Add(@($i))
    } else {
      for ($j = $i + 1; $j -lt $adet; $j++) { [void]$bolunmeler.Add(@($i, $j)) }
    }
  }

  $enIyi = $null
  $enIyiGenislik = [double]::MaxValue
  foreach ($sinirlar in $bolunmeler) {
    $parcalar = @()
    $bas = 0
    foreach ($sinir in (@($sinirlar) + @($adet))) {
      $parcalar += ($kelimeler[$bas..($sinir - 1)] -join ' ')
      $bas = $sinir
    }
    $genislik = ($parcalar | ForEach-Object { Olc $g $_ $font 0 } | Measure-Object -Maximum).Maximum
    if ($genislik -lt $enIyiGenislik) { $enIyiGenislik = $genislik; $enIyi = $parcalar }
  }
  if ($enIyi -and $enIyiGenislik -le $METIN_EN) { return ,$enIyi }
  return $null
}

function Sar($g, $metin, $font) {
  # Kelime kelime doldurur. Tek basina sigmayan kelime kendi satirinda kalir —
  # o durumda punto zaten cagiran tarafta kucultulmus oluyor.
  $kelimeler = @($metin -split '\s+' | Where-Object { $_ })
  $satirlar = New-Object System.Collections.ArrayList
  $suan = ''
  foreach ($kelime in $kelimeler) {
    $deneme = if ($suan) { "$suan $kelime" } else { $kelime }
    if (-not $suan -or (Olc $g $deneme $font 0) -le $METIN_EN) {
      $suan = $deneme
    } else {
      [void]$satirlar.Add($suan); $suan = $kelime
    }
  }
  if ($suan) { [void]$satirlar.Add($suan) }
  $dengeli = Dengele $g $kelimeler $font $satirlar.Count
  if ($dengeli) { return ,$dengeli }
  return ,$satirlar.ToArray()
}

function SigdirCok($g, $metin, $aile, $punto, $satirSiniri, $kalin) {
  # Kapak basligi bir cumle, terim degil: satira bolunebilir ama siniri asamaz.
  # En buyuk punto, metin o sinira sigana kadar kucultulerek bulunur.
  $p = $punto
  while ($p -gt 12) {
    $f = YeniFont $aile $p $kalin
    $satirlar = Sar $g $metin $f
    if ($satirlar.Count -le $satirSiniri) { return @{ Font=$f; Satirlar=$satirlar } }
    $f.Dispose(); $p -= 4
  }
  $f = YeniFont $aile 12 $kalin
  return @{ Font=$f; Satirlar=(Sar $g $metin $f) }
}

function EnUzunKelime($metin) {
  return ($metin -split '\s+' | Where-Object { $_ } | Sort-Object { $_.Length } | Select-Object -Last 1)
}

function BlokKur($g, $slayt, $olcek) {
  # Slaytin butun ogelerini olcer, blogun toplam yuksekligini dondurur.
  # $olcek < 1 ise punto ve bosluklar birlikte kuculur (bkz. tasma dongusu).
  $ogeler = New-Object System.Collections.ArrayList
  $toplam = 0
  foreach ($o in $slayt.ogeler) {
    $s = $STIL[$o.tur]
    if (-not $s) { throw "bilinmeyen oge turu: $($o.tur)" }
    $aile = if ($s.Font -eq 'baslik') { $BaslikFont } else { $GovdeFont }
    # `alt`: bu ogenin altindaki bosluk. Ritmi slayt icinde bir kez bozmak
    # gerektiginde (son sikkin altindaki nefes gibi) tur stilini ezer.
    $tabanBosluk = if ($null -ne $o.alt) { [int]$o.alt } else { $s.Bosluk }
    $bosluk = [math]::Round($tabanBosluk * $olcek)

    if ($o.tur -eq 'ayrac') {
      $genislik = if ($o.en) { [int]$o.en } else { 220 }
      [void]$ogeler.Add(@{ Tur='ayrac'; Yuk=4; Bosluk=$bosluk; Stil=$s; En=$genislik; Olcek=$olcek })
      $toplam += 4 + $bosluk
      continue
    }

    $punto = [math]::Max(12, [math]::Round($s.Punto * $olcek))
    if ($s.Satir) {
      $sonuc = SigdirCok $g $o.metin $aile $punto $s.Satir $s.Kalin
      $f = $sonuc.Font; $satirlar = $sonuc.Satirlar
    } elseif ($s.Sar) {
      # Punto sabit; yalnizca en uzun kelime tek basina sigmiyorsa kuculur.
      $f = Sigdir $g (EnUzunKelime $o.metin) $aile $punto 0 $s.Kalin
      $satirlar = Sar $g $o.metin $f
    } else {
      $f = Sigdir $g $o.metin $aile $punto $s.Aralik $s.Kalin
      $satirlar = @($o.metin)
    }

    $satirYuk = $g.MeasureString('Ag', $f, [System.Drawing.PointF]::new(0,0), $biz).Height
    $yuk = $satirYuk * $satirlar.Count
    if ($s.Kutu) { $yuk = $satirYuk + 2 * [math]::Round($SIK_PAY * $olcek) }

    [void]$ogeler.Add(@{
      Tur=$o.tur; Satirlar=$satirlar; Font=$f; Yuk=$yuk; SatirYuk=$satirYuk
      Bosluk=$bosluk; Stil=$s; Olcek=$olcek
    })
    $toplam += $yuk + $bosluk
  }
  if ($ogeler.Count) { $toplam -= $ogeler[$ogeler.Count - 1].Bosluk }
  return @{ Ogeler=$ogeler; Toplam=$toplam }
}

function BlokBirak($blok) {
  foreach ($o in $blok.Ogeler) { if ($o.Font) { $o.Font.Dispose() } }
}

function Bas($g, $metin, $font, $firca, $y, $aralik) {
  $w = Olc $g $metin $font $aralik
  $x = ($EN - $w) / 2
  if ($aralik -le 0) {
    $g.DrawString($metin, $font, $firca, $x, $y, $biz)
  } else {
    foreach ($h in $metin.ToCharArray()) {
      $g.DrawString($h, $font, $firca, $x, $y, $biz)
      $x += $g.MeasureString($h, $font, [System.Drawing.PointF]::new(0,0), $biz).Width + $aralik
    }
  }
}

# Denetim kapisi: metin once okunur, sonra basilir. Gorsel metni bozamadigi
# icin geriye tek risk metnin kendisi kaliyor; o da buradan geciyor.
$denetci = Join-Path $PSScriptRoot 'metin_denetle.py'
if (Test-Path $denetci) {
  $env:PYTHONIOENCODING = 'utf-8'
  $rapor = & python $denetci $Spec 2>&1
  $rapor | ForEach-Object { "  $_" }
  if ($LASTEXITCODE -ne 0) {
    throw "metin denetimi gecilemedi, duzeltmeden basilmaz: $Spec"
  }
} else {
  Write-Warning "metin_denetle.py bulunamadi, denetim atlandi"
}

$veri = Get-Content -Raw -Encoding UTF8 $Spec | ConvertFrom-Json
$hedefYol = if ([System.IO.Path]::IsPathRooted($Hedef)) { $Hedef } else { Join-Path $kok $Hedef }
if (-not (Test-Path $hedefYol)) { New-Item -ItemType Directory -Force $hedefYol | Out-Null }

$enc = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
$prm = New-Object System.Drawing.Imaging.EncoderParameters 1
$prm.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter ([System.Drawing.Imaging.Encoder]::Quality), ([long]$Kalite)

$no = 0
foreach ($slayt in $veri.slaytlar) {
  $no++
  $zem = [System.Drawing.Image]::FromFile($Zemin)
  $bmp = New-Object System.Drawing.Bitmap $EN, $BOY, ([System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.DrawImage($zem, 0, 0, $EN, $BOY)
  $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias
  $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias

  # 1. gecis: olc. Blok kenar bosluklarina sigmiyorsa punto ve bosluklar birlikte
  # kucultulup yeniden olculur — deste slaytlari (bes maddelik cevap anahtari
  # gibi) tekil karttan cok daha uzun, tasma da sessizce kirpilmis metin demek.
  $olcek = 1.0
  $blok = BlokKur $g $slayt $olcek
  $tur = 0
  while ($blok.Toplam -gt $ISLEK_BOY -and $tur -lt 4) {
    $olcek = $olcek * ($ISLEK_BOY / $blok.Toplam) * 0.99
    BlokBirak $blok
    $blok = BlokKur $g $slayt $olcek
    $tur++
  }

  # Blok dikeyde ortalanir. Bosluk degerleri arsivdeki kartlarin dikey ritmine
  # gore ayarli: tekil kartta blok ~1280 px, ustte ve altta ~560 px nefes.
  $y = ($BOY * 0.50) - ($blok.Toplam / 2)

  foreach ($o in $blok.Ogeler) {
    $firca = New-Object System.Drawing.SolidBrush $o.Stil.Renk
    if ($o.Tur -eq 'ayrac') {
      $g.FillRectangle($firca, ($EN - $o.En) / 2, $y, $o.En, 4)
    } elseif ($o.Stil.Kutu) {
      $kutuEn = [math]::Round($SIK_EN * $o.Olcek)
      $kalem = New-Object System.Drawing.Pen($o.Stil.Renk, [float]3)
      $g.DrawRectangle($kalem, [float](($EN - $kutuEn) / 2), [float]$y, [float]$kutuEn, [float]$o.Yuk)
      $kalem.Dispose()
      Bas $g $o.Satirlar[0] $o.Font $firca ($y + ($o.Yuk - $o.SatirYuk) / 2) 0
    } else {
      $satirY = $y
      foreach ($satir in $o.Satirlar) {
        Bas $g $satir $o.Font $firca $satirY $o.Stil.Aralik
        $satirY += $o.SatirYuk
      }
    }
    $y += $o.Yuk + $o.Bosluk
    $firca.Dispose()
  }
  BlokBirak $blok

  $cikti = Join-Path $hedefYol "$no.jpg"
  $bmp.Save($cikti, $enc, $prm)
  $olcekNot = if ($olcek -lt 1) { ", olcek $([math]::Round($olcek,2))" } else { "" }
  "  $no.jpg  ($([math]::Round($blok.Toplam)) px blok, $BaslikFont$olcekNot)"
  $g.Dispose(); $bmp.Dispose(); $zem.Dispose()
}
"$no slayt basildi -> $hedefYol"
