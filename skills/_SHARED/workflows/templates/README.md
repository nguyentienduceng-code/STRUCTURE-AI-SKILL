# Workflow Templates

Các workflow templates cho Claude Code.

## Parallel Review Workflow

Review song song nhiều phần của hồ sơ.

```bash
python parallel_review_workflow.py --project DUAN_A --scope "beam,column" --output report.json
```

### Integration với Claude Code Workflow

Để sử dụng trong Claude Code:

```javascript
// Trong Claude Code workflow
const { ParallelReviewWorkflow } = require('./parallel_review_workflow.js')

const workflow = new ParallelReviewWorkflow('DUAN_A', ['beam', 'column', 'foundation'])
workflow.generate_tasks(elements)
```

## More templates sẽ được thêm...

- Forensic Investigation Loop
- Value Engineering Analysis
- Standards Compliance Check
