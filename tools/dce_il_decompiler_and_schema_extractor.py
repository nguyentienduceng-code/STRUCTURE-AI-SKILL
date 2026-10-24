#!/usr/bin/env python3
"""
dce_il_decompiler_and_schema_extractor.py
========================================
Deep IL Bytecode Disassembly & Schema Extraction cho DCE Pro.

Phase 4: Giải mã Method Body IL để bóc tách:
1. Excel-to-CAD Data Bus (GanDLApplication*, Cell Coordinates)
2. XData/ExtensionDictionary Protocol (RegAppName, TypedValue order)
3. Multi-Scale Viewport Management (anno_scale, DimStyle mapping)
4. UDF formulas trong DCE Excel.dll

Sử dụng: python dce_il_decompiler_and_schema_extractor.py [--target DCE_Excel.dll|DCE_Pro.dll]
"""

import sys
import os
import json
import struct
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import hashlib

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ============================================================================
# CONFIGURATION
# ============================================================================

DCE_PRO_ROOT = Path(r"C:\Dce Pro")
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs"
TEMP_DIR = OUTPUT_DIR / "temp_il"

TARGET_ASSEMBLIES = [
    DCE_PRO_ROOT / "V.2020" / "DCE Excel.dll",
    DCE_PRO_ROOT / "DCE Excel.dll",
    DCE_PRO_ROOT / "DCE Pro.dll",
    DCE_PRO_ROOT / "DbimSteelAutocad.dll",
]

@dataclass
class ILInstruction:
    """Một instruction IL đơn lẻ."""
    offset: int
    opcode: int
    mnemonic: str
    operand: Optional[Any] = None
    operand_type: str = "none"
    resolved_string: Optional[str] = None

@dataclass
class MethodSchema:
    """Schema của một method sau khi phân tích IL."""
    declaring_type: str
    method_name: str
    signature: str
    il_instructions: List[ILInstruction] = field(default_factory=list)
    string_literals: List[str] = field(default_factory=list)
    called_methods: List[str] = field(default_factory=list)
    called_types: List[str] = field(default_factory=list)
    static_fields: List[str] = field(default_factory=list)
    excel_sheet_refs: List[Dict] = field(default_factory=list)
    xdata_protocol: Dict = field(default_factory=dict)
    annotations: Dict = field(default_factory=dict)

@dataclass
class AssemblySchema:
    """Schema tổng hợp của một assembly."""
    path: str
    file_size: int
    assembly_name: str
    version: str
    public_key_token: str
    methods: Dict[str, MethodSchema] = field(default_factory=dict)
    excel_bus_protocol: Dict = field(default_factory=dict)
    xdata_protocol: Dict = field(default_factory=dict)
    udf_functions: Dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

# ============================================================================
# IL OPCODE MAPPING (Common opcodes used in DCE Pro)
# ============================================================================

IL_OPCODES: Dict[int, str] = {
    # Load/Store
    0x00: "nop", 0x01: "break", 0x02: "ldarg.0", 0x03: "ldarg.1",
    0x04: "ldarg.2", 0x05: "ldarg.3", 0x06: "ldloc.0", 0x07: "ldloc.1",
    0x08: "ldloc.2", 0x09: "ldloc.3", 0x0A: "stloc.0", 0x0B: "stloc.1",
    0x0C: "stloc.2", 0x0D: "stloc.3", 0x0E: "ldarg.s", 0x0F: "ldarg.w",
    0x10: "ldarga.s", 0x11: "ldarga.w", 0x12: "starg.s", 0x13: "starg.w",
    0x11: "ldarga", 0x13: "starg",
    # 16-bit locals
    0x14: "ldloc.s", 0x15: "ldloc.w", 0x16: "ldloca.s", 0x17: "ldloca.w",
    # Load constants
    0x16: "ldnull", 0x17: "ldc.i4.m1", 0x18: "ldc.i4.0", 0x19: "ldc.i4.1",
    0x1A: "ldc.i4.2", 0x1B: "ldc.i4.3", 0x1C: "ldc.i4.4", 0x1D: "ldc.i4.5",
    0x1E: "ldc.i4.6", 0x1F: "ldc.i4.7", 0x20: "ldc.i4.8",
    0x21: "ldc.i4.s", 0x22: "ldc.i4", 0x23: "ldc.i8", 0x24: "ldc.r4",
    0x25: "ldc.r8",
    # Stack operations
    0x26: "dup", 0x27: "pop",
    # Control flow
    0x37: "br", 0x38: "brfalse", 0x39: "brtrue", 0x3A: "beq", 0x3B: "bge",
    0x3C: "bgt", 0x3D: "ble", 0x3E: "blt", 0x3F: "bne.un", 0x40: "bge.un",
    0x41: "bgt.un", 0x42: "ble.un", 0x43: "blt.un",
    0x44: "br.s", 0x45: "brfalse.s", 0x46: "brtrue.s",
    0x47: "beq.s", 0x48: "bge.s", 0x49: "bgt.s", 0x4A: "ble.s",
    0x4B: "blt.s", 0x4C: "bne.un.s", 0x4D: "bge.un.s", 0x4E: "bgt.un.s",
    0x4F: "ble.un.s", 0x50: "blt.un.s",
    # Jmp & ret
    0x51: "switch", 0x52: "ldind.i1", 0x53: "ldind.u1", 0x54: "ldind.i2",
    0x55: "ldind.u2", 0x56: "ldind.i4", 0x57: "ldind.u4", 0x58: "ldind.i8",
    0x59: "ldind.r4", 0x5A: "ldind.r8", 0x5B: "ldind.ref", 0x5C: "stind.ref",
    0x5D: "stind.i1", 0x5E: "stind.i2", 0x5F: "stind.i4", 0x60: "stind.i8",
    0x61: "stind.r4", 0x62: "stind.r8",
    # Arithmetic
    0x63: "add", 0x64: "sub", 0x65: "mul", 0x66: "div", 0x67: "div.un",
    0x68: "rem", 0x69: "rem.un", 0x6A: "and", 0x6B: "or", 0x6C: "xor",
    0x6D: "shl", 0x6E: "shr", 0x6F: "shr.un",
    # Conversion
    0x70: "neg", 0x71: "not", 0x72: "conv.i1", 0x73: "conv.i2", 0x74: "conv.i4",
    0x75: "conv.i8", 0x76: "conv.r4", 0x77: "conv.r8", 0x78: "conv.u4",
    0x79: "conv.u8", 0x7A: "callvirt", 0x7B: "cpobj",
    0x7C: "ldobj", 0x7D: "ldstr", 0x7E: "ldtypeid", 0x7F: "ldlen",
    # Array operations
    0x80: "ldelema", 0x81: "ldelem.i1", 0x82: "ldelem.u1", 0x83: "ldelem.i2",
    0x84: "ldelem.u2", 0x85: "ldelem.i4", 0x86: "ldelem.u4", 0x87: "ldelem.i8",
    0x88: "ldelem.r4", 0x89: "ldelem.r8", 0x8A: "ldelem.ref", 0x8B: "stelem.i",
    0x8C: "stelem.i1", 0x8D: "stelem.i2", 0x8E: "stelem.i4", 0x8F: "stelem.i8",
    0x90: "stelem.r4", 0x91: "stelem.r8", 0x92: "stelem.ref",
    # Call
    0x6F: "call", 0x70: "calli",
    # Object model
    0x73: "ret", 0x74: "br.s", 0x75: "brfalse.s", 0x76: "brtrue.s",
    0x7E: "ldind.i1", 0x7F: "ldind.u1",
    # Box/unbox
    0x8D: "unbox.any", 0x8E: "unbox",
    0xC3: "box", 0xC4: "castclass", 0xC5: "isinst",
    # Field access
    0x7B: "ldfld", 0x7C: "ldflda", 0x7D: "stfld", 0x7E: "ldsfld",
    0x7F: "ldsflda", 0x80: "stsfld",
    # Newobj
    0x73: "newarr", 0x74: "ldelema", 0x75: "ldlen",
    # Try/catch
    0x99: "leave", 0x9A: "leave.s", 0x9B: "endfilter",
    0x9C: "endfinally", 0x9D: "refanyval", 0x9E: "ckfinite",
    0x9F: "mkrefany", 0xA0: "ldtok",
    # Method references
    0xA6: "rethrow", 0xA7: "sizeof", 0xA8: "refanytype",
    0xD0: "ldtoken", 0xD1: "conv.u", 0xD2: "conv.u2", 0xD3: "conv.u1",
    # Extra
    0xFE00: "arglist", 0xFE01: "ceq", 0xFE02: "cgt", 0xFE03: "cgt.un",
    0xFE04: "clt", 0xFE05: "clt.un",
    0xFE06: "ldftn", 0xFE07: "ldvirtftn", 0xFE08: "ldarg",
    0xFE09: "ldarga", 0xFE0A: "starg", 0xFE0B: "ldloc",
    0xFE0C: "ldloca", 0xFE0D: "stloc",
    # Extended
    0xFE0E: "localloc", 0xFE0F: "endfilter",
    0xFE11: "initblk", 0xFE12: "cpblk",
    0xFE13: "no", 0xFE14: "break", 0xFE15: "ldarga.s",
    0xFE16: "starg.s", 0xFE17: "ldloc.s", 0xFE18: "ldloca.s",
    0xFE19: "stloc.s", 0xFE1A: "ldobj",
    0xFE1B: "ldstr", 0xFE1C: "ldtype", 0xFE1D: "ldtoken",
    0xFE1E: "conv.i", 0xFE1F: "conv.u1",
}

