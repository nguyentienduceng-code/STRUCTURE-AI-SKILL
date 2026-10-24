#!/usr/bin/env pwsh
# dce_il_decompiler_dotnet.ps1
# Deep IL Analysis using .NET Metadata Reader + Reflection

param(
    [string]$DllPath = "C:\Dce Pro\DCE Pro.dll",
    [string]$OutputDir = "g:\My Drive\Google AI Studio\.agents\docs"
)

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "DCE Pro IL Deep Analysis via System.Reflection.Metadata" -ForegroundColor Cyan
Write-Host "=" * 70

# Load .NET reflection assemblies
Add-Type -AssemblyName System.Reflection.Metadata
Add-Type -AssemblyName System.Reflection.Metadata.Ecma335

# Helper function to resolve metadata token
function Resolve-Token {
    param($reader, $handle)

    if ($handle.Kind -eq [System.Reflection.Metadata.EntityHandleKind]::MemberReference) {
        $mr = $reader.GetMemberReference(([System.Reflection.Metadata.EntityHandle]$handle))
        $parent = $mr.Parent
        $name = $reader.GetString($mr.Name)

        # Get parent type name
        $parentName = ""
        try {
            if ($parent.Kind -eq [System.Reflection.Metadata.EntityHandleKind]::TypeReference) {
                $tr = $reader.GetTypeReference(([System.Reflection.Metadata.EntityHandle]$parent))
                $parentName = $reader.GetString($tr.Name)
            } elseif ($parent.Kind -eq [System.Reflection.Metadata.EntityHandleKind]::TypeDefinition) {
                $td = $reader.GetTypeDefinition(([System.Reflection.Metadata.EntityHandle]$parent))
                $parentName = $reader.GetString($td.Name)
            }
        } catch {}

        return "$parentName::$name"
    }
    return "unknown"
}

