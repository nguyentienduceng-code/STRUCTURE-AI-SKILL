# dce_il_string_extractor.ps1
# Trích xuất chính xác các chuỗi hằng số của từng phương thức bằng:
# [System.Reflection.Assembly]::ReflectionOnlyLoadFrom($dllPath)
# kết hợp $method.GetMethodBody().GetILAsByteArray() và $module.ResolveString($token) tại opcode 0x72 (ldstr).

param(
    [string]$OutJsonPath = "G:\My Drive\Google AI Studio\.agents\docs\DCE_IL_EXTRACTED_STRINGS.json"
)

$ErrorActionPreference = "Continue"

# 1. Setup Assembly Resolution for ReflectionOnly and LoadFrom
$dceDirs = @(
    "C:\Dce Pro",
    "C:\Dce Pro\AddinSteelCad",
    "C:\Dce Pro\AddinSteel",
    "C:\Dce Pro\AddinRevit\AddinDbimDcepro",
    "C:\Dce Pro\V.2020",
    "C:\Program Files\Autodesk\AutoCAD 2021",
    "C:\Program Files\Autodesk\Revit 2021"
)

$dllLookup = @{}
foreach ($dir in $dceDirs) {
    if (Test-Path $dir) {
        Get-ChildItem -Path $dir -Filter *.dll -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            $nameKey = $_.Name.ToLower()
            if (-not $dllLookup.ContainsKey($nameKey)) {
                $dllLookup[$nameKey] = $_.FullName
            }
        }
    }
}

$script:resolving = New-Object 'System.Collections.Generic.HashSet[string]'
$resolveHandler = {
    param($sender, $args)
    if (-not $args.Name) { return $null }
    $rawName = ($args.Name.Split(',')[0]).Trim().ToLower()
    if ($script:resolving.Contains($rawName)) { return $null }
    [void]$script:resolving.Add($rawName)
    
    try { return [System.Reflection.Assembly]::ReflectionOnlyLoad($args.Name) } catch {}
    
    $dllFile = "$rawName.dll"
    if ($dllLookup.ContainsKey($dllFile)) {
        try { return [System.Reflection.Assembly]::ReflectionOnlyLoadFrom($dllLookup[$dllFile]) } catch {}
    }
    return $null
}

[System.AppDomain]::CurrentDomain.add_ReflectionOnlyAssemblyResolve($resolveHandler)

# 2. Target Assemblies to inspect
$targetDlls = @(
    "C:\Dce Pro\DCE Pro.dll",
    "C:\Dce Pro\AddinSteelCad\DbimSteelAutocad-ToanHuynh-2.dll",
    "C:\Dce Pro\AddinSteelCad\DbimSteelAutocad.dll",
    "C:\Dce Pro\AddinSteel\DceSteel-DESKTOP-BT5QG2E.dll",
    "C:\Dce Pro\AddinSteel\DceSteel.dll",
    "C:\Dce Pro\V.2020\DCE Excel.dll",
    "C:\Dce Pro\BcDCE Pro.dll",
    "C:\Dce Pro\ZwDCE Pro.dll",
    "C:\Dce Pro\GcDCE Pro.dll",
    "C:\Dce Pro\IcDCE Pro.dll"
)

$allAssemblyResults = [ordered]@{}
$grandTotalMethodsWithLdstr = 0
$grandTotalLdstrStrings = 0

foreach ($dllPath in $targetDlls) {
    if (-not (Test-Path $dllPath)) {
        Write-Host "[SKIP] File not found: $dllPath"
        continue
    }
    
    $dllName = [System.IO.Path]::GetFileName($dllPath)
    Write-Host "[SCAN] Dang phan tich IL opcode 0x72 trong: $dllName"
    
    $asm = $null
    $modeUsed = "ReflectionOnlyLoadFrom"
    try {
        $asm = [System.Reflection.Assembly]::ReflectionOnlyLoadFrom($dllPath)
    } catch {
        try {
            $asm = [System.Reflection.Assembly]::LoadFrom($dllPath)
            $modeUsed = "LoadFrom"
        } catch {
            Write-Host "  [WARN] Khong the nap $dllName : $_"
            continue
        }
    }
    
    $mod = $asm.ManifestModule
    $types = @()
    try {
        $types = $asm.GetTypes()
    } catch [System.Reflection.ReflectionTypeLoadException] {
        $types = $_.Exception.Types | Where-Object { $_ -ne $null }
    }
    
    $methodsMap = [ordered]@{}
    $assemblyTotalLdstr = 0
    $assemblyMethodsWithLdstr = 0
    
    foreach ($t in $types) {
        $methods = @()
        try {
            $methods = $t.GetMethods([System.Reflection.BindingFlags]"Public,NonPublic,Static,Instance,DeclaredOnly")
        } catch {}
        
        foreach ($m in $methods) {
            $body = $null
            try { $body = $m.GetMethodBody() } catch {}
            if (-not $body) { continue }
            $il = $null
            try { $il = $body.GetILAsByteArray() } catch {}
            if (-not $il -or $il.Length -lt 5) { continue }
            
            $methodStrings = @()
            for ($i = 0; $i -lt $il.Length - 4; $i++) {
                if ($il[$i] -eq 0x72) { # ldstr opcode
                    $token = [System.BitConverter]::ToInt32($il, $i + 1)
                    try {
                        $s = $mod.ResolveString($token)
                        if ($s -ne $null) {
                            $methodStrings += $s
                        }
                    } catch {}
                    $i += 4
                }
            }
            
            if ($methodStrings.Count -gt 0) {
                $methodKey = "$($t.FullName)::$($m.Name)"
                $methodsMap[$methodKey] = $methodStrings
                $assemblyMethodsWithLdstr++
                $assemblyTotalLdstr += $methodStrings.Count
            }
        }
    }
    
    $grandTotalMethodsWithLdstr += $assemblyMethodsWithLdstr
    $grandTotalLdstrStrings += $assemblyTotalLdstr
    
    Write-Host "  -> $dllName : $assemblyMethodsWithLdstr methods co ldstr, tong $assemblyTotalLdstr chuoi trich xuat ($modeUsed)."
    
    $allAssemblyResults[$dllName] = [ordered]@{
        dll_path = $dllPath
        load_mode = $modeUsed
        total_types = $types.Count
        methods_with_ldstr = $assemblyMethodsWithLdstr
        total_ldstr_count = $assemblyTotalLdstr
        methods = $methodsMap
    }
}

$summary = [ordered]@{
    extracted_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
    description = "Exact method string constants extracted via ReflectionOnlyLoadFrom + GetMethodBody().GetILAsByteArray() at opcode 0x72 (ldstr) and ResolveString"
    total_assemblies_scanned = $allAssemblyResults.Count
    grand_total_methods_with_ldstr = $grandTotalMethodsWithLdstr
    grand_total_ldstr_strings = $grandTotalLdstrStrings
    assemblies = $allAssemblyResults
}

$jsonText = $summary | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText($OutJsonPath, $jsonText, [System.Text.Encoding]::UTF8)
Write-Host "[OK] Da xuat toan bo hoso string IL ra: $OutJsonPath ($grandTotalLdstrStrings chuoi)."
