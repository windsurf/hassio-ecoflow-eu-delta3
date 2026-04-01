# test_all_switches.ps1
# EcoFlow Delta 3 1500 — volledige entiteitstest v0.2.23
#
# Test verificatie per groep:
#   [TELEMETRIE] state key verandert aantoonbaar via MQTT
#   [SELECT]     discrete opties — telemetrie verificatie
#   [ACK ONLY]   geen telemetrie feedback — alleen ack=1 telt
#   [ONBEKEND]   niet in app, geen telemetrie — ack als indicator
#
# Entiteiten in sync met v0.2.23:
#   Switches (11): AC Output, X-Boost, USB Output, DC Output, AC Charging,
#                  Backup Reserve, Beep, Solar Priority, AC Auto-On,
#                  AC Always-On, Bypass, Output Memory
#   Numbers  (10): AC Charging Speed, Max Charge Level, Min Discharge Level,
#                  Generator Start/Stop SOC, Backup Reserve SOC,
#                  Min SOC AC Auto-On, LCD Brightness,
#                  Screen Standby, Overall Standby (read-only)
#   Selects   (5): Screen Timeout, Unit Standby, AC Standby,
#                  DC 12V Standby, DC Charge Current
#
# Gebruik:
#   cd C:\Users\arieb\Downloads
#   PowerShell -ExecutionPolicy Bypass -File .\test_all_switches.ps1

$EMAIL    = "windsurf@live.nl"
$PASSWORD = "vul_hier_je_wachtwoord_in"
$SN       = "D361ZEH49GAR0848"

$WAIT_TELEMETRY_S = 15   # seconden wachten op telemetrie feedback
$WAIT_RESTORE_S   = 5    # seconden wachten na terugzetten

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
Write-Host "Login OK" -ForegroundColor Green

# ---- MQTT verbinden --------------------------------------------------
$mqtt = New-Object uPLibrary.Networking.M2Mqtt.MqttClient($cert.url, [int]$cert.port, $true, $null, $null, [uPLibrary.Networking.M2Mqtt.MqttSslProtocols]::TLSv1_2)

$global:telemetry = @{}
$global:lastAck   = $null
$global:ackEvent  = New-Object System.Threading.ManualResetEventSlim($false)
$global:seq       = 3000

Register-ObjectEvent -InputObject $mqtt -EventName MqttMsgPublishReceived -Action {
    $topic = $args[1].Topic
    try {
        $msg = [System.Text.Encoding]::UTF8.GetString($args[1].Message)
        $obj = $msg | ConvertFrom-Json
        if ($topic -like "*/device/property/*" -and $obj.params) {
            $obj.params.PSObject.Properties | ForEach-Object { $global:telemetry[$_.Name] = $_.Value }
        }
        if ($topic -like "*/get_reply" -and $obj.data -and $obj.data.quotaMap) {
            $obj.data.quotaMap.PSObject.Properties | ForEach-Object { $global:telemetry[$_.Name] = $_.Value }
        }
        if ($topic -like "*/set_reply") {
            $global:lastAck = $obj
            $global:ackEvent.Set()
        }
    } catch {}
} | Out-Null

$rc = $mqtt.Connect($clientId, $cert.certificateAccount, $cert.certificatePassword, $true, 60)
if (-not $mqtt.IsConnected) { Write-Host "Verbinding mislukt" -ForegroundColor Red; exit 1 }

$topicTelemetry = "/app/device/property/$SN"
$topicGetReply  = "/app/$userId/$SN/thing/property/get_reply"
$topicSetReply  = "/app/$userId/$SN/thing/property/set_reply"
$topicGet       = "/app/$userId/$SN/thing/property/get"
$topicSet       = "/app/$userId/$SN/thing/property/set"

$mqtt.Subscribe([string[]]@($topicTelemetry, $topicSetReply, $topicGetReply), [byte[]]@(0, 1, 1)) | Out-Null

