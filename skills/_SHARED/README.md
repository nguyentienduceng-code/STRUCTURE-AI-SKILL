# Shared Utilities

Utilities chung được dùng bởi nhiều skills.

## Cấu trúc

```
_SHARED/
├── standards_mcp/          ← MCP Server tra cứu tiêu chuẩn
│   ├── server.py         # Main server
│   └── cache/           # Cache directory
│
├── memory/               ← Project context persistence
│   ├── projects/        # Lưu context từng dự án
│   └── project_memory.py # CLI tool
│
├── workflows/            ← Workflow templates
│   ├── templates/       # Reusable templates
│   └── parallel_review_workflow.py
│
└── README.md            # File này
```

## Sử dụng

### Standards MCP Server

```bash
cd _SHARED/standards_mcp
python server.py --test
```

### Project Memory

```bash
cd _SHARED/memory
python project_memory.py --project DUAN_A --action list
python project_memory.py --project DUAN_A --action create --name "Dự án A"
```

### Parallel Review Workflow

```bash
cd _SHARED/workflows
python parallel_review_workflow.py --project DUAN_A --scope "beam,column" --output report.json
```

## Cập nhật: 2026-08-30