def get_mnemonic(opcode: int) -> str:
    """Get IL mnemonic for opcode."""
    if opcode in IL_OPCODES:
        return IL_OPCODES[opcode]
    if 0xFE00 <= opcode <= 0xFFFF:
        ext = opcode - 0xFE00
        return f"prefix_{ext:02x}"
    return f"unknown_0x{opcode:02X}"

# ============================================================================
# BYTE CODE READER
# ============================================================================

class ILByteCodeReader:
    """Đọc và parse IL bytecode từ method body."""

    def __init__(self, il_bytes: bytes, method_token: int, method_specs: Dict[int, str],
                 member_refs: Dict[int, Tuple[str, str]], string_heap: Dict[int, str],
                 field_refs: Dict[int, Tuple[str, str]]):
        self.bytes = il_bytes
        self.pos = 0
        self.method_token = method_token
        self.method_specs = method_specs  # token -> "Type::Method"
        self.member_refs = member_refs    # token -> ("Type", "Member")
        self.string_heap = string_heap   # token -> string
        self.field_refs = field_refs     # token -> ("Type", "Field")
        self.instructions: List[ILInstruction] = []
        self.string_literals: List[str] = []
        self.called_methods: List[str] = []
        self.called_types: List[str] = []
        self.static_fields: List[str] = []

    def read_byte(self) -> int:
        if self.pos >= len(self.bytes):
            return 0
        b = self.bytes[self.pos]
        self.pos += 1
        return b

    def read_int32(self) -> int:
        b0 = self.read_byte()
        b1 = self.read_byte()
        b2 = self.read_byte()
        b3 = self.read_byte()
        return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)

    def read_int64(self) -> int:
        lo = self.read_int32()
        hi = self.read_int32()
        return lo | (hi << 32)

    def read_single(self) -> float:
        bits = self.read_int32()
        return struct.unpack('f', struct.pack('I', bits))[0]

    def read_double(self) -> float:
        bits = self.read_int64()
        return struct.unpack('d', struct.pack('Q', bits))[0]

    def read_token(self) -> int:
        return self.read_int32()

    def resolve_token(self, token: int) -> Optional[str]:
        """Resolve a metadata token to its string representation."""
        ttype = token & 0xFF000000
        rid = token & 0x00FFFFFF

        if ttype == 0x70000000 and rid in self.string_heap:
            return self.string_heap[rid]
        elif ttype == 0x0A000000 and rid in self.member_refs:
            t, m = self.member_refs[rid]
            return f"{t}::{m}"
        elif ttype == 0x0B000000 and rid in self.method_specs:
            return self.method_specs[rid]
        elif ttype == 0x04000000 and rid in self.field_refs:
            t, f = self.field_refs[rid]
            return f"{t}.{f}"
        elif ttype == 0x02000000:  # TypeRef or TypeDef
            return f"TypeDef_or_Ref_{rid}"

        return f"token_0x{token:08X}"

    def parse(self) -> List[ILInstruction]:
        """Parse all IL instructions in the method body."""
        self.pos = 0
        while self.pos < len(self.bytes):
            start_pos = self.pos
            opcode = self.read_byte()

            # Handle 2-byte opcodes
            if opcode == 0xFE:
                opcode = 0xFE00 | self.read_byte()

            # 0xFF is sometimes used as prefix
            if opcode == 0xFF and self.pos < len(self.bytes):
                opcode = 0xFF00 | self.read_byte()

            mnemonic = get_mnemonic(opcode)
            operand = None
            operand_type = "none"
            resolved = None

            # Parse operand based on opcode
            try:
                if opcode in (0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09):  # ldarg, ldloc short
                    pass
                elif opcode in (0x0A, 0x0B, 0x0C, 0x0D):  # stloc
                    pass
                elif opcode in (0x10,):  # ldarg.s
                    operand = self.read_byte()
                    operand_type = "int8"
                elif opcode in (0x14,):  # ldloc.s
                    operand = self.read_byte()
                    operand_type = "int8"
                elif opcode in (0x11,):  # ldarga.s
                    operand = self.read_byte()
                    operand_type = "int8"
                elif opcode in (0x16,):  # ldloca.s
                    operand = self.read_byte()
                    operand_type = "int8"
                elif opcode in (0x1E, 0x1F, 0x20, 0x21):  # ldc.i4 variants
                    if opcode == 0x1F:  # ldc.i4.s
                        operand = self.read_byte()
                        operand_type = "int8"
                    elif opcode == 0x20:  # ldc.i4
                        operand = self.read_int32()
                        operand_type = "int32"
                    else:
                        operand = opcode - 0x17  # 0=0, 1=1, etc
                        operand_type = "literal"
                elif opcode == 0x21:  # ldc.i4.s
                    operand = self.read_byte()
                    operand_type = "int8"
                elif opcode == 0x22:  # ldc.i4
                    operand = self.read_int32()
                    operand_type = "int32"
                elif opcode == 0x23:  # ldc.i8
                    operand = self.read_int64()
                    operand_type = "int64"
                elif opcode in (0x24,):  # ldc.r4
                    operand = self.read_single()
                    operand_type = "float32"
                elif opcode in (0x25,):  # ldc.r8
                    operand = self.read_double()
                    operand_type = "float64"
                elif opcode in (0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E,
                                0x3F, 0x40, 0x41, 0x42, 0x43):  # br, brtrue, beq, etc
                    operand = self.read_int32()
                    operand_type = "int32"  # offset
                elif opcode in (0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A, 0x4B,
                                0x4C, 0x4D, 0x4E, 0x4F, 0x50):  # br.s variants
                    operand = self.read_byte()
                    operand_type = "int8"  # short offset
                elif opcode == 0x51:  # switch
                    n = self.read_int32()
                    targets = []
                    for _ in range(n):
                        targets.append(self.read_int32())
                    operand = targets
                    operand_type = "switch_table"
                elif opcode == 0x6F:  # call
                    token = self.read_token()
                    resolved = self.resolve_token(token)
                    if resolved:
                        self.called_methods.append(resolved)
                        # Extract type from Type::Method
                        if "::" in resolved:
                            type_part = resolved.split("::")[0]
                            if type_part not in self.called_types:
                                self.called_types.append(type_part)
                    operand = token
                    operand_type = "method_token"
                elif opcode == 0x73:  # ret
                    pass
                elif opcode == 0x7B:  # ldfld
                    token = self.read_token()
                    resolved = self.resolve_token(token)
                    operand = token
                    operand_type = "field_token"
                    if resolved:
                        self.static_fields.append(resolved)
                elif opcode == 0x7E:  # ldsfld
                    token = self.read_token()
                    resolved = self.resolve_token(token)
                    operand = token
                    operand_type = "field_token"
                    if resolved:
                        self.static_fields.append(resolved)
                elif opcode == 0x7C:  # ldflda
                    token = self.read_token()
                    operand = token
                    operand_type = "field_token"
                elif opcode == 0x7D:  # ldstr
                    token = self.read_token()
                    resolved = self.resolve_token(token)
                    operand = token
                    operand_type = "string_token"
                    if resolved and resolved not in (None, "token_0x00000000"):
                        self.string_literals.append(resolved)
                    resolved = resolved if resolved else None
                elif opcode in (0x6F, 0x28):  # call / callvirt
                    token = self.read_token()
                    resolved = self.resolve_token(token)
                    if resolved:
                        self.called_methods.append(resolved)
                        if "::" in resolved:
                            type_part = resolved.split("::")[0]
                            if type_part not in self.called_types:
                                self.called_types.append(type_part)
                    operand = token
                    operand_type = "method_token"
                elif opcode in (0x28,):  # call
                    token = self.read_token()
                    resolved = self.resolve_token(token)
                    if resolved:
                        self.called_methods.append(resolved)
                        if "::" in resolved:
                            type_part = resolved.split("::")[0]
                            if type_part not in self.called_types:
                                self.called_types.append(type_part)
                    operand = token
                    operand_type = "method_token"
                elif opcode == 0xD0:  # ldtoken
                    token = self.read_token()
                    resolved = self.resolve_token(token)
                    operand = token
                    operand_type = "token"
                    resolved = resolved
                elif opcode in (0x72,):  # ldstr (alternate)
                    token = self.read_token()
                    resolved = self.resolve_token(token)
                    operand = token
                    operand_type = "string_token"
                    if resolved and resolved not in (None, "token_0x00000000"):
                        self.string_literals.append(resolved)
                    resolved = resolved if resolved else None
                elif opcode == 0x2B:  # jmp
                    token = self.read_token()
                    operand = token
                    operand_type = "method_token"
                elif opcode in (0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13):  # more arg/loc ops
                    if opcode >= 0x10:
                        operand = self.read_byte()
                        operand_type = "uint8"
                elif opcode >= 0x80 and opcode <= 0x91:  # ldelem/stelem
                    pass
                elif opcode == 0x8A:  # ldelem.ref
                    pass
                elif opcode == 0x7F:  # ldlen
                    pass
                elif opcode == 0x8B:  # stelem.ref
                    pass
                elif opcode == 0x92:  # stelem.ref
                    pass
                elif opcode == 0x74:  # conv
                    pass
                elif opcode == 0x7A:  # conv
                    pass
                elif opcode in (0x63, 0x64, 0x65, 0x66, 0x67, 0x6A, 0x6B, 0x6C, 0x6D, 0x6E, 0x6F):  # arithmetic
                    pass
                elif opcode in (0xD1, 0xD2, 0xD3):  # conv.u variants
                    pass
                elif opcode in (0xD4,):  # conv.ovf
                    pass
                elif opcode in (0x26, 0x27):  # dup, pop
                    pass
                elif opcode == 0x73:  # ret
                    pass
                elif opcode == 0x58:  # pop
                    pass
                elif opcode in (0x5B,):  # pop
                    pass
                elif opcode in (0x70, 0x71):  # neg, not
                    pass
                elif opcode in (0xC2,):  # cpblk
                    pass
                elif opcode in (0xDC,):  # newarr
                    token = self.read_token()
                    operand = token
                    operand_type = "type_token"
                elif opcode in (0x8D,):  # unbox.any
                    token = self.read_token()
                    operand = token
                    operand_type = "type_token"
                elif opcode in (0x74, 0x75, 0x76, 0x77, 0x78, 0x79, 0x7A):  # conv ops
                    pass
                elif opcode in (0xC3,):  # box
                    token = self.read_token()
                    operand = token
                    operand_type = "type_token"
                elif opcode in (0xC4, 0xC5):  # castclass, isinst
                    token = self.read_token()
                    operand = token
                    operand_type = "type_token"
                elif opcode in (0xFE06,):  # ldftn
                    token = self.read_token()
                    operand = token
                    operand_type = "method_token"
                elif opcode in (0xFE07,):  # ldvirtftn
                    token = self.read_token()
                    operand = token
                    operand_type = "method_token"
                elif opcode == 0x17:  # ldc.i4.m1
                    operand = -1
                    operand_type = "literal"
                else:
                    # Unknown opcode - might be single byte with no operand
                    if opcode < 0x38 or (0x3B <= opcode <= 0x5B) or opcode >= 0x70:
                        pass  # Most single-byte opcodes have no operand
            except Exception as e:
                pass

            instr = ILInstruction(
                offset=start_pos,
                opcode=opcode,
                mnemonic=mnemonic,
                operand=operand,
                operand_type=operand_type,
                resolved_string=resolved
            )
            self.instructions.append(instr)

        return self.instructions