Start-Sleep -Milliseconds 500
$global:seq++
$getAll = @{ id=$global:seq; version="1.0"; sn=$SN; moduleType=0; operateType="latestQuotas"; params=@{} } | ConvertTo-Json -Compress
$mqtt.Publish($topicGet, [System.Text.Encoding]::UTF8.GetBytes($getAll), 1, $false) | Out-Null
Write-Host "Verbonden! State ophalen (8 sec)..." -ForegroundColor Green
Start-Sleep -Seconds 8

# ---- Helpers ---------------------------------------------------------
function Get-Raw { param([string]$Key)
    if ($global:telemetry.ContainsKey($Key)) { return $global:telemetry[$Key] }
    return $null
}

function Send-Cmd { param([int]$ModuleType, [string]$OperateType, [hashtable]$Params)
    $global:seq++
    $global:ackEvent.Reset()
    $global:lastAck = $null
    $cmd = @{ id=$global:seq; version="1.0"; sn=$SN; moduleType=$ModuleType; operateType=$OperateType; from="Android"; params=$Params } | ConvertTo-Json -Compress -Depth 5
    $mqtt.Publish($topicSet, [System.Text.Encoding]::UTF8.GetBytes($cmd), 1, $false) | Out-Null
}

function Get-Ack {
    $received = $global:ackEvent.Wait(8000)
    if ($received -and $global:lastAck) { return [int]$global:lastAck.data.ack }
    return -1
}

# ---- Test functies ---------------------------------------------------
function Test-Telemetry {
    param([string]$Name, [string]$AppName, [int]$ModuleType, [string]$OperateType,
          [string[]]$VerifyKeys, [hashtable]$ParamsTest, [hashtable]$ParamsRestore, [string]$Note = "")
    Write-Host ""
    Write-Host ("  [$Name] [TELEMETRIE]") -ForegroundColor White
    if ($AppName) { Write-Host ("  App: $AppName") -ForegroundColor DarkGray }
    if ($Note)    { Write-Host ("  Note: $Note") -ForegroundColor DarkGray }
    $before = @{}
    foreach ($k in $VerifyKeys) {
        $before[$k] = Get-Raw $k
        Write-Host ("    Voor  {0,-42} = {1}" -f $k, $before[$k]) -ForegroundColor Gray
    }
    Send-Cmd $ModuleType $OperateType $ParamsTest
    Start-Sleep -Seconds $WAIT_TELEMETRY_S
    $changed = $false
    foreach ($k in $VerifyKeys) {
        $after = Get-Raw $k
        $diff  = ($null -ne $after) -and ("$($before[$k])" -ne "$after")
        if ($diff) { $changed = $true }
        Write-Host ("    Na    {0,-42} = {1}" -f $k, $after) -ForegroundColor $(if ($diff) { "Green" } else { "Yellow" })
    }
    if ($changed) { Write-Host "    Resultaat: WERKT" -ForegroundColor Green }
    else          { Write-Host "    Resultaat: GEEN REACTIE" -ForegroundColor Red }
    Send-Cmd $ModuleType $OperateType $ParamsRestore
    Start-Sleep -Seconds $WAIT_RESTORE_S
    return $changed
}

