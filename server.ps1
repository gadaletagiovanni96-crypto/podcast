# Server locale per il telecomando della TV (Windows, nessuna installazione necessaria).
# Avvialo con "avvia-telecomando-windows.bat".
param([int]$Porta = 8080)

$root = [IO.Path]::GetFullPath((Split-Path -Parent $MyInvocation.MyCommand.Path))
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://+:$Porta/")
try { $listener.Start() }
catch {
  Write-Host ""
  Write-Host "ERRORE: impossibile avviare il server sulla porta $Porta." -ForegroundColor Red
  Write-Host "Avvialo con 'avvia-telecomando-windows.bat' e rispondi SI alla richiesta di Windows."
  Write-Host $_.Exception.Message
  Read-Host "Premi Invio per chiudere"
  exit 1
}

$ip = ([System.Net.Dns]::GetHostAddresses([System.Net.Dns]::GetHostName()) |
  Where-Object { $_.AddressFamily -eq 'InterNetwork' -and $_.ToString() -notlike '127.*' -and $_.ToString() -notlike '169.254.*' } |
  Select-Object -First 1)
if ($ip) { $ip = $ip.ToString() } else { $ip = "localhost" }

Write-Host ""
Write-Host "  ==============================================" -ForegroundColor Yellow
Write-Host "   TELECOMANDO TV ATTIVO" -ForegroundColor Yellow
Write-Host "  ==============================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "   Sul PC della TV apri:   http://localhost:$Porta/tv.html"
Write-Host "   Sul telefono apri:      http://${ip}:$Porta/telecomando.html" -ForegroundColor Green
Write-Host ""
Write-Host "   Il telefono deve essere connesso alla STESSA rete Wi-Fi del PC."
Write-Host "   NON chiudere questa finestra finche' la mostra e' aperta."
Write-Host ""
Start-Process "http://localhost:$Porta/tv.html"

$mime = @{ ".html" = "text/html; charset=utf-8"; ".js" = "application/javascript"; ".css" = "text/css";
           ".png" = "image/png"; ".jpg" = "image/jpeg"; ".svg" = "image/svg+xml"; ".json" = "application/json";
           ".md" = "text/plain; charset=utf-8"; ".ico" = "image/x-icon" }
$cmdId = 0; $cmdAz = ""; $stato = "null"; $statoT = [DateTime]::MinValue
$utf8 = New-Object System.Text.UTF8Encoding($false)

while ($listener.IsListening) {
  $ctx = $listener.GetContext()
  $req = $ctx.Request; $res = $ctx.Response
  try {
    $res.Headers.Add("Cache-Control", "no-store")
    $path = $req.Url.LocalPath
    $json = $null
    if ($path -eq "/api/cmd") {
      $a = $req.QueryString["azione"]
      if (@("play", "pausa", "toggle", "inizio") -contains $a) { $cmdId++; $cmdAz = $a }
      $json = '{"ok":true,"id":' + $cmdId + '}'
    } elseif ($path -eq "/api/poll") {
      $json = '{"id":' + $cmdId + ',"azione":"' + $cmdAz + '"}'
    } elseif ($path -eq "/api/stato") {
      if ($req.HttpMethod -eq "POST") {
        $sr = New-Object System.IO.StreamReader($req.InputStream, [System.Text.Encoding]::UTF8)
        $t = $sr.ReadToEnd(); $sr.Close()
        if ($t.Length -lt 4000 -and $t.StartsWith("{")) { $stato = $t; $statoT = Get-Date }
        $json = '{"ok":true}'
      } else {
        $eta = [int][Math]::Min(99999, ((Get-Date) - $statoT).TotalSeconds)
        $json = '{"eta":' + $eta + ',"tv":' + $stato + '}'
      }
    } elseif ($path -eq "/api/info") {
      $json = '{"ip":"' + $ip + '","porta":' + $Porta + '}'
    }

    if ($json -ne $null) {
      $bytes = $utf8.GetBytes($json)
      $res.ContentType = "application/json; charset=utf-8"
    } else {
      if ($path -eq "/") { $path = "/index.html" }
      $file = [IO.Path]::GetFullPath((Join-Path $root ($path.TrimStart('/') -replace '/', '\')))
      if (-not $file.StartsWith($root + '\') -or -not (Test-Path $file -PathType Leaf)) {
        $res.StatusCode = 404; $bytes = $utf8.GetBytes("Non trovato"); $res.ContentType = "text/plain"
      } else {
        $bytes = [IO.File]::ReadAllBytes($file)
        $ext = [IO.Path]::GetExtension($file).ToLower()
        if ($mime.ContainsKey($ext)) { $res.ContentType = $mime[$ext] } else { $res.ContentType = "application/octet-stream" }
      }
    }
    $res.ContentLength64 = $bytes.Length
    $res.OutputStream.Write($bytes, 0, $bytes.Length)
  } catch {
    # una richiesta andata male non deve fermare il server
  } finally {
    try { $res.OutputStream.Close() } catch {}
  }
}