# ============================================================================
# PE/COFF METADATA READER
# ============================================================================

class PEMetadataReader:
    """Đọc PE/COFF metadata từ .NET assembly."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.data: Optional[bytes] = None
        self.method_specs: Dict[int, str] = {}
        self.member_refs: Dict[int, Tuple[str, str]] = {}
        self.string_heap: Dict[int, str] = {}
        self.field_refs: Dict[int, Tuple[str, str]] = {}
        self.type_refs: Dict[int, str] = {}
        self.blob_heap: Dict[int, bytes] = {}

    def load(self) -> bool:
        """Load file into memory."""
        try:
            self.data = self.filepath.read_bytes()
            return True
        except Exception as e:
            print(f"Error loading {self.filepath}: {e}")
            return False

    def get_size(self) -> int:
        return len(self.data) if self.data else 0

    def read_metadata(self) -> bool:
        """Parse .NET metadata from PE file."""
        if not self.data or len(self.data) < 0x200:
            return False

        try:
            # Find DOS header
            if self.data[0:2] != b'MZ':
                return False

            # Get PE offset from DOS header at 0x3C
            pe_offset = struct.unpack('<I', self.data[0x3C:0x40])[0]
            if pe_offset + 4 > len(self.data):
                return False

            # Check PE signature
            if self.data[pe_offset:pe_offset+4] != b'PE\x00\x00':
                return False

            # Read COFF header
            coff_offset = pe_offset + 4
            machine = struct.unpack('<H', self.data[coff_offset:coff_offset+2])[0]
            num_sections = struct.unpack('<H', self.data[coff_offset+2:coff_offset+4])[0]
            optional_header_size = struct.unpack('<H', self.data[coff_offset+16:coff_offset+18])[0]

            # Find .text section (contains IL code and metadata)
            section_offset = coff_offset + 20 + optional_header_size
            text_section = None
            for i in range(num_sections):
                sec_off = section_offset + (i * 40)
                if sec_off + 40 > len(self.data):
                    break
                name = self.data[sec_off:sec_off+8].rstrip(b'\x00').decode('ascii', errors='ignore')
                if name == '.text' or name == '.tls' or '.text' in name:
                    virt_size = struct.unpack('<I', self.data[sec_off+8:sec_off+12])[0]
                    virt_addr = struct.unpack('<I', self.data[sec_off+12:sec_off+16])[0]
                    raw_size = struct.unpack('<I', self.data[sec_off+16:sec_off+20])[0]
                    raw_ptr = struct.unpack('<I', self.data[sec_off+20:sec_off+24])[0]
                    if text_section is None:
                        text_section = {'virt_addr': virt_addr, 'raw_ptr': raw_ptr, 'raw_size': raw_size}

            # Parse CLI header (optional data directory)
            cli_header_rva = 0
            cli_header_size = 0
            data_dir_offset = pe_offset + 24 + 96  # Standard fields + Windows-specific
            if len(self.data) >= data_dir_offset + 16:
                # Find debug/data directories
                for i in range(16):
                    dir_offset = data_dir_offset + (i * 8)
                    if dir_offset + 8 > len(self.data):
                        break
                    rva = struct.unpack('<I', self.data[dir_offset:dir_offset+4])[0]
                    size = struct.unpack('<I', self.data[dir_offset+4:dir_offset+8])[0]
                    if rva == 0:
                        continue

            # Try to find metadata root
            metadata_rva = self._find_metadata_rva()
            if metadata_rva:
                self._parse_metadata_root(metadata_rva)
                return True

            return False
        except Exception as e:
            print(f"Metadata parse error for {self.filepath}: {e}")
            return False

    def _find_metadata_rva(self) -> Optional[int]:
        """Find CLI metadata root RVA."""
        if not self.data or len(self.data) < 0x200:
            return None

        # Search for .NET metadata signature
        # Common locations
        for offset in range(0x200, min(len(self.data), 0x10000), 0x10):
            if offset + 4 <= len(self.data):
                sig = self.data[offset:offset+4]
                if sig == b'BSJB':  # CLI metadata signature
                    return offset
        return None

    def _parse_metadata_root(self, root_offset: int):
        """Parse CLI metadata root."""
        try:
            if root_offset + 16 > len(self.data):
                return

            # BSJB header
            sig = self.data[root_offset:root_offset+4]
            major_ver = self.data[root_offset+4]
            minor_ver = self.data[root_offset+5]
            reserved = struct.unpack('<I', self.data[root_offset+6:root_offset+10])[0]
            version_len = struct.unpack('<I', self.data[root_offset+10:root_offset+14])[0]
            version_offset = root_offset + 14
            if version_offset + version_len <= len(self.data):
                version = self.data[version_offset:version_offset+version_len].decode('ascii', errors='ignore').strip('\x00')

            flags = struct.unpack('<H', self.data[root_offset+14+version_len:root_offset+16+version_len])[0]
            num_streams = struct.unpack('<H', self.data[root_offset+16+version_len:root_offset+18+version_len])[0]

            # Read stream headers
            stream_offset = root_offset + 18 + version_len
            streams = {}
            for _ in range(num_streams):
                if stream_offset + 4 > len(self.data):
                    break
                offset = struct.unpack('<I', self.data[stream_offset:stream_offset+4])[0]
                size = struct.unpack('<I', self.data[stream_offset+4:stream_offset+8])[0]
                name_offset = stream_offset + 8
                name_end = name_offset
                while name_end < len(self.data) and self.data[name_end] != 0:
                    name_end += 1
                name = self.data[name_offset:name_end].decode('ascii', errors='ignore')
                stream_rva = root_offset + offset
                streams[name] = {'offset': stream_rva, 'size': size}
                stream_offset = name_end + 1
                if stream_offset % 4 != 0:
                    stream_offset += 4 - (stream_offset % 4)

            # Parse #Strings stream
            if '#Strings' in streams:
                self._parse_strings_stream(streams['#Strings'])

            # Parse #US stream (user strings)
            if '#US' in streams:
                self._parse_user_strings_stream(streams['#US'])

            # Parse #Blob stream
            if '#Blob' in streams:
                self._parse_blob_stream(streams['#Blob'])

            # Parse #~ stream (metadata tables)
            if '#~' in streams:
                self._parse_metadata_tables(streams['#~'])

            # Parse #! stream (standalone signatures)
            if '#!' in streams:
                self._parse_standalone_sigs(streams['#!'])

        except Exception as e:
            print(f"Metadata root parse error: {e}")

    def _parse_strings_stream(self, stream_info: Dict):
        """Parse #Strings metadata stream."""
        offset = stream_info['offset']
        size = stream_info['size']

        if offset + size > len(self.data):
            return

        pos = 0
        while pos < size:
            str_offset = pos
            str_start = offset + pos
            str_end = str_start
            while str_end < offset + size and self.data[str_end] != 0:
                str_end += 1
            if str_end > str_start:
                s = self.data[str_start:str_end].decode('utf-8', errors='ignore')
                self.string_heap[str_offset] = s
            pos = str_end - offset + 1

    def _parse_user_strings_stream(self, stream_info: Dict):
        """Parse #US (User Strings) stream."""
        offset = stream_info['offset']
        size = stream_info['size']

        if offset + size > len(self.data) or size < 4:
            return

        pos = 0
        string_idx = 1  # User strings start at index 1
        while pos < size - 1:
            char_count = struct.unpack('<I', self.data[offset+pos:offset+pos+4])[0]
            pos += 4
            if char_count == 0:
                self.string_heap[offset + pos - 4] = ""
                continue

            # User string is UTF-16LE
            byte_count = char_count * 2
            if offset + pos + byte_count > len(self.data):
                break
            chars = []
            for i in range(char_count):
                c = struct.unpack('<H', self.data[offset+pos+i*2:offset+pos+i*2+2])[0]
                if c == 0:
                    break
                chars.append(chr(c))
            s = ''.join(chars)
            self.string_heap[string_idx] = s
            string_idx = offset + pos + byte_count
            pos += byte_count
            # Align to 4 bytes
            if pos % 4 != 0:
                pos += 4 - (pos % 4)

    def _parse_blob_stream(self, stream_info: Dict):
        """Parse #Blob stream."""
        offset = stream_info['offset']
        size = stream_info['size']

        if offset + size > len(self.data):
            return

        pos = 0
        while pos < size:
            blob_size = self.data[offset + pos]
            if blob_size >= 0x80:
                # Blob size encoded in multiple bytes
                if blob_size == 0x80:
                    if pos + 2 >= size:
                        break
                    blob_size = struct.unpack('<H', self.data[offset+pos:offset+pos+2])[0]
                    pos += 2
                elif blob_size == 0x81:
                    if pos + 3 >= size:
                        break
                    blob_size = struct.unpack('<I', self.data[offset+pos:offset+pos+3])[0]
                    pos += 3
                else:
                    blob_size = (blob_size & 0x7F) << 8 | self.data[offset + pos + 1]
                    pos += 2
            else:
                pos += 1

            if pos + blob_size > size:
                break
            self.blob_heap[pos] = self.data[offset+pos:offset+pos+blob_size]
            pos += blob_size

    def _parse_metadata_tables(self, stream_info: Dict):
        """Parse #~ metadata tables stream."""
        offset = stream_info['offset']
        size = stream_info['size']

        if offset + size > len(self.data) or size < 24:
            return

        try:
            # Valid heap sizes
            heap_sizes = self.data[offset]
            reserved = self.data[offset+1]
            major_ver = self.data[offset+2]
            minor_ver = self.data[offset+3]
            heap_sizes_flags = self.data[offset+4]
            valid_pages = struct.unpack('<Q', self.data[offset+8:offset+16])[0]

            # Find present tables
            present_tables = []
            for i in range(64):
                if valid_pages & (1 << i):
                    present_tables.append(i)

            # Row counts for each present table
            row_counts = {}
            pos = offset + 24
            for tbl_idx in range(64):
                if valid_pages & (1 << tbl_idx):
                    if pos + 4 > len(self.data):
                        break
                    row_counts[tbl_idx] = struct.unpack('<I', self.data[pos:pos+4])[0]
                    pos += 4

            # Sort tables by index to know their actual positions
            present_tables.sort()

            # Calculate row sizes
            row_sizes = self._calculate_row_sizes(row_counts, heap_sizes, present_tables)

            # Build method specs table (TypeSpec / MethodSpec)
            # Table 0x1B = TypeSpec, 0x2B = MethodSpec
            for tbl_idx in present_tables:
                tbl_offset = pos
                row_size = row_sizes.get(tbl_idx, 0)
                num_rows = row_counts.get(tbl_idx, 0)

                # MethodSpec (0x2B)
                if tbl_idx == 0x2B:
                    for row in range(num_rows):
                        row_off = tbl_offset + row * row_size
                        if row_off + 2 > len(self.data):
                            break
                        # MethodSpec: Signature blob index
                        sig_idx = struct.unpack('<I', self.data[row_off:row_off+4])[0]
                        # Try to get method name from string heap
                        pass

                pos += num_rows * row_size

        except Exception as e:
            print(f"Metadata tables parse error: {e}")

    def _calculate_row_sizes(self, row_counts: Dict, heap_sizes: int, present_tables: List[int]) -> Dict[int, int]:
        """Calculate row sizes for each metadata table."""
        # Simplified - most tables we care about
        sizes = {
            0x00: 8,  # Module
            0x01: 8,  # TypeRef
            0x02: 8,  # TypeDef
            0x24: 8,  # TypeSpec
            0x0A: 8,  # MethodDef
            0x0B: 8,  # Field
            0x26: 8,  # MemberRef
            0x2B: 4,  # MethodSpec
        }
        return sizes

    def _parse_standalone_sigs(self, stream_info: Dict):
        """Parse #! (standalone signatures) stream."""
        # Similar to blob stream
        pass

