# mqtt_listen.ps1
# EcoFlow MQTT listener — toont alleen gewijzigde telemetriewaarden.
# Stuurt bij opstarten een get-all request zodat de volledige device state binnenkomt.
# Nieuwe keys worden gemarkeerd met [NIEUW].
#
# Gebruik:
#   cd C:\Users\arieb\Downloads
#   PowerShell -ExecutionPolicy Bypass -File .\mqtt_listen.ps1
#
# Werkwijze:
#   1. Script opstarten
#   2. Wachten tot "Luisteren..." verschijnt en get-all is verstuurd
#   3. Schakelaar omzetten in EcoFlow app
#   4. Gewijzigde key verschijnt direct in console met oude en nieuwe waarde

$EMAIL    = "windsurf@live.nl"
$PASSWORD = "vul_hier_je_wachtwoord_in"
$SN       = "D361ZEH49GAR0848"

# ---- DLL laden -------------------------------------------------------
$dllPath = "$PSScriptRoot\M2Mqtt.Net.dll"
if (-not (Test-Path $dllPath)) {
    Write-Host "M2Mqtt.Net.dll downloaden..." -ForegroundColor Yellow
    $nupkg = "$PSScriptRoot\m2mqtt.nupkg"
    Invoke-WebRequest -Uri "https://www.nuget.org/api/v2/package/M2Mqtt/4.3.0.0" -OutFile $nupkg -UseBasicParsing
    $extract = "$PSScriptRoot\m2mqtt_tmp"
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($nupkg, $extract)
    $found = Get-ChildItem -Path $extract -Recurse -Filter "M2Mqtt.Net.dll" | Select-Object -First 1
    Copy-Item $found.FullName $dllPath
    Remove-Item $nupkg -Force
    Remove-Item $extract -Recurse -Force
}
Add-Type -Path $dllPath -ErrorAction Stop

# ---- Login -----------------------------------------------------------
Write-Host "Login..." -ForegroundColor Yellow
$b64pw = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($PASSWORD))
$h = @{ "Content-Type" = "application/json"; "User-Agent" = "okhttp/3.14.9" }
$loginBody = @{ email=$EMAIL; password=$b64pw; scene="IOT_APP"; userType="ECOFLOW"; appVersion="4.1.2.02"; os="android"; osVersion="30" } | ConvertTo-Json -Compress
$loginResp = Invoke-RestMethod -Uri "https://api.ecoflow.com/auth/login" -Method Post -Headers $h -Body $loginBody
if ([string]$loginResp.code -ne "0") { Write-Host "Login mislukt" -ForegroundColor Red; exit 1 }
$token  = $loginResp.data.token
$userId = [string]$loginResp.data.user.userId
$h2 = @{ "Content-Type" = "application/json"; "Authorization" = "Bearer $token"; "User-Agent" = "okhttp/3.14.9" }
$certResp = Invoke-RestMethod -Uri "https://api.ecoflow.com/iot-auth/app/certification?userId=$userId" -Method Get -Headers $h2
$cert = $certResp.data
$clientId = "ANDROID_$(Get-Random -Minimum 10000000 -Maximum 99999999)_$userId"
Write-Host "Login OK  (userId: $userId)" -ForegroundColor Green

# ---- MQTT verbinden --------------------------------------------------
$mqtt = New-Object uPLibrary.Networking.M2Mqtt.MqttClient($cert.url, [int]$cert.port, $true, $null, $null, [uPLibrary.Networking.M2Mqtt.MqttSslProtocols]::TLSv1_2)

$global:state    = @{}   # huidige bekende waarden
$global:seenKeys = @{}   # keys die al eerder gezien zijn
$global:seq      = 1000