# Main analysis
try {
    Write-Host "`nLoading: $DllPath" -ForegroundColor Yellow

    $peStream = [System.IO.File]::OpenRead($DllPath)
    $metadataReader = [System.Reflection.Metadata.MetadataReaderProvider]::FromPortablePdbStream($peStream)

    # Actually use the file directly
    $peReader = [System.Reflection.Metadata.PortableExecutable.PEReader]::new($peStream)
    $metadataProvider = $peReader.GetMetadataReader()
    $reader = $metadataProvider.GetMetadataReader()

    Write-Host "Metadata loaded successfully!" -ForegroundColor Green
    Write-Host "Assembly: $($reader.GetAssemblyDefinition().Name)" -ForegroundColor White

    # Get string heap for string literals
    $stringHeap = $reader.GetBlobReader()

    # Collect method information
    $methods = @()
    $typeMap = @{}

    Write-Host "`nScanning types..." -ForegroundColor Yellow

    $typeDefs = $reader.GetTypeDefinitions()
    $typeCount = 0
    $methodCount = 0

    foreach ($typeHandle in $typeDefs) {
        $typeDef = $reader.GetTypeDefinition($typeHandle)
        $namespace = $reader.GetString($typeDef.Namespace)
        $typeName = $reader.GetString($typeDef.Name)

        if ($typeName -match "^(Beam|Dam|Cot|Vach|San|Mong|Thang|Excel|GanDL|XData|RegApp|VeDam|VeCot|Quet|SuaCK|GanLien)" -or
            $namespace -match "Excel|GanDL|XData|DCE" -or
            $typeName -match "Excel|GanDL|XData") {

            $typeFullName = "$namespace.$typeName"
            $typeMap[$typeHandle.Value] = $typeFullName

            # Get methods for this type
            $methodHandles = $typeDef.GetMethods()
            foreach ($methodHandle in $methodHandles) {
                $methodDef = $reader.GetMethodDefinition($methodHandle)
                $methodName = $reader.GetString($methodDef.Name)

                $methodCount++

                # Try to get IL body
                if ($methodDef.RelativeVirtualAddress -ne 0) {
                    try {
                        $ilBytes = $peReader.GetMethodBody($methodDef.RelativeVirtualAddress)
                        if ($ilBytes) {
                            $methodInfo = @{
                                TypeName = $typeFullName
                                MethodName = $methodName
                                RVA = $methodDef.RelativeVirtualAddress
                                ILSize = $ilBytes.IL.Length
                                MaxStack = $ilBytes.MaxStack
                                LocalVariables = $ilBytes.LocalVariables.Count
                                HasExceptionHandlers = $ilBytes.HasExceptionHandlers
                                Strings = @()
                                Calls = @()
                                Fields = @()
                            }

                            # Analyze IL
                            $il = $ilBytes.IL
                            $pos = 0
                            while ($pos -lt $il.Length) {
                                $opcode = $il[$pos]
                                $opName = switch($opcode) {
                                    0x72 { "ldstr" }
                                    0x6F { "call" }
                                    0x28 { "call" }
                                    0x7E { "ldsfld" }
                                    0x7B { "ldfld" }
                                    0x73 { "ret" }
                                    0x20 { "ldc.i4" }
                                    0x21 { "ldc.i4.s" }
                                    0x22 { "ldc.i4" }
                                    0x02 { "ldarg.0" }
                                    0x03 { "ldarg.1" }
                                    0x06 { "ldloc.0" }
                                    0x0A { "stloc.0" }
                                    default { "other" }
                                }

                                # ldstr - load string literal
                                if ($opcode -eq 0x72 -or $opcode -eq 0x0D) {
                                    if ($pos + 4 -lt $il.Length) {
                                        $token = [BitConverter]::ToInt32($il, $pos + 1)
                                        $strHandle = [System.Reflection.Metadata.HandleKind]::UserString -shl 24 -bor ($token -band 0x00FFFFFF)
                                        try {
                                            $str = $reader.GetUserString([int]$token)
                                            if ($str) {
                                                $methodInfo.Strings += $str
                                            }
                                        } catch {}
                                    }
                                }

                                # call - method call
                                if ($opcode -eq 0x6F -or $opcode -eq 0x28) {
                                    if ($pos + 4 -lt $il.Length) {
                                        $token = [BitConverter]::ToInt32($il, $pos + 1)
                                        $methodInfo.Calls += "token_0x$($token.ToString('X8'))"
                                    }
                                }

                                # ldsfld - static field
                                if ($opcode -eq 0x7E) {
                                    if ($pos + 4 -lt $il.Length) {
                                        $token = [BitConverter]::ToInt32($il, $pos + 1)
                                        $methodInfo.Fields += "token_0x$($token.ToString('X8'))"
                                    }
                                }

                                # ldfld - instance field
                                if ($opcode -eq 0x7B) {
                                    if ($pos + 4 -lt $il.Length) {
                                        $token = [BitConverter]::ToInt32($il, $pos + 1)
                                        $methodInfo.Fields += "token_0x$($token.ToString('X8'))"
                                    }
                                }

                                # Skip operand bytes
                                if ($opcode -ge 0x20 -and $opcode -le 0x27) { $pos += 4 }
                                elseif ($opcode -ge 0x38 -and $opcode -le 0x3F) { $pos += 4 }
                                elseif ($opcode -ge 0x40 -and $opcode -le 0x50) { $pos += 4 }
                                elseif ($opcode -eq 0x51) {
                                    if ($pos + 4 -lt $il.Length) {
                                        $count = [BitConverter]::ToInt32($il, $pos + 1)
                                        $pos += 4 + ($count * 4)
                                        continue
                                    }
                                }
                                elseif ($opcode -eq 0xFE) { $pos += 2 }
                                else { $pos++ }

                                if ($opcode -ne 0xFE) { $pos++ }
                            }

                            if ($methodInfo.Strings.Count -gt 0 -or $methodInfo.Calls.Count -gt 0) {
                                $methods += $methodInfo
                            }
                        }
                    } catch {
                        # Method body access failed - skip
                    }
                }
            }
        }

        $typeCount++
    }

    Write-Host "Types scanned: $typeCount" -ForegroundColor Gray
    Write-Host "Methods with code: $methodCount" -ForegroundColor Gray
    Write-Host "Methods with data: $($methods.Count)" -ForegroundColor Cyan

    # Aggregate strings
    $allStrings = @{}
    $excelPatterns = @()
    $cellRefs = @()
    $regAppNames = @()

    foreach ($m in $methods) {
        foreach ($s in $m.Strings) {
            if ($s -and $s.Length -gt 0 -and $s.Length -lt 200) {
                $allStrings[$s] = $true

                # Pattern matching
                if ($s -match "^[A-Z]{1,3}\d+$") { $cellRefs += $s }
                if ($s -match "^[A-Z]{1,3}\d+:[A-Z]{1,3}\d+$") { $cellRefs += $s }
                if ($s -match "^(Sheet|DATA|Beam|Column|Slab|Design|Tong|Hop)") { $excelPatterns += $s }
                if ($s -match "^[A-Z][A-Z0-9_]{2,16}$") { $regAppNames += $s }
            }
        }
    }

    # Create output
    $output = @{
        metadata = @{
            timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
            dll_path = $DllPath
            dll_size = (Get-Item $DllPath).Length
            total_strings = $allStrings.Keys.Count
            total_methods_analyzed = $methods.Count
        }
        excel_bus = @{
            sheet_patterns = $excelPatterns | Sort-Object -Unique
            cell_references = $cellRefs | Sort-Object -Unique
        }
        xdata_protocol = @{
            regapp_candidates = ($regAppNames | Sort-Object -Unique | Where-Object { $_ -notmatch "^[A-Z]{3,}$" })
        }
        method_samples = @()
        string_samples = @()
    }

    # Add sample methods
    $sampleMethods = $methods | Where-Object { $_.Strings.Count -gt 3 } | Select-Object -First 50
    foreach ($m in $sampleMethods) {
        $output.method_samples += @{
            type = $m.TypeName
            method = $m.MethodName
            strings = $m.Strings
            il_size = $m.ILSize
        }
    }

    # Add sample strings
    $output.string_samples = ($allStrings.Keys | Where-Object {
        $_.Length -gt 3 -and $_.Length -lt 100 -and $_ -notmatch "^[\x00-\x1F]+$"
    } | Select-Object -First 200)

    # Save JSON
    $outputPath = Join-Path $OutputDir "DCE_DEEP_OPERATION_SCHEMA.json"
    $output | ConvertTo-Json -Depth 10 | Out-File -FilePath $outputPath -Encoding UTF8

    Write-Host "`nSaved: $outputPath" -ForegroundColor Green

    # Print summary
    Write-Host "`n--- SUMMARY ---" -ForegroundColor Yellow
    Write-Host "Total strings: $($allStrings.Keys.Count)"
    Write-Host "Excel patterns: $($excelPatterns.Count)"
    Write-Host "Cell refs: $($cellRefs.Count)"

    if ($excelPatterns.Count -gt 0) {
        Write-Host "`nExcel Sheet Names:" -ForegroundColor Cyan
        $excelPatterns | Select-Object -First 20 | ForEach-Object { Write-Host "  $_" }
    }

    if ($cellRefs.Count -gt 0) {
        Write-Host "`nCell References (sample):" -ForegroundColor Cyan
        $cellRefs | Select-Object -First 30 | Sort-Object | ForEach-Object { Write-Host "  $_" }
    }

    $peStream.Close()

} catch {
    Write-Host "`nERROR: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
}

Write-Host "`nDone!" -ForegroundColor Green