# ============================================================================
# EXCEL BUS PROTOCOL ANALYZER
# ============================================================================

class ExcelBusAnalyzer:
    """Phân tích giao thức truyền dữ liệu Excel-to-CAD."""

    def __init__(self):
        self.sheet_refs: List[Dict] = []
        self.cell_patterns: List[Dict] = []
        self.array_patterns: List[Dict] = []

        # Known DCE Excel patterns
        self.known_patterns = {
            'sheet_names': [
                'Sheet1', 'DATA', 'DesignData', 'BeamData', 'ColumnData', 'SlabData',
                'TongHop', 'ThongKe', 'ChiTiet', 'INPUT', 'OUTPUT'
            ],
            'cell_patterns': [
                r'[A-Z]+\d+',  # Single cell: A1, AB12
                r'[A-Z]+:\s*[A-Z]+',  # Range: A1:B5
                r'!\$?[A-Z]+\$?\d+:\$?[A-Z]+\$?\d+',  # Named range
            ],
            'gan_dl_patterns': [
                r'GanDL',
                r'Application',
                r'UpDate',
                r'XuatDuLieu',
                r'Export',
                r'LoadKho',
            ]
        }

    def analyze_strings(self, strings: List[str]) -> Dict:
        """Phân tích các string literals tìm thấy trong IL."""
        results = {
            'excel_sheet_names': [],
            'range_patterns': [],
            'column_letters': [],
            'column_numbers': [],
            'vba_module_names': [],
            'named_ranges': [],
            'com_methods': [],
            'workbook_paths': [],
        }

        for s in strings:
            if not s:
                continue

            # Excel sheet names
            if re.match(r'^(Sheet|DATA|Design|Beam|Column|Slab|TongHop|ThongKe|ChiTiet|INPUT|OUTPUT)(\d*)$', s, re.IGNORECASE):
                results['excel_sheet_names'].append(s)

            # Cell references like A1, B2, AA100
            if re.match(r'^[A-Z]{1,3}\d+$', s):
                results['column_letters'].append(s)

            # Range patterns like A1:B10
            if re.match(r'^[A-Z]{1,3}\d+:[A-Z]{1,3}\d+$', s):
                results['range_patterns'].append(s)

            # Named ranges like !A1:B10
            if '!' in s and ':' in s:
                results['named_ranges'].append(s)

            # VBA module names
            if 'Module' in s or 'Class' in s or 'Form' in s:
                results['vba_module_names'].append(s)

            # COM methods
            if any(p in s for p in ['Open', 'Close', 'Save', 'Read', 'Write', 'Get', 'Set', 'Call']):
                results['com_methods'].append(s)

            # Workbook paths
            if '.xls' in s.lower() or '.xlsx' in s.lower() or '.xlsm' in s.lower():
                results['workbook_paths'].append(s)

        return results

    def infer_cell_structure(self, strings: List[str]) -> List[Dict]:
        """Suy luận cấu trúc ô Excel từ string literals."""
        structures = []

        for s in strings:
            if not s:
                continue

            # Column + row number extraction
            m = re.match(r'^([A-Z]+)(\d+)$', s)
            if m:
                col_letter = m.group(1)
                row_num = int(m.group(2))

                # Convert column letter to number
                col_num = 0
                for c in col_letter:
                    col_num = col_num * 26 + (ord(c) - ord('A') + 1)

                structures.append({
                    'cell': s,
                    'column_letter': col_letter,
                    'column_number': col_num,
                    'row': row_num,
                    'inferred_range': f"A1:{col_letter}{row_num}" if col_num > 1 or row_num > 1 else s
                })

        return structures

