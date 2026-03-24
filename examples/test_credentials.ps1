# test_credentials.ps1
# EcoFlow API Credential Diagnostic Tool (PowerShell)
#
# Tests all three EcoFlow API servers with your credentials and shows:
#   - Which server works for authentication
#   - Which devices are linked to your API key
#   - Whether your device serial number is found
#
# Run: PowerShell -ExecutionPolicy Bypass -File test_credentials.ps1

# -- Fill in your credentials ---------------------------------------------
$ACCESS_KEY = ""     # From https://developer-eu.ecoflow.com/us/security
$SECRET_KEY = ""     # From https://developer-eu.ecoflow.com/us/security
$DEVICE_SN  = ""     # Your device serial number (e.g. D361ZEH49GAR0848)
# -- End credentials -------------------------------------------------------

$SERVERS = [ordered]@{
    "EU     (api-e.ecoflow.com)" = "https://api-e.ecoflow.com"
    "US     (api-a.ecoflow.com)" = "https://api-a.ecoflow.com"
    "Global (api.ecoflow.com)"   = "https://api.ecoflow.com"
}

function Get-SignedHeaders {
    param([string]$AccessKey, [string]$SecretKey)

    $nonce = "$(Get-Random -Minimum 100000 -Maximum 999999)"
    $timestamp = "$([long]([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()))"
    $signInput = "accessKey=$AccessKey&nonce=$nonce&timestamp=$timestamp"

    $hmacsha = New-Object System.Security.Cryptography.HMACSHA256
    $hmacsha.Key = [System.Text.Encoding]::UTF8.GetBytes($SecretKey)
    $hash = $hmacsha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($signInput))
    $sign = -join ($hash | ForEach-Object { $_.ToString("x2") })

    return @{
        "Content-Type" = "application/json"
        "accessKey"    = $AccessKey
        "nonce"        = $nonce
        "timestamp"    = $timestamp
        "sign"         = $sign
    }
}

function Test-Server {
    param([string]$Label, [string]$Host_)

    Write-Host ""
    Write-Host ("=" * 60)
    Write-Host "Testing: $Label"
    Write-Host "URL    : $Host_"

    # Step 1: authentication via /certification
    try {
        $headers = Get-SignedHeaders -AccessKey $ACCESS_KEY -SecretKey $SECRET_KEY
        $resp = Invoke-RestMethod -Uri "$Host_/iot-open/sign/certification" `
            -Headers $headers -Method GET -TimeoutSec 10
    } catch {
        Write-Host "Auth   : FAIL - $_"
        return $false
    }

    if ("$($resp.code)" -ne "0") {
        Write-Host "Auth   : FAIL - $($resp.code): $($resp.message)"
        return $false
    }
    Write-Host "Auth   : OK"

    # Step 2: device list
    try {
        $headers = Get-SignedHeaders -AccessKey $ACCESS_KEY -SecretKey $SECRET_KEY
        $resp = Invoke-RestMethod -Uri "$Host_/iot-open/sign/device/list" `
            -Headers $headers -Method GET -TimeoutSec 10
    } catch {
        Write-Host "Devices: FAIL - $_"
        return $true  # auth worked
    }

    if ("$($resp.code)" -ne "0") {
        Write-Host "Devices: FAIL - $($resp.code): $($resp.message)"
        return $true
    }

    $devices = $resp.data
    if (-not $devices -or ($devices -isnot [array])) {
        Write-Host "Devices: WARNING - No devices found on this account"
        return $true
    }

    Write-Host "Devices: OK - $($devices.Count) device(s) found:"
    $foundSN = $false
    foreach ($d in $devices) {
        $sn = $d.sn
        $name = if ($d.productName) { $d.productName } elseif ($d.deviceName) { $d.deviceName } else { "Unknown" }
        $mark = ""
        if ($sn -eq $DEVICE_SN) { $mark = " <-- YOUR DEVICE"; $foundSN = $true }
        Write-Host "           $name | SN: $sn$mark"
    }

    if ($DEVICE_SN -and -not $foundSN) {
        Write-Host ""
        Write-Host "WARNING: Serial '$DEVICE_SN' NOT found on this account!"
        $sns = ($devices | ForEach-Object { $_.sn }) -join ", "
        Write-Host "         Check for typos. Found SNs: $sns"
    }

    return $true
}

# -- Main ------------------------------------------------------------------
Write-Host "EcoFlow API Credential Diagnostic Tool (PowerShell)"

if (-not $ACCESS_KEY -or -not $SECRET_KEY) {
    Write-Host ""
    Write-Host "ERROR: Fill in ACCESS_KEY and SECRET_KEY before running."
    Write-Host "       Get them from https://developer-eu.ecoflow.com/us/security"
    exit 1
}

Write-Host "Access Key : $($ACCESS_KEY.Substring(0,6))...$($ACCESS_KEY.Substring($ACCESS_KEY.Length-4))"
if ($DEVICE_SN) { Write-Host "Device SN  : $DEVICE_SN" }
else            { Write-Host "Device SN  : (not set - will skip SN check)" }

$working = @()
foreach ($label in $SERVERS.Keys) {
    $host_ = $SERVERS[$label]
    $ok = Test-Server -Label $label -Host_ $host_
    if ($ok) { $working += $host_ }
}

Write-Host ""
Write-Host ("=" * 60)
Write-Host "SUMMARY"
if ($working.Count -gt 0) {
    Write-Host "OK: Working server(s): $($working -join ', ')"
    Write-Host "   Use the first one in the HA integration setup."
} else {
    Write-Host "FAIL: No server worked. Check your credentials."
}

Write-Host ""
Write-Host "Press Enter to close..."
Read-Host