function Test-AckOnly {
    param([string]$Name, [string]$AppName, [int]$ModuleType, [string]$OperateType,
          [hashtable]$ParamsTest, [hashtable]$ParamsRestore, [string]$Note = "")
    Write-Host ""
    Write-Host ("  [$Name] [ACK ONLY]") -ForegroundColor Yellow
    if ($AppName) { Write-Host ("  App: $AppName") -ForegroundColor DarkGray }
    if ($Note)    { Write-Host ("  Note: $Note") -ForegroundColor DarkGray }
    Write-Host "    Geen telemetrie feedback beschikbaar" -ForegroundColor DarkGray
    Send-Cmd $ModuleType $OperateType $ParamsTest
    $ack1 = Get-Ack
    $l1 = if ($ack1 -eq 1) { "ack=1 ONTVANGEN" } elseif ($ack1 -eq 0) { "ack=0" } else { "TIMEOUT" }
    Write-Host ("    Test:     $l1") -ForegroundColor $(if ($ack1 -eq 1) { "Green" } elseif ($ack1 -eq 0) { "Yellow" } else { "Red" })
    Start-Sleep -Seconds $WAIT_RESTORE_S
    Send-Cmd $ModuleType $OperateType $ParamsRestore
    $ack2 = Get-Ack
    Write-Host ("    Terugzet: $(if ($ack2 -eq 1) { 'ack=1' } elseif ($ack2 -eq 0) { 'ack=0' } else { 'TIMEOUT' })") -ForegroundColor $(if ($ack2 -eq 1) { "Green" } else { "DarkGray" })
    $ok = ($ack1 -eq 1) -or ($ack2 -eq 1)
    if ($ok) { Write-Host "    Resultaat: ACK ONTVANGEN (effect onbekend)" -ForegroundColor Yellow }
    else     { Write-Host "    Resultaat: GEEN ACK" -ForegroundColor Red }
    return $ok
}

function Test-Unknown {
    param([string]$Name, [string]$AppName, [int]$ModuleType, [string]$OperateType,
          [hashtable]$ParamsTest, [hashtable]$ParamsRestore, [string]$Note = "")
    Write-Host ""
    Write-Host ("  [$Name] [ONBEKEND]") -ForegroundColor DarkGray
    if ($AppName) { Write-Host ("  App: $AppName") -ForegroundColor DarkGray }
    else          { Write-Host ("  App: niet aanwezig in app") -ForegroundColor DarkGray }
    if ($Note)    { Write-Host ("  Note: $Note") -ForegroundColor DarkGray }
    Send-Cmd $ModuleType $OperateType $ParamsTest
    $ack1 = Get-Ack
    Write-Host ("    Test:     $(if ($ack1 -eq 1) { 'ack=1' } elseif ($ack1 -eq 0) { 'ack=0' } else { 'TIMEOUT' })") -ForegroundColor $(if ($ack1 -eq 1) { "Cyan" } elseif ($ack1 -eq 0) { "Yellow" } else { "Red" })
    Start-Sleep -Seconds $WAIT_RESTORE_S
    Send-Cmd $ModuleType $OperateType $ParamsRestore
    $ack2 = Get-Ack
    Write-Host ("    Terugzet: $(if ($ack2 -eq 1) { 'ack=1' } elseif ($ack2 -eq 0) { 'ack=0' } else { 'TIMEOUT' })") -ForegroundColor DarkGray
    return $ack1
}

function Test-Number {
    param([string]$Name, [string]$AppName, [int]$ModuleType, [string]$OperateType,
          [string]$TelemetryKey, [string]$ParamKey, [int]$StepSize, [int]$Min, [int]$Max,
          [hashtable]$ExtraParams = @{}, [string]$Note = "")
    Write-Host ""
    Write-Host ("  [$Name] [TELEMETRIE]") -ForegroundColor White
    if ($AppName) { Write-Host ("  App: $AppName") -ForegroundColor DarkGray }
    if ($Note)    { Write-Host ("  Note: $Note") -ForegroundColor DarkGray }
    $current = Get-Raw $TelemetryKey
    if ($null -eq $current) { Write-Host ("    SKIP -- $TelemetryKey niet in telemetrie") -ForegroundColor Yellow; return $null }
    $currentInt = [int]$current
    if ($currentInt -eq 255) { Write-Host ("    SKIP -- waarde 255 is sentinel/keep-current") -ForegroundColor Yellow; return $null }
    $rounded = [int]([Math]::Round($currentInt / $StepSize) * $StepSize)
    $testVal = if (($rounded + $StepSize) -le $Max) { $rounded + $StepSize } else { $rounded - $StepSize }
    if ($testVal -lt $Min) { $testVal = $Min + $StepSize }
    Write-Host ("    Voor  {0,-42} = {1}" -f $TelemetryKey, $currentInt) -ForegroundColor Gray
    Write-Host ("    Testwaarde: $testVal  (origineel: $currentInt)") -ForegroundColor White
    $pTest    = @{}; foreach ($kv in $ExtraParams.GetEnumerator()) { $pTest[$kv.Key] = $kv.Value }; $pTest[$ParamKey] = $testVal
    $pRestore = @{}; foreach ($kv in $ExtraParams.GetEnumerator()) { $pRestore[$kv.Key] = $kv.Value }; $pRestore[$ParamKey] = $currentInt
    Send-Cmd $ModuleType $OperateType $pTest
    Start-Sleep -Seconds $WAIT_TELEMETRY_S
    $after   = Get-Raw $TelemetryKey
    $changed = ($null -ne $after) -and ([int]$after -ne $currentInt)
    Write-Host ("    Na    {0,-42} = {1}" -f $TelemetryKey, $after) -ForegroundColor $(if ($changed) { "Green" } else { "Red" })
    if ($changed) { Write-Host "    Resultaat: WERKT" -ForegroundColor Green }
    else          { Write-Host "    Resultaat: GEEN REACTIE" -ForegroundColor Red }
    Send-Cmd $ModuleType $OperateType $pRestore
    Start-Sleep -Seconds $WAIT_RESTORE_S
    return $changed
}