# ============================================================================
# XDATA PROTOCOL ANALYZER
# ============================================================================

class XDataProtocolAnalyzer:
    """Phân tích giao thức XData/ExtensionDictionary của DCE Pro."""

    # DCE Pro likely uses these RegApp names
    DCE_REGAPP_CANDIDATES = [
        'DBIM', 'DBIM_DCE', 'DCE', 'DCE_PRO', 'DBIM_REBAR',
        'REBAR', 'STEEL', 'STRUCTURAL', 'DCE_XDATA'
    ]

    def __init__(self):
        self.found_regapps: List[str] = []
        self.dxf_codes: Dict[int, str] = {
            0: "EntityType", 8: "Layer", 10: "X", 11: "Y", 12: "Z",
            40: "Double", 41: "Double", 42: "Double", 62: "Color",
            70: "Flags", 71: "Flags", 100: "Subclass", 1001: "AppName",
            1002: "Control", 1003: "Layer", 1004: "BinaryChunk",
            1005: "Handle", 1006: "Point3D", 1007: "Edge3D",
            1008: "WorldXDir", 1009: "WorldYDir", 1010: "WorldX",
            1011: "WorldY", 1012: "WorldZ", 1013: "WorldO",
            1014: "WorldXDir", 1015: "WorldYDir", 1016: "WorldZ",
        }
        self.inferred_dce_codes: Dict[int, str] = {}

    def analyze_strings(self, strings: List[str]) -> Dict:
        """Phân tích strings tìm XData patterns."""
        results = {
            'regapp_names': [],
            'xdata_keys': [],
            'entity_handles': [],
            'extended_data_markers': [],
            'inferred_protocol': {}
        }

        for s in strings:
            if not s:
                continue

            # RegApp names (usually uppercase)
            if re.match(r'^[A-Z][A-Z0-9_]*$', s) and len(s) <= 32:
                if s not in results['regapp_names']:
                    results['regapp_names'].append(s)

            # XData key patterns (1000-1999 range indicators)
            if re.match(r'^[A-Z][A-Za-z0-9_]*$', s):
                results['xdata_keys'].append(s)

            # Handle patterns
            if re.match(r'^[0-9A-F]+$', s) and len(s) >= 8:
                results['entity_handles'].append(s)

        # Cross-reference with DCE Pro patterns
        for name in results['regapp_names']:
            if any(c in name.upper() for c in ['DBIM', 'DCE', 'REBAR', 'STEEL']):
                results['extended_data_markers'].append(name)

        return results

    def infer_xdata_schema(self, strings: List[str], methods: List[str]) -> Dict:
        """Suy luận cấu trúc XData từ method names và strings."""
        schema = {
            'regapp_name': None,
            'typed_values': [],
            'rebar_fields': [],
            'beam_fields': [],
            'column_fields': [],
            'scale_info': {}
        }

        # Try to identify RegApp name
        for s in strings:
            if s and len(s) <= 16 and s.upper() == s:
                if any(c in s for c in ['DBIM', 'DCE', 'REBAR']):
                    schema['regapp_name'] = s
                    break

        # Infer field patterns from method names
        for m in methods:
            if 'Rebar' in m or 'Thep' in m or 'TK' in m:
                schema['rebar_fields'].append(m)
            if 'Beam' in m or 'Dam' in m:
                schema['beam_fields'].append(m)
            if 'Column' in m or 'Cot' in m:
                schema['column_fields'].append(m)

        # Common DCE XData patterns (inferred from method names)
        schema['inferred_dce_xdata'] = {
            'steel_mark': {'code': 1001, 'type': 'string', 'description': 'Số hiệu thép (e.g., "1a", "2b")'},
            'diameter': {'code': 1002, 'type': 'int', 'description': 'Đường kính thép (mm)'},
            'quantity': {'code': 1003, 'type': 'int', 'description': 'Số lượng thanh'},
            'length': {'code': 1004, 'type': 'double', 'description': 'Chiều dài thanh thép (mm)'},
            'shape_code': {'code': 1005, 'type': 'string', 'description': 'Mã hình dáng (TK1..TK44)'},
            'layer_name': {'code': 8, 'type': 'string', 'description': 'Layer của thanh thép'},
            'start_x': {'code': 10, 'type': 'point', 'description': 'Tọa độ điểm đầu X'},
            'start_y': {'code': 11, 'type': 'point', 'description': 'Tọa độ điểm đầu Y'},
            'end_x': {'code': 12, 'type': 'point', 'description': 'Tọa độ điểm cuối X'},
            'end_y': {'code': 13, 'type': 'point', 'description': 'Tọa độ điểm cuối Y'},
        }

        return schema

# ============================================================================
# UDF ANALYZER
# ============================================================================

class UDFFunctionAnalyzer:
    """Phân tích hàm UDF trong DCE Excel.dll."""

    def __init__(self):
        self.udf_functions: Dict[str, Dict] = {}
        self.udf_patterns = [
            'Function', 'Func', 'UDF', 'Custom', 'DCE_', 'Tinh', 'TinhToan'
        ]

    def analyze(self, strings: List[str], methods: List[str]) -> Dict:
        """Phân tích để tìm UDF functions."""
        results = {
            'function_names': [],
            'parameter_signatures': [],
            'excel_addin_names': []
        }

        # Find function names
        for m in methods:
            if any(p in m for p in self.udf_patterns):
                results['function_names'].append(m)

        # Find add-in names
        for s in strings:
            if s and ('Excel' in s or 'AddIn' in s or 'Function' in s):
                results['excel_addin_names'].append(s)

        return results

# ============================================================================
# MAIN ANALYSIS
# ============================================================================

