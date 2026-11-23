// dce_snapshot_plugin.cs — Tầng 2B · Plugin READ-ONLY "DCE_SNAPSHOT" cho AutoCAD 2021
// ============================================================================
// Nguồn plugin .NET (AutoCAD 2021 Core Console managed, R24.0) — CHỈ ĐỌC, không sửa mô hình.
//
// API đích: AutoCAD .NET 2021 (AcCoreMgd.dll + AcDbMgd.dll). Lệnh:
//   _.NETLOAD dce_snapshot_plugin.dll
//   DCE_SNAPSHOT
//
// Đầu vào ưu tiên qua biến môi trường (an toàn Unicode & khoảng trắng khi chạy Core Console):
//   DCE_SNAPSHOT_OUT : Đường dẫn file JSON snapshot đầu ra
//   DCE_SNAPSHOT_REV : Nhãn revision tùy chọn (mặc định: tên file bản vẽ)
//   (Fallback sang PromptStringOptions nếu chạy thủ công chưa đặt DCE_SNAPSHOT_OUT.)
//
// CHỈ ĐỌC: chỉ mở Transaction OpenMode.ForRead, tuyệt đối KHÔNG gọi Document.Save()
// hay ghi ngược vào bản vẽ.
// Xuất snapshot JSON chính tắc (schema native_dwg_snapshot v1.0):
//   { document_id, revision, units:"mm",
//     records:[{element_id, role, floor_id, handle, dxftype, layer,
//               geometry:{...}, properties:{...}}, ...] }
// Định danh 2A: đọc XData AppID "DCE_ELEMENT_ID" ("ID=..;ROLE=..;FLOOR=..").
// Entity thiếu XData => element_id=null (Python đưa vào UNMATCHED, không tự gán).

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using AcAppCore = Autodesk.AutoCAD.ApplicationServices.Core;
using AcDb = Autodesk.AutoCAD.DatabaseServices;
using AcEd = Autodesk.AutoCAD.EditorInput;
using AcRt = Autodesk.AutoCAD.Runtime;

namespace DceSnapshot
{
    public static class DceSnapshotPlugin
    {
        private const string ElementIdAppId = "DCE_ELEMENT_ID";
        private const string BeamAppId = "DCE_BEAM";
        private const string RolePrimary = "PRIMARY_GEOM";
        private const string RoleTag = "ANNOTATION_TAG";
        private const string RoleDetail = "DETAIL_VIEW";
        private static readonly HashSet<string> KnownRoles =
            new HashSet<string> { RolePrimary, RoleTag, RoleDetail };

        [AcRt.CommandMethod("DCE_SNAPSHOT")]
        public static void Run()
        {
            var doc = AcAppCore.Application.DocumentManager.MdiActiveDocument;
            if (doc == null) return;
            AcEd.Editor ed = doc.Editor;

            string outPath = Environment.GetEnvironmentVariable("DCE_SNAPSHOT_OUT");
            string revision = Environment.GetEnvironmentVariable("DCE_SNAPSHOT_REV");
            bool fromEnv = !string.IsNullOrWhiteSpace(outPath);

            if (!fromEnv)
            {
                var pOut = new AcEd.PromptStringOptions("\nOut JSON path: ") { AllowSpaces = true };
                AcEd.PromptResult resOut = ed.GetString(pOut);
                if (resOut.Status != AcEd.PromptStatus.OK || string.IsNullOrWhiteSpace(resOut.StringResult))
                {
                    ed.WriteMessage("\nDCE_SNAPSHOT: no output path; aborted (read-only).");
                    return;
                }
                outPath = resOut.StringResult;

                if (string.IsNullOrWhiteSpace(revision))
                {
                    var pRev = new AcEd.PromptStringOptions("\nRevision [blank=document]: ") { AllowSpaces = true };
                    AcEd.PromptResult resRev = ed.GetString(pRev);
                    if (resRev.Status == AcEd.PromptStatus.OK)
                        revision = resRev.StringResult;
                }
            }

            string docName = string.IsNullOrWhiteSpace(doc.Name) ? "?" : doc.Name;
            string docId = Path.GetFileNameWithoutExtension(docName);
            if (string.IsNullOrWhiteSpace(docId)) docId = "?";
            if (string.IsNullOrWhiteSpace(revision)) revision = docId;

            try
            {
                AcDb.Database db = doc.Database;
                List<string> records = new List<string>();

                using (AcDb.Transaction tr = db.TransactionManager.StartTransaction())
                {
                    AcDb.BlockTable bt =
                        (AcDb.BlockTable)tr.GetObject(db.BlockTableId, AcDb.OpenMode.ForRead);
                    AcDb.BlockTableRecord msp =
                        (AcDb.BlockTableRecord)tr.GetObject(bt[AcDb.BlockTableRecord.ModelSpace],
                                                            AcDb.OpenMode.ForRead);
                    foreach (AcDb.ObjectId oid in msp)
                    {
                        if (oid.IsErased) continue;
                        AcDb.Entity ent = tr.GetObject(oid, AcDb.OpenMode.ForRead) as AcDb.Entity;
                        if (ent == null) continue;
                        records.Add(SerializeEntity(ent, tr));
                    }
                    tr.Commit();
                }

                string outDir = Path.GetDirectoryName(Path.GetFullPath(outPath));
                if (!string.IsNullOrEmpty(outDir) && !Directory.Exists(outDir))
                    Directory.CreateDirectory(outDir);

                StringBuilder sb = new StringBuilder();
                sb.Append('{');
                sb.Append("\"document_id\":").Append(JsonQuote(docId));
                sb.Append(",\"revision\":").Append(JsonQuote(revision));
                sb.Append(",\"units\":\"mm\"");
                sb.Append(",\"records\":[");
                sb.Append(string.Join(",", records));
                sb.Append(']');
                sb.Append('}');

                File.WriteAllText(outPath, sb.ToString(), new UTF8Encoding(false));
                ed.WriteMessage(string.Format(
                    CultureInfo.InvariantCulture,
                    "\nDCE_SNAPSHOT: {0} records -> {1} (READ-ONLY; source not modified).",
                    records.Count, outPath));
            }
            catch (Exception ex)
            {
                ed.WriteMessage("\nDCE_SNAPSHOT FAILED: " + ex.Message);
            }
        }