function Test-Select {
    param([string]$Name, [string]$AppName, [int]$ModuleType, [string]$OperateType,
          [string]$TelemetryKey, [string]$ParamKey, [int[]]$Options,
          [hashtable]$ExtraParams = @{}, [string]$Note = "")
    Write-Host ""
    Write-Host ("  [$Name] [SELECT/TELEMETRIE]") -ForegroundColor White
    if ($AppName) { Write-Host ("  App: $AppName") -ForegroundColor DarkGray }
    if ($Note)    { Write-Host ("  Note: $Note") -ForegroundColor DarkGray }
    $current = Get-Raw $TelemetryKey
    if ($null -eq $current) { Write-Host ("    SKIP -- $TelemetryKey niet in telemetrie") -ForegroundColor Yellow; return $null }
    $currentInt = [int]$current
    $idx     = [Array]::IndexOf($Options, $currentInt)
    $testVal = if ($idx -ge 0 -and $idx -lt ($Options.Count - 1)) { $Options[$idx + 1] } else { $Options[0] }
    Write-Host ("    Voor  {0,-42} = {1}" -f $TelemetryKey, $currentInt) -ForegroundColor Gray
    Write-Host ("    Testwaarde: $testVal  (origineel: $currentInt)") -ForegroundColor White
    $pTest    = @{}; foreach ($kv in $ExtraParams.GetEnumerator()) { $pTest[$kv.Key] = $kv.Value }; $pTest[$ParamKey] = $testVal
    $pRestore = @{}; foreach ($kv in $ExtraParams.GetEnumerator()) { $pRestore[$kv.Key] = $kv.Value }; $pRestore[$ParamKey] = $currentInt
    Send-Cmd $ModuleType $OperateType $pTest
    Start-Sleep -Seconds $WAIT_TELEMETRY_S
    $after   = Get-Raw $TelemetryKey
    $changed = ($null -ne $after) -and ([int]$after -ne $currentInt)
    Write-Host ("    Na    {0,-42} = {1}" -f $TelemetryKey, $after) -ForegroundColor $(if ($changed) { "Green" } else { "Red" })
    if ($changed) { Write-Host "    Resultaat: WERKT" -ForegroundColor Green }
    else          { Write-Host "    Resultaat: GEEN REACTIE" -ForegroundColor Red }
    Send-Cmd $ModuleType $OperateType $pRestore
    Start-Sleep -Seconds $WAIT_RESTORE_S
    return $changed
}