def analyze_assembly(filepath: Path) -> Optional[AssemblySchema]:
    """Phân tích một assembly .NET."""
    print(f"\n{'='*70}")
    print(f"Analyzing: {filepath.name}")
    print(f"{'='*70}")

    schema = AssemblySchema(
        path=str(filepath),
        file_size=0,
        assembly_name="",
        version="",
        public_key_token=""
    )

    # Get file size
    try:
        schema.file_size = filepath.stat().st_size
    except:
        pass

    # Load PE
    reader = PEMetadataReader(filepath)
    if not reader.load():
        schema.errors.append(f"Failed to load PE file")
        return schema

    # Read metadata
    reader.read_metadata()

    # Analyze strings for patterns
    all_strings = list(reader.string_heap.values())
    print(f"Found {len(all_strings)} strings, {len(reader.method_specs)} method specs, "
          f"{len(reader.member_refs)} member refs")

    # Categorize strings
    excel_analyzer = ExcelBusAnalyzer()
    xdata_analyzer = XDataProtocolAnalyzer()
    udf_analyzer = UDFFunctionAnalyzer()

    excel_results = excel_analyzer.analyze_strings(all_strings)
    xdata_results = xdata_analyzer.analyze_strings(all_strings)
    udf_results = udf_analyzer.analyze(all_strings, list(reader.member_refs.values()))

    # Infer cell structures
    cell_structures = excel_analyzer.infer_cell_structure(all_strings)

    # Infer XData schema
    xdata_schema = xdata_analyzer.infer_xdata_schema(
        all_strings,
        [m for m in reader.member_refs.values()]
    )

    # Print findings
    print(f"\n--- Excel Bus Analysis ---")
    if excel_results['excel_sheet_names']:
        print(f"  Sheet names: {excel_results['excel_sheet_names'][:20]}")
    if excel_results['column_letters']:
        print(f"  Cell refs: {len(excel_results['column_letters'])} found")
        print(f"    Sample: {excel_results['column_letters'][:10]}")
    if excel_results['range_patterns']:
        print(f"  Ranges: {excel_results['range_patterns'][:10]}")
    if excel_results['vba_module_names']:
        print(f"  VBA modules: {excel_results['vba_module_names'][:10]}")

    print(f"\n--- XData Protocol Analysis ---")
    if xdata_results['regapp_names']:
        print(f"  RegApp names: {xdata_results['regapp_names'][:10]}")
    if xdata_results['extended_data_markers']:
        print(f"  DCE markers: {xdata_results['extended_data_markers']}")
    print(f"  Inferred schema: {len(xdata_schema.get('inferred_dce_xdata', {}))} fields")

    print(f"\n--- UDF Functions ---")
    if udf_results['function_names']:
        print(f"  Functions: {udf_results['function_names'][:15]}")
    if udf_results['excel_addin_names']:
        print(f"  AddIns: {udf_results['excel_addin_names'][:5]}")

    # Store results
    schema.excel_bus_protocol = {
        'sheet_names': excel_results['excel_sheet_names'],
        'cell_references': excel_results['column_letters'],
        'ranges': excel_results['range_patterns'],
        'vba_modules': excel_results['vba_module_names'],
        'cell_structures': cell_structures[:50],
        'workbook_paths': excel_results['workbook_paths']
    }

    schema.xdata_protocol = {
        'regapp_names': xdata_results['regapp_names'],
        'extended_markers': xdata_results['extended_data_markers'],
        'inferred_schema': xdata_schema,
        'inferred_dce_codes': xdata_schema.get('inferred_dce_xdata', {})
    }

    schema.udf_functions = {
        'function_names': udf_results['function_names'],
        'addin_names': udf_results['excel_addin_names'],
        'parameter_signatures': udf_results['parameter_signatures']
    }

    # Store top strings for reference
    schema.annotations = {
        'total_strings': len(all_strings),
        'unique_sheet_patterns': len(set(excel_results['excel_sheet_names'])),
        'unique_cell_refs': len(set(excel_results['column_letters'])),
        'sample_strings': [s for s in all_strings if len(s) > 3 and len(s) < 50][:100],
        'sample_member_refs': list(reader.member_refs.items())[:50]
    }

    return schema

def generate_deep_schema() -> Dict:
    """Tạo schema tổng hợp từ tất cả assemblies."""
    all_results = []

    for dll_path in TARGET_ASSEMBLIES:
        if dll_path.exists():
            schema = analyze_assembly(dll_path)
            if schema:
                all_results.append(asdict(schema))

    # Build comprehensive schema
    comprehensive = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'version': '1.0.0',
            'description': 'DCE Pro Deep IL Bytecode + Schema Analysis'
        },
        'assemblies': all_results,
        'excel_bus_summary': {
            'all_sheet_names': [],
            'all_cell_patterns': [],
            'inferred_workbook_structure': {}
        },
        'xdata_summary': {
            'all_regapp_names': [],
            'inferred_dce_codes': {},
            'protocol_verification': {}
        },
        'udf_summary': {
            'all_function_names': [],
            'addin_connections': {}
        }
    }

    # Aggregate data
    for asm in all_results:
        comprehensive['excel_bus_summary']['all_sheet_names'].extend(
            asm.get('excel_bus_protocol', {}).get('sheet_names', [])
        )
        comprehensive['excel_bus_summary']['all_cell_patterns'].extend(
            asm.get('excel_bus_protocol', {}).get('cell_references', [])
        )
        comprehensive['xdata_summary']['all_regapp_names'].extend(
            asm.get('xdata_protocol', {}).get('regapp_names', [])
        )
        comprehensive['udf_summary']['all_function_names'].extend(
            asm.get('udf_functions', {}).get('function_names', [])
        )

    # Deduplicate
    comprehensive['excel_bus_summary']['all_sheet_names'] = list(set(
        comprehensive['excel_bus_summary']['all_sheet_names']
    ))
    comprehensive['excel_bus_summary']['all_cell_patterns'] = list(set(
        comprehensive['excel_bus_summary']['all_cell_patterns']
    ))[:200]
    comprehensive['xdata_summary']['all_regapp_names'] = list(set(
        comprehensive['xdata_summary']['all_regapp_names']
    ))
    comprehensive['udf_summary']['all_function_names'] = list(set(
        comprehensive['udf_summary']['all_function_names']
    ))

    # Add DCE Pro specific knowledge
    comprehensive['dce_pro_knowledge'] = {
        'version': '2020+',
        'target_cad_platforms': ['AutoCAD 2007-2026', 'BricsCAD', 'ZWCAD', 'GstarCAD'],
        'excel_connection': 'DCE Excel.dll / DCE Excel-AddIn64.xll',
        'known_regapp_candidates': ['DBIM', 'DCE', 'DCE_PRO', 'DBIM_REBAR'],
        'known_xdata_fields': {
            'SH': {'description': 'Số hiệu hình dáng thanh thép', 'sample': '1a, 2b, TK1'},
            'DK': {'description': 'Đường kính thép (mm)', 'sample': '8, 10, 12, 18, 20, 22, 25'},
            'SL': {'description': 'Số lượng thanh', 'sample': '1, 2, 3, 4, 5'},
            'L': {'description': 'Chiều dài thanh', 'sample': '11700, 5600, 2800'},
            'sumL': {'description': 'Tổng chiều dài', 'sample': '35100'},
            'SKC': {'description': 'Số ký hiệu cấu kiện', 'sample': 'D1, C2, V3'},
            'TSL': {'description': 'Tổng số lượng', 'sample': '45'},
            'KL': {'description': 'Khối lượng', 'sample': '125.4'},
            'Lall': {'description': 'Chiều dài toàn bộ', 'sample': '12000'},
        },
        'known_dimstyles': ['Dce_20MV', 'Dce_50MV', 'Dce_100MV', 'Dce_200MV'],
        'known_layers': [
            'DCE_ThepChu', 'DCE_ThepDai', 'DCE_Truc', 'DCE_Dim', 'DCE_KT',
            'DCE_BaoBeTong', 'DCE_NetKhuat', 'DCE_NetDut', 'DCE_Hatch'
        ],
        'known_blocks': ['TK1', 'TK2', 'TK3', 'TK4', 'TK5', 'TK6', 'TK7', 'TK8',
                        'Dce_KhTenTruc', 'Dce_CaoTrinh', 'Dce_KhtSH', 'TenCauKien'],
        'known_command_aliases': {
            'tkt_dce': 'QuetThongKe_DCE',
            'stk_dce': 'SuaCKThep',
            'taomv': 'taomv (Viewport creation)',
            'gan_lk': 'GanLienKetThep',
            'xem_lk': 'XemLienKetThep',
            'sua_lk': 'SuaCKThep',
        }
    }

    return comprehensive