        // ── per-entity serialization ──────────────────────────────────────
        private static string SerializeEntity(AcDb.Entity e, AcDb.Transaction tr)
        {
            Identity id = ReadElementIdentity(e);
            Beam beam = ReadBeam(e);
            StringBuilder sb = new StringBuilder();
            sb.Append('{');
            sb.Append("\"element_id\":").Append(JsonQuote(id.ElementId));
            sb.Append(",\"role\":").Append(JsonQuote(id.Role));
            sb.Append(",\"floor_id\":").Append(JsonQuote(id.FloorId));
            sb.Append(",\"handle\":\"").Append(e.ObjectId.Handle.ToString()).Append('"');
            sb.Append(",\"dxftype\":\"").Append(JsonEscape(e.GetType().Name)).Append('"');
            try { sb.Append(",\"layer\":\"").Append(JsonEscape(e.Layer)).Append('"'); }
            catch { }
            if (beam.Mark != null)
                sb.Append(",\"mark\":").Append(JsonQuote(beam.Mark));
            sb.Append(",\"geometry\":"); AppendGeometry(sb, e);
            sb.Append(",\"properties\":"); AppendProperties(sb, e, tr, beam);
            sb.Append('}');
            return sb.ToString();
        }

        private static void AppendGeometry(StringBuilder sb, AcDb.Entity e)
        {
            sb.Append('{');
            bool first = true;
            AcDb.Line l = e as AcDb.Line;
            if (l != null)
            {
                PutG(sb, ref first, "x0_mm", l.StartPoint.X);
                PutG(sb, ref first, "y0_mm", l.StartPoint.Y);
                PutG(sb, ref first, "z0_mm", l.StartPoint.Z);
                PutG(sb, ref first, "x1_mm", l.EndPoint.X);
                PutG(sb, ref first, "y1_mm", l.EndPoint.Y);
                PutG(sb, ref first, "z1_mm", l.EndPoint.Z);
            }
            else if (e is AcDb.BlockReference)
            {
                AcDb.BlockReference br = (AcDb.BlockReference)e;
                PutG(sb, ref first, "insert_mm_x", br.Position.X);
                PutG(sb, ref first, "insert_mm_y", br.Position.Y);
                PutG(sb, ref first, "insert_mm_z", br.Position.Z);
                PutG(sb, ref first, "scale_x", br.ScaleFactors.X);
                PutG(sb, ref first, "scale_y", br.ScaleFactors.Y);
                PutG(sb, ref first, "scale_z", br.ScaleFactors.Z);
                PutG(sb, ref first, "rotation_deg", br.Rotation * 180.0 / Math.PI);
            }
            else if (e is AcDb.Circle)
            {
                AcDb.Circle c = (AcDb.Circle)e;
                PutG(sb, ref first, "center_mm_x", c.Center.X);
                PutG(sb, ref first, "center_mm_y", c.Center.Y);
                PutG(sb, ref first, "radius_mm", c.Radius);
            }
            else if (e is AcDb.Arc)
            {
                AcDb.Arc a = (AcDb.Arc)e;
                PutG(sb, ref first, "center_mm_x", a.Center.X);
                PutG(sb, ref first, "center_mm_y", a.Center.Y);
                PutG(sb, ref first, "radius_mm", a.Radius);
                PutG(sb, ref first, "start_deg", a.StartAngle * 180.0 / Math.PI);
                PutG(sb, ref first, "end_deg", a.EndAngle * 180.0 / Math.PI);
            }
            else if (e is AcDb.Polyline)
            {
                AcDb.Polyline pl = (AcDb.Polyline)e;
                PutG(sb, ref first, "length_mm", Math.Round(pl.Length, 4));
                PutG(sb, ref first, "closed", pl.Closed ? 1.0 : 0.0);
                PutG(sb, ref first, "vertices", (double)pl.NumberOfVertices);
            }
            else if (e is AcDb.DBText)
            {
                AcDb.DBText dt = (AcDb.DBText)e;
                PutG(sb, ref first, "x_mm", dt.Position.X);
                PutG(sb, ref first, "y_mm", dt.Position.Y);
                PutG(sb, ref first, "height_mm", dt.Height);
            }
            else if (e is AcDb.MText)
            {
                AcDb.MText mt = (AcDb.MText)e;
                PutG(sb, ref first, "x_mm", mt.Location.X);
                PutG(sb, ref first, "y_mm", mt.Location.Y);
                PutG(sb, ref first, "height_mm", mt.TextHeight);
            }
            else
            {
                sb.Append("\"note\":\"unhandled-dxftype\"");
            }
            sb.Append('}');
        }

