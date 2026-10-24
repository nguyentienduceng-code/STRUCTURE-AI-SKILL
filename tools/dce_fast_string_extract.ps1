#!/usr/bin/env pwsh
# dce_fast_string_extract.ps1 - Fast string extraction from DCE Pro DLLs

param(
    [string]$OutputDir = "g:\My Drive\Google AI Studio\.agents\docs"
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "SilentlyContinue"

$Dlls = @(
    "C:\Dce Pro\DCE Pro.dll",
    "C:\Dce Pro\V.2020\DCE Excel.dll",
    "C:\Dce Pro\DbimSteelAutocad.dll"
)

Write-Host "="*70 -ForegroundColor Cyan
Write-Host "DCE Pro - Fast String Extraction" -ForegroundColor Cyan
Write-Host "="*70

$AllStrings = @{}
$ExcelStrings = @()
$XDataStrings = @()
$CommandStrings = @()
$LayerStrings = @()
$BlockStrings = @()

foreach ($Dll in $Dlls) {
    if (-not (Test-Path $Dll)) {
        Write-Host "SKIP: $Dll (not found)" -ForegroundColor Gray
        continue
    }

    Write-Host "`nExtracting: $Dll" -ForegroundColor Yellow

    # Method 1: Binary read and find strings
    $data = [System.IO.File]::ReadAllBytes($Dll)
    $buffer = [System.Text.StringBuilder]::new()
    $minLen = 4
    $maxLen = 200

    for ($i = 0; $i -lt $data.Length; $i++) {
        $b = $data[$i]

        if ($b -ge 32 -and $b -lt 127) {
            [void]$buffer.Append([char]$b)
        } else {
            $s = $buffer.ToString()
            $buffer.Clear() | Out-Null

            if ($s.Length -ge $minLen -and $s.Length -le $maxLen -and $s -match '[A-Za-z]') {
                $AllStrings[$s] = $true

                # Categorize
                if ($s -match '^[A-Z]{1,3}\d+$' -or $s -match '^[A-Z]{1,3}\d+:[A-Z]{1,3}\d+$') {
                    $ExcelStrings += $s
                }
                if ($s -in @('SH','DK','SL','L','TK','SKC','TSL','KL','sumL','Lall','L1','L2','L3')) {
                    $XDataStrings += $s
                }
                if ($s -match '^(VeDam|VeCot|VeVach|VeSan|GanDL|QuetThongKe|SuaCK|GanLienKet)$') {
                    $CommandStrings += $s
                }
                if ($s -match '^Dce_' -or $s -match '^KC_') {
                    $LayerStrings += $s
                }
                if ($s -match '^TK\d+[a-zA-Z]*$' -or $s -match '^Dce_Kh') {
                    $BlockStrings += $s
                }
            }
        }
    }

    Write-Host "  Total strings: $($AllStrings.Count)" -ForegroundColor Gray
}

Write-Host "`n" + ("="*70) -ForegroundColor Cyan
Write-Host "RESULTS" -ForegroundColor Cyan
Write-Host ("="*70) -ForegroundColor Cyan

# Unique sorted
$ExcelUnique = ($ExcelStrings | Sort-Object -Unique)
$XDataUnique = ($XDataStrings | Sort-Object -Unique)
$CommandUnique = ($CommandStrings | Sort-Object -Unique)
$LayerUnique = ($LayerStrings | Sort-Object -Unique)
$BlockUnique = ($BlockStrings | Sort-Object -Unique)

Write-Host "`n=== EXCEL PATTERNS ===" -ForegroundColor Green
Write-Host "Cell refs: $($ExcelUnique.Count)"
$ExcelUnique | Select-Object -First 50 | ForEach-Object { Write-Host "  $_" }

Write-Host "`n=== XDATA FIELD TAGS ===" -ForegroundColor Green
Write-Host "Tags found: $($XDataUnique.Count)"
$XDataUnique | ForEach-Object { Write-Host "  $_" }

Write-Host "`n=== DCE COMMANDS ===" -ForegroundColor Green
Write-Host "Commands found: $($CommandUnique.Count)"
$CommandUnique | ForEach-Object { Write-Host "  $_" }

Write-Host "`n=== DCE LAYERS ===" -ForegroundColor Green
Write-Host "Layers found: $($LayerUnique.Count)"
$LayerUnique | Select-Object -First 30 | ForEach-Object { Write-Host "  $_" }

Write-Host "`n=== DCE BLOCKS ===" -ForegroundColor Green
Write-Host "Blocks found: $($BlockUnique.Count)"
$BlockUnique | Select-Object -First 30 | ForEach-Object { Write-Host "  $_" }

# Save to JSON
$Output = @{
    metadata = @{
        generated_at = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
        total_strings = $AllStrings.Count
    }
    excel_bus = @{
        cell_refs = @($ExcelUnique | Select-Object -First 500)
    }
    xdata_protocol = @{
        field_tags = @($XDataUnique)
        regapp_name = "DBIM"  # Most likely based on DCE Pro naming convention
    }
    cad_integration = @{
        layers = @($LayerUnique | Select-Object -First 100)
        blocks = @($BlockUnique | Select-Object -First 100)
        commands = @($CommandUnique)
    }
    all_strings_sample = @($AllStrings.Keys | Where-Object {
        $_.Length -gt 5 -and $_.Length -lt 100 -and $_ -notmatch '^[\x00-\x1F]+$'
    } | Select-Object -First 500)
}

$jsonPath = Join-Path $OutputDir "DCE_DEEP_OPERATION_SCHEMA.json"
$Output | ConvertTo-Json -Depth 10 | Out-File -FilePath $jsonPath -Encoding UTF8
Write-Host "`nSaved: $jsonPath" -ForegroundColor Green

Write-Host "`nDone!" -ForegroundColor Cyan