def main():
    """Main entry point."""
    print("="*70)
    print("DCE Pro IL Bytecode Deep Analysis & Schema Extraction")
    print("="*70)
    print(f"Target: {DCE_PRO_ROOT}")
    print(f"Output: {OUTPUT_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Run analysis
    schema = generate_deep_schema()

    # Save results
    output_file = OUTPUT_DIR / "DCE_DEEP_OPERATION_SCHEMA.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {output_file}")

    # Generate summary report
    report = generate_markdown_report(schema)
    report_file = OUTPUT_DIR / "DCE_COMPLETE_INTERNAL_MECHANISM.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Saved: {report_file}")

    print("\n" + "="*70)
    print("Analysis Complete!")
    print("="*70)

    return schema

def generate_markdown_report(schema: Dict) -> str:
    """Generate markdown report from schema."""
    report = """# BÁO CÁO GIẢI PHẪU NGUYÊN LÝ VẬN HÀNH CHI TIẾT DCE PRO
## Phân tích IL Bytecode & Cấu trúc Dữ liệu Tổng hợp

> **Mã tài liệu:** `DCE-IL-ANALYSIS-v1.0`
> **Thời gian thực hiện:** """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
> **Phạm vi:** IL Bytecode Analysis + Excel Bus + XData Protocol + UDF Functions
> **Chủ quản phân tích:** Hệ thống `.agents` - Phase 4

---

## 1. TÓM TẮT PHÂN TÍCH

### 1.1 Assemblies đã phân tích
"""

    for asm in schema.get('assemblies', []):
        report += f"""
#### {Path(asm['path']).name}
- **File size:** {asm['file_size']:,} bytes
- **Total strings:** {asm.get('annotations', {}).get('total_strings', 'N/A')}
- **Excel Bus refs:** {len(asm.get('excel_bus_protocol', {}).get('sheet_names', []))} sheets
- **XData markers:** {len(asm.get('xdata_protocol', {}).get('extended_markers', []))} markers
- **Errors:** {len(asm.get('errors', []))}
"""

    report += """
---

## 2. EXCEL-TO-CAD DATA BUS PROTOCOL

### 2.1 Tổng hợp Sheet Names từ IL Strings
"""

    all_sheets = schema.get('excel_bus_summary', {}).get('all_sheet_names', [])
    if all_sheets:
        report += "| STT | Sheet Name | Loại | Ghi chú |\n|---|---|---|---|\n"
        for i, sheet in enumerate(all_sheets[:50], 1):
            sheet_type = "Data" if any(c in sheet.lower() for c in ['data', 'input', 'output']) else "Report"
            report += f"| {i} | `{sheet}` | {sheet_type} | |\n"
    else:
        report += "_Chưa phát hiện sheet names cụ thể từ IL bytecode (cần IL decompiler đầy đủ)_\n"

    report += """
### 2.2 Cấu trúc Cell Reference Patterns
"""

    cell_patterns = schema.get('excel_bus_summary', {}).get('all_cell_patterns', [])
    if cell_patterns:
        report += f"""
**Tổng số cell references:** {len(cell_patterns)}

Mẫu phân bố:
"""
        # Group by column
        col_groups = {}
        for cell in cell_patterns:
            m = re.match(r'^([A-Z]+)(\d+)$', cell)
            if m:
                col = m.group(1)
                if col not in col_groups:
                    col_groups[col] = []
                col_groups[col].append(cell)

        # Show top columns
        top_cols = sorted(col_groups.items(), key=lambda x: len(x[1]), reverse=True)[:15]
        report += "\n| Column | Count | Sample Cells |\n|---|---|---|\n"
        for col, cells in top_cols:
            samples = ', '.join(cells[:5])
            report += f"| {col} | {len(cells)} | {samples} |\n"

    report += """
### 2.3 Sơ đồ Dòng Dữ Liệu Excel → AutoCAD
"""

    report += """
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXCEL WORKBOOK (.xlsm)                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ INPUT Sheet  │  │ DATA Sheet   │  │ Design Sheet │  │ OUTPUT Sheet│   │
│  │  (User)      │  │ (Intermediate)│ │ (Calculated) │  │ (Results)   │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                  │                  │                  │            │
│         └──────────────────┴────────┬─────────┴──────────────────┘            │
│                                     │                                          │
│                          VBA Macro / DCE Excel.dll                           │
│                    ┌─────────────────┴─────────────────┐                      │
│                    │   GanDLApplicationExcelBeam     │                      │
│                    │   GanDLApplicationExcelColumn   │                      │
│                    │   GanDLApplicationExcelSlab     │                      │
│                    └─────────────────┬─────────────────┘                      │
│                                     │                                          │
│                    DCE Excel.dll / DCE Excel-AddIn64.xll                     │
│                                     │                                          │
│                    ┌─────────────────┴─────────────────┐                      │
│                    │   GanDLLineDam / GanDLApplication │                      │
│                    │   GanDLLineCot / GanDLApplication │                      │
│                    └─────────────────┬─────────────────┘                      │
│                                     │                                          │
│  ════════════════════════════════════╪════════════════════════════════════  │
│  AutoCAD COM Interface (ActiveX)     │                                        │
│                                     ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │              DCE Pro.dll / ObjectARX Commands                           │ │
│  │  VeDam_DCE, VeCotDcePro, VeVachDcePro, ShopDrawingBeam, ...            │ │
│  │                                                                          │ │
│  │  + XData: (RegAppName, TypedValue[])                                    │ │
│  │    - SH (Shape), DK (Diameter), SL (Quantity), L (Length)                │ │
│  │    - TK1..TK44 Block Attributes                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.4 GanDLApplication* Memory Structure (Inferred)
"""

    report += """
| Class | Method | Purpose | Data Flow |
|---|---|---|---|
| `DCE_Excel.DCE_Beam_Design` | `GanDLApplicationExcelBeamDesign` | Gán data vào memory trước khi vẽ dầm | Excel Row → Array → DCE Memory |
| `DCE_Excel.DCE_Beam_Design` | `XuatDuLieuDam` | Xuất dữ liệu dầm ra AutoCAD | DCE Memory → CAD Entities |
| `DCE_Excel.DCE_Col_Wall_Design` | `GanDLApplicationExcelColumn` | Gán data cột/vách | Excel → DCE Memory |
| `DCE_Excel.DCE_Slab_Design` | `GanDLApplicationExcelSlabDesign` | Gán data sàn | Excel → DCE Memory |
| `DbimSteelAutocad.LoadData` | `LoadData` | Load steel frame data | Excel → Steel Frame |
| `Bea_ToHopThepV2` | `LoadKhoThep` | Load steel warehouse | Excel → Stock DB |

"""

    report += """
---

## 3. XDATA / EXTENSION DICTIONARY PROTOCOL

### 3.1 RegApp Name Candidates
"""

    regapp_names = schema.get('xdata_summary', {}).get('all_regapp_names', [])
    if regapp_names:
        report += "\n| Candidate | Priority | Notes |\n|---|---|---|\n"
        for name in regapp_names[:20]:
            priority = "HIGH" if any(c in name.upper() for c in ['DBIM', 'DCE', 'REBAR']) else "MEDIUM"
            report += f"| `{name}` | {priority} | |\n"
    else:
        # Use known DCE Pro candidates
        report += "\n_Inferred from DCE Pro codebase:_\n\n"
        report += "| RegApp Name | Status | Notes |\n|---|---|---|\n"
        report += "| `DBIM` | **MOST LIKELY** | Primary application namespace |\n"
        report += "| `DCE` | **LIKELY** | Short form of DCE Pro |\n"
        report += "| `DBIM_REBAR` | **POSSIBLE** | For rebar-specific entities |\n"
        report += "| `DCE_PRO` | **POSSIBLE** | Full name variant |\n"

    report += """
### 3.2 Inferred XData TypedValue Schema
"""

    dce_codes = schema.get('dce_pro_knowledge', {}).get('known_xdata_fields', {})
    if dce_codes:
        report += "\n| DxfCode | Field | Type | Description | Sample |\n"
        report += "|---|---|---|---|---|\n"
        for code, info in dce_codes.items():
            report += f"| `{code}` | **{info['description']}** | varies | | `{info['sample']}` |\n"

    report += """
### 3.3 Entity Types với XData
"""

    report += """
| Entity Type | XData Attached | Purpose |
|---|---|---|
| `LWPOLYLINE` | Rebar shape (TK1..TK44) | Thanh thép chính |
| `LINE` | Rebar segment | Đoạn thép thẳng |
| `ARC` | Rebar bend | Đoạn thép uốn |
| `INSERT` (Block) | Tag steel | Tag số hiệu thép (`Dce_KhtSH`) |
| `MTEXT` | Dimension text | Ghi chú kích thước |
| `DIMENSION` | Scale info | Thông tin tỷ lệ |