        private static void PutG(StringBuilder sb, ref bool first, string key, double v)
        {
            if (double.IsNaN(v) || double.IsInfinity(v)) return;
            if (!first) sb.Append(',');
            first = false;
            sb.Append('"').Append(key).Append("\":").Append(Math.Round(v, 6).ToString("R", CultureInfo.InvariantCulture));
        }

        private static void PutNum(StringBuilder sb, ref bool first, string key, double v)
        {
            if (double.IsNaN(v) || double.IsInfinity(v)) return;
            if (!first) sb.Append(',');
            first = false;
            sb.Append('"').Append(key).Append("\":").Append(Math.Round(v, 3).ToString("R", CultureInfo.InvariantCulture));
        }

        private static void PutProp(StringBuilder sb, ref bool first, string key, string val)
        {
            if (!first) sb.Append(',');
            first = false;
            sb.Append('"').Append(JsonEscape(key)).Append("\":").Append(JsonQuote(val));
        }

        private static void AppendProperties(StringBuilder sb, AcDb.Entity e, AcDb.Transaction tr, Beam beam)
        {
            sb.Append('{');
            bool first = true;
            // DCE_BEAM (MARK/B/H) — nghiệp vụ; áp cho MỌI dxftype (fixture gán lên
            // LWPOLYLINE, không phải block). CÙNG regapp mà đường ezdxf cũng đọc.
            if (!string.IsNullOrEmpty(beam.B))
            {
                double bmm;
                if (double.TryParse(beam.B, NumberStyles.Float, CultureInfo.InvariantCulture, out bmm))
                    PutNum(sb, ref first, "b_mm", bmm);
            }
            if (!string.IsNullOrEmpty(beam.H))
            {
                double hmm;
                if (double.TryParse(beam.H, NumberStyles.Float, CultureInfo.InvariantCulture, out hmm))
                    PutNum(sb, ref first, "h_mm", hmm);
            }
            AcDb.BlockReference br = e as AcDb.BlockReference;
            if (br != null)
            {
                string blockName = br.Name;
                try
                {
                    AcDb.ObjectId btrId = br.IsDynamicBlock ? br.DynamicBlockTableRecord : br.BlockTableRecord;
                    if (!btrId.IsNull)
                    {
                        AcDb.BlockTableRecord btr = tr.GetObject(btrId, AcDb.OpenMode.ForRead) as AcDb.BlockTableRecord;
                        if (btr != null && !string.IsNullOrEmpty(btr.Name)) blockName = btr.Name;
                    }
                }
                catch { }
                PutProp(sb, ref first, "block_name", blockName);

                foreach (AcDb.ObjectId attId in br.AttributeCollection)
                {
                    if (attId.IsNull || attId.IsErased) continue;
                    AcDb.AttributeReference at = tr.GetObject(attId, AcDb.OpenMode.ForRead) as AcDb.AttributeReference;
                    if (at == null) continue;
                    string tag = (at.Tag == null ? "?" : at.Tag).ToUpperInvariant();
                    PutProp(sb, ref first, "attr_" + tag, at.TextString);
                    if (tag == "MARK" || tag == "TAG")
                        PutProp(sb, ref first, "mark", at.TextString);
                }
            }
            else if (e is AcDb.DBText)
            {
                AcDb.DBText dt = (AcDb.DBText)e;
                PutProp(sb, ref first, "text", dt.TextString);
            }
            else if (e is AcDb.MText)
            {
                AcDb.MText mt = (AcDb.MText)e;
                PutProp(sb, ref first, "text", mt.Text);
            }
            sb.Append('}');
        }

