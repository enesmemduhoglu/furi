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
$LACIVERT = [System.Drawing.Color]::FromArgb(14, 32, 56)
$TURUNCU  = [System.Drawing.Color]::FromArgb(239, 74, 24)
$GRI      = [System.Drawing.Color]::FromArgb(107, 114, 128)

# Oge tipi -> (font rolu, hedef punto, en buyuk punto, renk, harf araligi, alt bosluk)
$STIL = @{
  'etiket' = @{ Font='baslik'; Punto=46;  Renk=$TURUNCU;  Aralik=10; Bosluk=120 }
  'baslik' = @{ Font='baslik'; Punto=250; Renk=$LACIVERT; Aralik=0;  Bosluk=175 }
  'anlam'  = @{ Font='baslik'; Punto=108; Renk=$LACIVERT; Aralik=0;  Bosluk=90  }
  'ornek'  = @{ Font='govde';  Punto=58;  Renk=$GRI;      Aralik=0;  Bosluk=240 }
  'ayrac'  = @{ Font='baslik'; Punto=0;   Renk=$TURUNCU;  Aralik=0;  Bosluk=64  }
  'cta'    = @{ Font='baslik'; Punto=74;  Renk=$LACIVERT; Aralik=0;  Bosluk=0   }
}

$biz = [System.Drawing.StringFormat]::GenericTypographic

function Olc($g, $metin, $font, $aralik) {
  $w = $g.MeasureString($metin, $font, [System.Drawing.PointF]::new(0,0), $biz).Width
  if ($aralik -gt 0 -and $metin.Length -gt 1) { $w += $aralik * ($metin.Length - 1) }
  return $w
}

function Sigdir($g, $metin, $aile, $punto, $aralik) {
  # Punto, metin KENAR bosluklarina sigana kadar kucultulur. Satir kirilmasi yok:
  # basligin iki satira dusmesi hiyerarsiyi bozuyordu, bu yuzden genislige oturtuluyor.
  $p = $punto
  while ($p -gt 12) {
    $f = New-Object System.Drawing.Font($aile, $p, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
    if ((Olc $g $metin $f $aralik) -le $METIN_EN) { return $f }
    $f.Dispose(); $p -= 2
  }
  return New-Object System.Drawing.Font($aile, 12, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
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

  # 1. gecis: her ogenin fontunu ve yuksekligini cikar, blok boyunu hesapla
  $ogeler = @()
  $toplam = 0
  foreach ($o in $slayt.ogeler) {
    $s = $STIL[$o.tur]
    if (-not $s) { throw "bilinmeyen oge turu: $($o.tur)" }
    $aile = if ($s.Font -eq 'baslik') { $BaslikFont } else { $GovdeFont }
    if ($o.tur -eq 'ayrac') {
      $ogeler += @{ Tur='ayrac'; Yuk=4; Stil=$s }
      $toplam += 4 + $s.Bosluk
      continue
    }
    $f = Sigdir $g $o.metin $aile $s.Punto $s.Aralik
    $h = $g.MeasureString($o.metin, $f, [System.Drawing.PointF]::new(0,0), $biz).Height
    $ogeler += @{ Tur=$o.tur; Metin=$o.metin; Font=$f; Yuk=$h; Stil=$s }
    $toplam += $h + $s.Bosluk
  }
  $toplam -= $ogeler[-1].Stil.Bosluk

  # Blok dikeyde ortalanir. Bosluk degerleri arsivdeki kartlarin dikey ritmine
  # gore ayarli: blok ~1280 px, ustte ve altta ~560 px nefes.
  $y = ($BOY * 0.50) - ($toplam / 2)

  foreach ($o in $ogeler) {
    $firca = New-Object System.Drawing.SolidBrush $o.Stil.Renk
    if ($o.Tur -eq 'ayrac') {
      $g.FillRectangle($firca, ($EN - 220) / 2, $y, 220, 4)
    } else {
      Bas $g $o.Metin $o.Font $firca $y $o.Stil.Aralik
      $o.Font.Dispose()
    }
    $y += $o.Yuk + $o.Stil.Bosluk
    $firca.Dispose()
  }

  $cikti = Join-Path $hedefYol "$no.jpg"
  $bmp.Save($cikti, $enc, $prm)
  "  $no.jpg  ($([math]::Round($toplam)) px blok, $BaslikFont)"
  $g.Dispose(); $bmp.Dispose(); $zem.Dispose()
}
"$no slayt basildi -> $hedefYol"