# ====================================================================
# TESTS
# ====================================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  EcoFlow Delta 3 1500 -- Entiteitstest v0.2.23" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  [TELEMETRIE]      = MQTT state key verandert aantoonbaar" -ForegroundColor White
Write-Host "  [SELECT/TELEMETRIE] = discrete optie — telemetrie verificatie" -ForegroundColor White
Write-Host "  [ACK ONLY]        = geen telemetrie, ack=1 enige bevestiging" -ForegroundColor Yellow
Write-Host "  [ONBEKEND]        = niet in app, geen telemetrie, ack als indicator" -ForegroundColor DarkGray
Write-Host ""

$results = [ordered]@{}

# ====================================================================
Write-Host "---- SWITCHES (telemetrie bevestigd) ----" -ForegroundColor Cyan
# ====================================================================

$results["AC Output"] = Test-Telemetry "AC Output" "AC uitgang" 5 "acOutCfg" @("pd.acEnabled") `
    @{ enabled=0; xboost=255; out_voltage=-1; out_freq=255 } `
    @{ enabled=1; xboost=255; out_voltage=-1; out_freq=255 }

$results["X-Boost"] = Test-Telemetry "X-Boost" "X-Boost" 5 "acOutCfg" @("mppt.cfgAcXboost", "inv.cfgAcXboost") `
    @{ enabled=255; xboost=1; out_voltage=4294967295; out_freq=255 } `
    @{ enabled=255; xboost=0; out_voltage=4294967295; out_freq=255 }

$results["USB Output"] = Test-Telemetry "USB Output" "USB uitgang" 1 "dcOutCfg" @("pd.dcOutState") `
    @{ enabled=1 } @{ enabled=0 }

$results["DC Output"] = Test-Telemetry "DC Output" "12V/auto uitgang" 5 "mpptCar" @("mppt.carState") `
    @{ enabled=1 } @{ enabled=0 }

$results["Backup Reserve"] = Test-Telemetry "Backup Reserve" "Energiebeheer schakelaar" 1 "watthConfig" @("pd.watchIsConfig") `
    @{ isConfig=1; bpPowerSoc=0; minDsgSoc=0; minChgSoc=0 } `
    @{ isConfig=0; bpPowerSoc=0; minDsgSoc=0; minChgSoc=0 } `
    "pd.watchIsConfig bevestigd via live MQTT observatie"

# Beep: beepState=1=geluid AAN → stuur enabled=1 (quiet=aan=geluid UIT)
$beepCurrent = if ($null -eq (Get-Raw "mppt.beepState")) { 0 } else { [int](Get-Raw "mppt.beepState") }
$beepTest    = if ($beepCurrent -eq 1) { @{ enabled=1 } } else { @{ enabled=0 } }
$beepRestore = if ($beepCurrent -eq 1) { @{ enabled=0 } } else { @{ enabled=1 } }
$results["Beep"] = Test-Telemetry "Beep" "Geluid aan/uit" 5 "quietMode" @("mppt.beepState") `
    $beepTest $beepRestore "omgekeerde logica: enabled=1=quiet aan=geluid UIT"

# AC Charging: inverted — chgPauseFlag=0=laden AAN
$results["AC Charging"] = Test-Telemetry "AC Charging" "AC laden (pause)" 5 "acChgCfg" @("mppt.chgPauseFlag") `
    @{ chgWatts=255; chgPauseFlag=1 } `
    @{ chgWatts=255; chgPauseFlag=0 } `
    "chgPauseFlag: 0=laden AAN, 1=laden GEPAUZEERD"

# ====================================================================
Write-Host ""
Write-Host "---- SWITCHES (ack only — geen telemetrie) ----" -ForegroundColor Yellow
# ====================================================================

$results["Output Memory"] = Test-AckOnly "Output Memory" "Geheugen van uitgangen" 1 "outputMemory" `
    @{ outputMemoryEn=1 } @{ outputMemoryEn=0 } "geen telemetrie feedback op D361"