        // ── 2A element identity from XData DCE_ELEMENT_ID ─────────────────
        private struct Identity { public string ElementId; public string Role; public string FloorId; }

        // ── DCE_BEAM (MARK/B/H) — nghiệp vụ, CÙNG regapp đường ezdxf đọc ────
        private struct Beam { public string Mark; public string B; public string H; }

        private static Identity ReadElementIdentity(AcDb.Entity e)
        {
            Identity r = new Identity { ElementId = null, Role = RolePrimary, FloorId = "" };
            try
            {
                using (AcDb.ResultBuffer rb = e.GetXDataForApplication(ElementIdAppId))
                {
                    if (rb != null)
                    {
                        foreach (AcDb.TypedValue tv in rb)
                        {
                            if (tv.TypeCode != 1000) continue;
                            ParsePayload(tv.Value as string, ref r);
                        }
                    }
                }
            }
            catch { /* thiếu XData -> element_id null (UNMATCHED) */ }
            return r;
        }

        private static void ParsePayload(string s, ref Identity r)
        {
            if (string.IsNullOrEmpty(s)) return;
            foreach (string seg in s.Split(';'))
            {
                int idx = seg.IndexOf('=');
                if (idx <= 0) continue;
                string k = seg.Substring(0, idx).Trim().ToUpperInvariant();
                string v = seg.Substring(idx + 1).Trim();
                if (k == "ID") r.ElementId = string.IsNullOrEmpty(v) ? null : v;
                else if (k == "ROLE") r.Role = KnownRoles.Contains(v) ? v : RolePrimary;
                else if (k == "FLOOR") r.FloorId = v;
            }
        }

        // ── DCE_BEAM (MARK/B/H) từ XData regapp "DCE_BEAM" (code 1000) ─────
        private static Beam ReadBeam(AcDb.Entity e)
        {
            Beam r = new Beam { Mark = null, B = null, H = null };
            try
            {
                using (AcDb.ResultBuffer rb = e.GetXDataForApplication(BeamAppId))
                {
                    if (rb == null) return r;
                    foreach (AcDb.TypedValue tv in rb)
                    {
                        if (tv.TypeCode != 1000) continue;
                        ParseBeam(tv.Value as string, ref r);
                    }
                }
            }
            catch { /* thiếu XData DCE_BEAM -> mark/b/h null (không bịa) */ }
            return r;
        }

        private static void ParseBeam(string s, ref Beam r)
        {
            if (string.IsNullOrEmpty(s)) return;
            foreach (string seg in s.Split(';'))
            {
                int idx = seg.IndexOf('=');
                if (idx <= 0) continue;
                string k = seg.Substring(0, idx).Trim().ToUpperInvariant();
                string v = seg.Substring(idx + 1).Trim();
                if (k == "MARK" && !string.IsNullOrEmpty(v)) r.Mark = v;
                else if (k == "B" && !string.IsNullOrEmpty(v)) r.B = v;
                else if (k == "H" && !string.IsNullOrEmpty(v)) r.H = v;
            }
        }

        // ── JSON helpers ──────────────────────────────────────────────────
        private static string JsonQuote(string s)
        {
            return s == null ? "null" : "\"" + JsonEscape(s) + "\"";
        }

        private static string JsonEscape(string s)
        {
            if (string.IsNullOrEmpty(s)) return "";
            StringBuilder sb = new StringBuilder();
            foreach (char c in s)
            {
                if (c == '"') sb.Append("\\\"");
                else if (c == '\\') sb.Append("\\\\");
                else if (c == '\n') sb.Append("\\n");
                else if (c == '\r') sb.Append("\\r");
                else if (c == '\t') sb.Append("\\t");
                else if (c < 0x20) sb.AppendFormat(CultureInfo.InvariantCulture, "\\u{0:x4}", (int)c);
                else sb.Append(c);
            }
            return sb.ToString();
        }
    }
}
