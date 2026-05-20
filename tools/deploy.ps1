param(
    [string]$Port = "COM3"
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$mpremote = Join-Path $projectRoot ".venv\Scripts\mpremote.exe"

if (Test-Path $mpremote) {
    $script:MpremoteExe = $mpremote
} else {
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) {
        $localUv = Join-Path $env:USERPROFILE ".local\bin\uv.exe"
        if (Test-Path $localUv) {
            $uv = [PSCustomObject]@{ Source = $localUv }
        }
    }

    if (-not $uv) {
        Write-Error "uv not found. Run tools\check_env.ps1 -Fix first."
        exit 1
    }

    $script:UvExe = $uv.Source
}

function Invoke-Mpremote {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$MpArgs
    )

    if ($script:MpremoteExe) {
        & $script:MpremoteExe @MpArgs
    } else {
        & $script:UvExe run mpremote @MpArgs
    }

    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

Invoke-Mpremote connect $Port cp boot.py :
Invoke-Mpremote connect $Port cp main.py :
Invoke-Mpremote connect $Port cp -r ./lib :
Invoke-Mpremote connect $Port reset
