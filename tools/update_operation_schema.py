# update_operation_schema.py
import sys
import json
import re
from datetime import datetime
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

AGENTS_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = AGENTS_ROOT / "docs"
SCHEMA_PATH = DOCS_DIR / "DCE_DEEP_OPERATION_SCHEMA.json"
IL_STRINGS_PATH = DOCS_DIR / "DCE_IL_EXTRACTED_STRINGS.json"


def update_operation_schema() -> int:
    if not SCHEMA_PATH.exists():
        print(f"[!] Schema file not found: {SCHEMA_PATH}")
        return 1
    if not IL_STRINGS_PATH.exists():
        print(f"[!] IL strings file not found: {IL_STRINGS_PATH}")
        return 1

    print(f"[*] Reading current schema: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    print(f"[*] Reading extracted IL strings: {IL_STRINGS_PATH}")
    with open(IL_STRINGS_PATH, "r", encoding="utf-8-sig") as f:
        il_data = json.load(f)

    # Collect categorized methods and strings
    etabs_sap_methods = {}
    cad_steel_methods = {}
    config_license_methods = {}
    security_runtime_methods = {}
    all_referenced_files = set()
    all_purlin_profiles = set()
    design_codes = set()
    csi_progids = set()

    for asm_name, asm_data in il_data["assemblies"].items():
        for method_key, strings in asm_data["methods"].items():
            clean_strings = [s.strip() for s in strings if s and s.strip()]
            if not clean_strings:
                continue
            
            # Track referenced files
            for s in clean_strings:
                if re.search(r'(\.txt|\.xlsm|\.xlsx|\.db|\.dwg|\.dxf|C:\\Dce Pro\\)', s, re.I):
                    all_referenced_files.add(s)
                if re.search(r'^(C\d{3}|Z\d{3})$', s):
                    all_purlin_profiles.add(s)
                if re.search(r'(AISC|SP 16|IBC)', s):
                    design_codes.add(s)
                if re.search(r'CSI\.(ETABS|SAP2000|SAFE)\.API', s):
                    csi_progids.add(s)
                    
            # Categorize methods
            if any(k in method_key for k in ["DceEtabs", "CSIMenuDefineMat", "PubSub", "APICSISofware"]):
                etabs_sap_methods[f"[{asm_name}] {method_key}"] = clean_strings
            elif any(k in method_key for k in ["DceCad", "Connection", "DceMath", "CalVolumne", "ExMarshal"]):
                cad_steel_methods[f"[{asm_name}] {method_key}"] = clean_strings
            elif any(k in method_key for k in ["CheckLicense", "KhoiDong", "CheckDownload", "Loai_Ky_Tu"]):
                config_license_methods[f"[{asm_name}] {method_key}"] = clean_strings
            elif any(k in method_key for k in ["zCRRx", "EDeSZ", "VSTUp", "CUnl2", "llKsp", "svH7s"]):
                security_runtime_methods[f"[{asm_name}] {method_key}"] = clean_strings

    print(f"  -> Extracted categories:")
    print(f"     ETABS/SAP methods: {len(etabs_sap_methods)}")
    print(f"     CAD/Steel methods: {len(cad_steel_methods)}")
    print(f"     Config/License methods: {len(config_license_methods)}")
    print(f"     Security/Runtime methods: {len(security_runtime_methods)}")
    print(f"     Referenced files in IL: {len(all_referenced_files)}")
    print(f"     Purlin profiles in IL: {len(all_purlin_profiles)}")
    print(f"     Design codes in IL: {len(design_codes)}")

    # Update Schema
    schema["metadata"]["generated_at"] = datetime.now().isoformat(timespec="seconds")
    schema["metadata"]["version"] = "4.0.0"
    schema["metadata"]["description"] = "DCE Pro Deep IL Bytecode Opcode 0x72 (ldstr) + Token ResolveString & Method-Level Operation Schema"
    schema["metadata"]["sources"] = [
        "C:\\Dce Pro\\DCE Pro.dll",
        "C:\\Dce Pro\\AddinSteelCad\\DbimSteelAutocad-ToanHuynh-2.dll",
        "C:\\Dce Pro\\AddinSteelCad\\DbimSteelAutocad.dll",
        "C:\\Dce Pro\\AddinSteel\\DceSteel-DESKTOP-BT5QG2E.dll",
        "C:\\Dce Pro\\AddinSteel\\DceSteel.dll",
        "C:\\Dce Pro\\V.2020\\DCE Excel.dll",
        "C:\\Dce Pro\\BcDCE Pro.dll",
        "C:\\Dce Pro\\ZwDCE Pro.dll",
        "C:\\Dce Pro\\GcDCE Pro.dll",
        "C:\\Dce Pro\\IcDCE Pro.dll"
    ]
    schema["metadata"]["total_methods_with_ldstr"] = il_data["grand_total_methods_with_ldstr"]
    schema["metadata"]["total_strings_scanned"] = il_data["grand_total_ldstr_strings"]
    schema["metadata"]["analysis_method"] = "[System.Reflection.Assembly]::ReflectionOnlyLoadFrom($dllPath) + $method.GetMethodBody().GetILAsByteArray() at opcode 0x72 (ldstr) with $module.ResolveString($token)"

    # Enrich CAD Integration
    if "purlin_profiles" not in schema["cad_integration"]:
        schema["cad_integration"]["purlin_profiles"] = sorted(list(all_purlin_profiles))
    else:
        schema["cad_integration"]["purlin_profiles"] = sorted(list(set(schema["cad_integration"]["purlin_profiles"]) | all_purlin_profiles))

    schema["cad_integration"]["internal_configs_referenced"] = sorted(list(all_referenced_files))

    # Add ETABS API Integration section
    schema["etabs_api_integration"] = {
        "supported_csi_progids": sorted(list(csi_progids)),
        "supported_design_codes": sorted(list(design_codes)),
        "startup_configs": [
            "C:\\Dce Pro\\System\\KhoiDongEtabs.txt",
            "C:\\Dce Pro\\System\\KhoiDongEtabs2.txt"
        ],
        "csi_registration_procedure": {
            "etabs": "C:\\Program Files\\Computers and Structures\\ETABS... => RegisterETABS.exe (Run as administrator)",
            "sap2000": "C:\\Program Files\\Computers and Structures\\SAP2000... => RegisterSAP2000.exe (Run as administrator)"
        },
        "key_oapi_methods_mapped": [
            "DbimSteelAutocad.DceEtabs::PublicSetup",
            "DbimSteelAutocad.DceEtabs::UnbracedLengthRatioMajor",
            "DbimSteelAutocad.DceEtabs::UnbracedLengthRatioMinor",
            "DbimSteelAutocad.DceEtabs::UnbracedLengthRatioLateralTorsionalBuckling",
            "DceSteel.DceEtabs::PointObjSetLoadForceValue",
            "DceSteel.DceEtabs::PropFrameSectI_Total",
            "DceSteel.DceEtabs::PropFrameSectI_Web",
            "DceSteel.DceEtabs::DefineFrameSectSteel",
            "DceSteel.DceEtabs::RoofObjAddByCoordTop",
            "DceSteel.DceEtabs::RoofObjAddByCoordBot",
            "DceSteel.DceEtabs::FrameObjGetLength"
        ]
    }

    # Add Method String Constants
    schema["method_string_constants"] = {
        "summary": {
            "total_assemblies": il_data["total_assemblies_scanned"],
            "total_methods_with_ldstr": il_data["grand_total_methods_with_ldstr"],
            "total_ldstr_resolved": il_data["grand_total_ldstr_strings"]
        },
        "etabs_sap_methods": etabs_sap_methods,
        "cad_steel_methods": cad_steel_methods,
        "config_license_methods": config_license_methods,
        "security_runtime_methods": security_runtime_methods
    }

    # Update High Confidence Findings
    schema["high_confidence_findings"].append({
        "type": "exact_method_ldstr_constants",
        "value": f"{il_data['grand_total_ldstr_strings']} strings across {il_data['grand_total_methods_with_ldstr']} methods in 10 assemblies",
        "confidence": "VERIFIED_100%",
        "evidence": "Extracted via [System.Reflection.Assembly]::ReflectionOnlyLoadFrom($dllPath) + $method.GetMethodBody().GetILAsByteArray() at opcode 0x72 (ldstr) and $module.ResolveString($token)"
    })
    schema["high_confidence_findings"].append({
        "type": "etabs_progids_and_standards",
        "value": "CSI.ETABS.API.ETABSObject, CSI.SAP2000.API.SapObject; AISC 360-05..22, SP 16.13330.2011/2017",
        "confidence": "VERIFIED_100%",
        "evidence": "Resolved from DceEtabs::PublicSetup, UnbracedLengthRatioMajor, UnbracedLengthRatioMinor in DceSteel.dll & DbimSteelAutocad.dll"
    })

    with open(SCHEMA_PATH, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)

    print(f"[OK] Successfully updated: {SCHEMA_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(update_operation_schema())