$results["Bypass"] = Test-AckOnly "Bypass" "Doorsluizen" 1 "bypassBan" `
    @{ banBypassEn=0 } @{ banBypassEn=1 } "geen telemetrie feedback op D361"

# ====================================================================
Write-Host ""
Write-Host "---- SWITCHES (onbekend — niet in app) ----" -ForegroundColor DarkGray
# ====================================================================

$results["Solar Priority"] = Test-Unknown "Solar Priority" "" 1 "pvChangePrio" `
    @{ pvChangeSet=1 } @{ pvChangeSet=0 } "pd.pvChgPrioSet in get-all maar nooit als WIJZIG gezien"

$results["AC Auto-On"] = Test-Unknown "AC Auto-On" "" 3 "acAutoOnCfg" `
    @{ enabled=1 } @{ enabled=0 } "pd.acAutoOnCfg in get-all maar nooit als WIJZIG gezien"

$results["AC Always-On"] = Test-Unknown "AC Always-On" "" 1 "acAutoOutConfig" `
    @{ acAutoOutConfig=1; minAcOutSoc=0 } @{ acAutoOutConfig=0; minAcOutSoc=0 } "pd.acAutoOutConfig in get-all"

# ====================================================================
Write-Host ""
Write-Host "---- NUMBERS (telemetrie bevestigd) ----" -ForegroundColor Cyan
# ====================================================================

$results["AC Charging Speed"] = Test-Number "AC Charging Speed" "Oplaadstroom (W)" 5 "acChgCfg" `
    "mppt.cfgChgWatts" "chgWatts" 100 200 1500 @{ chgPauseFlag=255 } `
    "255=sentinel wordt geskipt; shadow state in integratie"

$results["Max Charge Level"] = Test-Number "Max Charge Level" "Max oplaadniveau" 2 "upsConfig" `
    "bms_emsStatus.maxChargeSoc" "maxChgSoc" 5 50 100

$results["Min Discharge Level"] = Test-Number "Min Discharge Level" "Min ontlaadniveau" 2 "dsgCfg" `
    "bms_emsStatus.minDsgSoc" "minDsgSoc" 5 0 30

$results["Generator Start SOC"] = Test-Number "Generator Start SOC" "" 2 "openOilSoc" `
    "bms_emsStatus.minOpenOilEb" "openOilSoc" 5 0 30 @{} "generator feature"

$results["Generator Stop SOC"] = Test-Number "Generator Stop SOC" "" 2 "closeOilSoc" `
    "bms_emsStatus.maxCloseOilEb" "closeOilSoc" 5 50 100 @{} "generator feature"

$results["Backup Reserve SOC"] = Test-Number "Backup Reserve SOC" "Noodstroom niveau slider" 1 "watthConfig" `
    "pd.bpPowerSoc" "bpPowerSoc" 5 5 100 @{ isConfig=1; minDsgSoc=0; minChgSoc=0 }

$results["LCD Brightness"] = Test-Number "LCD Brightness" "" 1 "lcdCfg" `
    "pd.brightLevel" "brighLevel" 1 0 3 @{ delayOff=65535 } "0-3 discrete niveaus"

$results["Min SOC AC Auto-On"] = Test-Number "Min SOC AC Auto-On" "" 1 "acAutoOutConfig" `
    "pd.minAcoutSoc" "minAcOutSoc" 5 0 100 @{ acAutoOutConfig=255 } "niet in app, effect onbekend"

# Read-only numbers — alleen state tonen, geen SET
Write-Host ""
Write-Host "  [Screen Standby / Overall Standby] [READ ONLY]" -ForegroundColor DarkGray
Write-Host ("    mppt.scrStandbyMin = {0}" -f (Get-Raw "mppt.scrStandbyMin")) -ForegroundColor DarkGray
Write-Host ("    mppt.powStandbyMin = {0}" -f (Get-Raw "mppt.powStandbyMin")) -ForegroundColor DarkGray
Write-Host "    Note: operateType onbekend — read-only in v0.2.23" -ForegroundColor DarkGray

# ====================================================================
Write-Host ""
Write-Host "---- SELECTS (telemetrie bevestigd) ----" -ForegroundColor Cyan
# ====================================================================

# Screen Timeout: opties 0,10,30,60,300,1800
$results["Screen Timeout"] = Test-Select "Screen Timeout" "" 1 "lcdCfg" `
    "pd.lcdOffSec" "delayOff" @(0, 10, 30, 60, 300, 1800) @{ brighLevel=255 } `
    "vaste opties per officiële doc"

# Unit Standby: opties in minuten
$results["Unit Standby"] = Test-Select "Unit Standby" "" 1 "standbyTime" `
    "pd.standbyMin" "standbyMin" @(0, 30, 60, 120, 240, 360, 720, 1440)