Register-ObjectEvent -InputObject $mqtt -EventName MqttMsgPublishReceived -Action {
    $topic = $args[1].Topic
    $ts    = Get-Date -Format "HH:mm:ss"
    try {
        $msg = [System.Text.Encoding]::UTF8.GetString($args[1].Message)
        $obj = $msg | ConvertFrom-Json

        # Telemetrie push
        if ($topic -like "*/device/property/*" -and $obj.params) {
            $obj.params.PSObject.Properties | ForEach-Object {
                $key = $_.Name
                $val = $_.Value

                $isNew     = -not $global:seenKeys.ContainsKey($key)
                $isChanged = $global:state.ContainsKey($key) -and ($global:state[$key] -ne $val)

                $global:seenKeys[$key] = 1

                if ($isNew) {
                    # Nieuwe key: altijd tonen met huidige waarde
                    Write-Host ("[{0}] [NIEUW]  {1,-40} = {2}" -f $ts, $key, $val) -ForegroundColor Magenta
                    $global:state[$key] = $val
                } elseif ($isChanged) {
                    # Gewijzigde key: toon oude en nieuwe waarde
                    $old = $global:state[$key]
                    Write-Host ("[{0}] [WIJZIG] {1,-40} = {2}  (was: {3})" -f $ts, $key, $val, $old) -ForegroundColor Cyan
                    $global:state[$key] = $val
                }
                # Ongewijzigde keys: niet tonen
            }
        }

        # Get-all reply (latestQuotas)
        elseif ($topic -like "*/get_reply" -and $obj.data) {
            Write-Host ""
            Write-Host ("[$ts] [GET-ALL] volledige state ontvangen:") -ForegroundColor Green
            try {
                $obj.data.PSObject.Properties | ForEach-Object {
                    $key = $_.Name
                    $val = $_.Value
                    $global:state[$key]    = $val
                    $global:seenKeys[$key] = 1
                    Write-Host ("  {0,-40} = {1}" -f $key, $val) -ForegroundColor DarkGray
                }
            } catch {}
            Write-Host ""
        }

        # Set reply
        elseif ($topic -like "*/set_reply") {
            $code = $obj.code
            $ack  = if ($obj.data) { $obj.data.ack } else { "?" }
            Write-Host ("[{0}] [SET_REPLY] code={1} ack={2}" -f $ts, $code, $ack) -ForegroundColor Yellow
        }

    } catch {}
} | Out-Null

$rc = $mqtt.Connect($clientId, $cert.certificateAccount, $cert.certificatePassword, $true, 60)
if (-not $mqtt.IsConnected) { Write-Host "Verbinding mislukt" -ForegroundColor Red; exit 1 }

$topicTelemetry = "/app/device/property/$SN"
$topicGetReply  = "/app/$userId/$SN/thing/property/get_reply"
$topicSetReply  = "/app/$userId/$SN/thing/property/set_reply"
$topicGet       = "/app/$userId/$SN/thing/property/get"

$mqtt.Subscribe([string[]]@($topicTelemetry, $topicGetReply, $topicSetReply), [byte[]]@(0, 1, 1)) | Out-Null

# ---- Get-all sturen --------------------------------------------------
Start-Sleep -Milliseconds 500
$global:seq++
$getAll = @{ id=$global:seq; version="1.0"; sn=$SN; moduleType=0; operateType="latestQuotas"; params=@{} } | ConvertTo-Json -Compress
$mqtt.Publish($topicGet, [System.Text.Encoding]::UTF8.GetBytes($getAll), 1, $false) | Out-Null

Write-Host ""
Write-Host "Luisteren... get-all verstuurd. Schakel nu dingen in de EcoFlow app." -ForegroundColor Green
Write-Host "Legenda:" -ForegroundColor DarkGray
Write-Host "  [MAGENTA]  [NIEUW]  = key nog niet eerder gezien in deze sessie" -ForegroundColor Magenta
Write-Host "  [CYAN]     [WIJZIG] = bestaande key met nieuwe waarde (oud -> nieuw)" -ForegroundColor Cyan
Write-Host "  [GEEL]     [SET_REPLY] = reactie op een SET commando" -ForegroundColor Yellow
Write-Host "  [GROEN]    [GET-ALL] = volledige state dump bij opstarten" -ForegroundColor Green
Write-Host ""
Write-Host "Stop met Ctrl+C" -ForegroundColor DarkGray
Write-Host ""

try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    $mqtt.Disconnect()
    Write-Host "Verbinding verbroken."
}