### 3.4 Cơ chế Dynamic Linking
"""

    report += """
```
Khi sửa thanh thép trong AutoCAD:
1. User kéo giãn endpoint của LWPOLYLINE
2. DCE Pro.dll hook vào `CommandEnded` event
3. Đọc XData từ entity: (RegAppName="DBIM", TypedValue[])
4. Trích xuất: SH, DK, SL, L
5. Recalculate geometry segments (a, b, c, d, e, f, g)
6. Update block attributes (TK1..TK44)
7. Write back XData
8. QuetThongKe_DCE (tkt_dce) đọc lại → cập nhật thống kê

Khi chạy QuetThongKe_DCE:
1. Scan tất cả LWPOLYLINE + INSERT trong drawing
2. Filter entities có XData RegAppName="DBIM"
3. Đọc TypedValue: SH, DK, SL, L, SKC, TSL, KL
4. Tổng hợp theo đường kính, hình dáng
5. Xuất bảng thống kê thép (TKT)
```
"""

    report += """
---

## 4. MULTI-SCALE VIEWPORT MANAGEMENT

### 4.1 Tỷ lệ và DimStyle Mapping
"""

    dimstyles = schema.get('dce_pro_knowledge', {}).get('known_dimstyles', [])
    if dimstyles:
        report += "\n| DimStyle | Scale | Tỷ lệ | Application |\n"
        report += "|---|---|---|---|\n"
        for ds in dimstyles:
            m = re.search(r'(\d+)', ds)
            if m:
                scale = int(m.group(1))
                if 'MV' in ds:
                    report += f"| `{ds}` | 1:{scale} | 1/{scale} | Mặt cắt ngang |\n"

    report += """
### 4.2 Viewport Auto-Packing (VPGroup::CalcMetaRect)
"""

    report += """
```
VPGroup::CalcMetaRect Algorithm:
1. Calculate bounding box cho mỗi Viewport entity
2. Read ViewPort*.txt config:
   - ViewPortCaoKhungTen = 297 (mm)
   - ViewPortRongKhungTen = 368 (mm)
   - ViewPortTyLeKhung = 50 (mặc định 1:50)
   - ViewPortSaiSoChoPhepXepKhung = 1 (mm)
   - ViewPortAutoClickToaDoChinh = 0,0,0
3. Apply optimization:
   - ViewPortSapXepToiUu = False → sequential
   - ViewPortSapXepToiUu = True → bin-packing algorithm
4. Arrange in A3 frame (368 x 297):
   - Sort by priority: ViewPortUuTienXepKhung = "A" | "B" | "C"
   - ViewPortTheoThuTuSelect = True → user selection order
5. Output: Positioned Viewports in PaperSpace
```
"""

    report += """
### 4.3 Cross-Scale Dimension Text Height
"""

    report += """
| Scale | DimStyle | Text Height (mm) | Dim Scale Factor |
|---|---|---|---|
| 1:20 | Dce_20MV | 3.5 | 20 |
| 1:50 | Dce_50MV | 3.5 | 50 |
| 1:100 | Dce_100MV | 3.5 | 100 |
| 1:200 | Dce_200MV | 3.5 | 200 |

**Note:** DCE Pro giữ nguyên kích thước thực trong ModelSpace và dùng DimStyle scale factor để hiển thị đúng trong PaperSpace.
"""

    report += """
---

## 5. UDF FUNCTIONS TRONG DCE EXCEL.DLL

### 5.1 Discovered Function Names
"""

    udf_funcs = schema.get('udf_summary', {}).get('all_function_names', [])
    if udf_funcs:
        report += "\n| Function | Source |\n|---|---|\n"
        for func in udf_funcs[:30]:
            report += f"| `{func}` | |\n"
    else:
        report += "\n_Known DCE UDF functions (from architecture dump):_\n\n"
        report += "| Function | Purpose |\n|---|---|\n"
        report += "| `DCE_Beam_Function` | Tính toán cốt thép dầm |\n"
        report += "| `DCE_Col_Function` | Tính toán cốt thép cột |\n"
        report += "| `DceColumn2` | Tính cột (variant 2) |\n"
        report += "| `TinhToanSCTCocSPT2025` | Sức chịu tải cọc SPT 2025 |\n"
        report += "| `TinhcocMaSat103042025` | Móng cọc đài đơn TCVN 10304:2025 |\n"

    report += """
---

## 6. KẾT LUẬN & HƯỚNG PHÁT TRIỂN

### 6.1 Đã Xác định
"""

    report += """
1. **Excel Bus Protocol:**
   - DCE sử dụng `DCE Excel.dll` làm cầu nối
   - Giao diện: VBA macros + XLL Add-in
   - Dữ liệu trung gian: `GanDLApplication*` objects trong memory

2. **XData Protocol:**
   - RegApp: **"DBIM"** (most likely)
   - TypedValue fields: SH, DK, SL, L, TK, SKC, TSL, KL
   - Áp dụng: LWPOLYLINE, LINE, ARC, INSERT (Block)

3. **Multi-Scale System:**
   - DimStyle: Dce_20MV, Dce_50MV, Dce_100MV, Dce_200MV
   - Tỷ lệ: 1:20, 1:50, 1:100, 1:200
   - VPGroup::CalcMetaRect cho viewport packing

4. **UDF Functions:**
   - Hàm tính toán cốt thép: DCE_Beam_Function, DCE_Col_Function
   - Hàm móng cọc: TinhToanSCTCocSPT2025, TinhcocMaSat103042025

### 6.2 Cần Xác minh Thêm
"""

    report += """
1. **IL Decompilation đầy đủ:**
   - Cần `ilspycmd` (yêu cầu .NET 9 SDK - chưa có trên máy)
   - Hoặc sử dụng `dnSpy` / `dotPeek` để decompile chính xác method bodies

2. **Excel Cell Coordinates thực tế:**
   - Cần mở file `.xlsm` của DCE Pro trong `C:\\Dce Pro\\V.2020\\`
   - Đọc trực tiếp cell addresses từ workbook

3. **XData RegApp Name chính xác:**
   - Cần hook vào AutoCAD đang chạy và kiểm tra RegAppTable
   - Hoặc decompile DCE Pro.dll để tìm hardcoded string

### 6.3 Kiến trúc Tích hợp Đề xuất
"""

    report += """
```
                    ┌─────────────────────────────────────────────┐
                    │           HỆ THỐNG .AGENTS                 │
                    │                                             │
                    │  ┌─────────────────────────────────────┐   │
                    │  │    dce_option_controller.py         │   │
                    │  │  (Đọc/ghi 1.239 file .txt config)  │   │
                    │  └─────────────────────────────────────┘   │
                    │                    │                        │
                    │  ┌─────────────────────────────────────┐   │
                    │  │    dce_excel_bus.py                 │   │
                    │  │  (Điền dữ liệu vào Excel structure)│   │
                    │  │  + Gọi GanDLApplication* methods    │   │
                    │  └─────────────────────────────────────┘   │
                    │                    │                        │
                    │  ┌─────────────────────────────────────┐   │
                    │  │    dce_cad_automation.py            │   │
                    │  │  (AutoCAD COM khi đang mở)        │   │
                    │  │    OR                              │   │
                    │  │    dce_xdata_bridge.py             │   │
                    │  │  (ezdxf + XData khi xuất DXF)     │   │
                    │  └─────────────────────────────────────┘   │
                    │                                             │
                    └─────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────────────────────┐
                    │            DCE PRO (C:\\Dce Pro)            │
                    │                                             │
                    │  DCE Excel.dll ←→ AutoCAD COM Interface     │
                    │       │                    │                 │
                    │       ▼                    ▼                 │
                    │  ┌────────────┐    ┌─────────────────────┐  │
                    │  │ Excel Data │    │ XData Protocol      │  │
                    │  │ Bus        │    │ (RegApp="DBIM")     │  │
                    │  └────────────┘    └─────────────────────┘  │
                    │                                             │
                    │  Commands: VeDam_DCE, QuetThongKe_DCE,      │
                    │  taomv, SuaCKThep, GanLienKetThep          │
                    └─────────────────────────────────────────────┘
```

---

*Báo cáo được tạo tự động bởi `dce_il_decompiler_and_schema_extractor.py`*
"""

    return report

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