# AC Standby
$results["AC Standby"] = Test-Select "AC Standby" "" 5 "standby" `
    "mppt.acStandbyMins" "standbyMins" @(0, 30, 60, 120, 240, 360, 720, 1440)

# DC 12V Standby
$results["DC 12V Standby"] = Test-Select "DC 12V Standby" "" 5 "carStandby" `
    "mppt.carStandbyMin" "standbyMins" @(0, 30, 60, 120, 240, 360, 720, 1440)

# DC Charge Current: bevestigd via live MQTT
$results["DC Charge Current"] = Test-Select "DC Charge Current" "Auto ingang (4A/6A/8A)" 5 "dcChgCfg" `
    "mppt.dcChgCurrent" "dcChgCfg" @(4000, 6000, 8000)

# ====================================================================
# SAMENVATTING
# ====================================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SAMENVATTING" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$ok = 0; $fail = 0; $skip = 0; $ackOk = 0; $ackFail = 0

Write-Host ""
Write-Host "  [TELEMETRIE / SELECT]" -ForegroundColor White
$telKeys = @("AC Output","X-Boost","USB Output","DC Output","Backup Reserve","Beep","AC Charging",
             "AC Charging Speed","Max Charge Level","Min Discharge Level","Generator Start SOC",
             "Generator Stop SOC","Backup Reserve SOC","LCD Brightness","Min SOC AC Auto-On",
             "Screen Timeout","Unit Standby","AC Standby","DC 12V Standby","DC Charge Current")
foreach ($key in $telKeys) {
    $val = $results[$key]
    if ($null -eq $val)     { Write-Host ("    {0,-30} SKIP"          -f $key) -ForegroundColor Yellow; $skip++ }
    elseif ($val -eq $true) { Write-Host ("    {0,-30} OK"            -f $key) -ForegroundColor Green;  $ok++ }
    else                    { Write-Host ("    {0,-30} GEEN REACTIE"  -f $key) -ForegroundColor Red;    $fail++ }
}

Write-Host ""
Write-Host "  [ACK ONLY]" -ForegroundColor Yellow
foreach ($key in @("Output Memory","Bypass")) {
    $val = $results[$key]
    if ($val -eq $true) { Write-Host ("    {0,-30} ACK ONTVANGEN" -f $key) -ForegroundColor Yellow; $ackOk++ }
    else                { Write-Host ("    {0,-30} GEEN ACK"       -f $key) -ForegroundColor Red;   $ackFail++ }
}

Write-Host ""
Write-Host "  [ONBEKEND]" -ForegroundColor DarkGray
foreach ($key in @("Solar Priority","AC Auto-On","AC Always-On")) {
    $val   = $results[$key]
    $label = if ($val -eq 1) { "ack=1" } elseif ($val -eq 0) { "ack=0" } else { "TIMEOUT" }
    Write-Host ("    {0,-30} $label" -f $key) -ForegroundColor $(if ($val -eq 1) { "Cyan" } elseif ($val -eq 0) { "Yellow" } else { "Red" })
}

Write-Host ""
Write-Host ("  Telemetrie/Select OK: $ok  |  Geen reactie: $fail  |  Skip: $skip") -ForegroundColor Cyan
Write-Host ("  Ack only OK: $ackOk  |  Geen ack: $ackFail") -ForegroundColor Yellow

$mqtt.Disconnect()
Write-Host ""
Write-Host "Klaar."
