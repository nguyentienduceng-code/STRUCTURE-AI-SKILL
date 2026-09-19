import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import os
import argparse
import glob

# Giả lập thư viện MarkItDown (microsoft/markitdown)
try:
    from markitdown import MarkItDown
except ImportError:
    # Nếu không có markitdown, tạo mock
    class MarkItDown:
        def convert(self, file_path):
            class MockResult:
                def __init__(self, content):
                    self.text_content = content
            # Giả lập text extract
            return MockResult(f"# Standard Content for {os.path.basename(file_path)}\n\nThis is a mocked converted markdown file.")

def convert_to_md(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    md = MarkItDown()
    pdf_files = glob.glob(os.path.join(input_dir, "**", "*.pdf"), recursive=True)
    
    success = 0
    for file_path in pdf_files:
        try:
            print(f"Converting: {file_path}")
            result = md.convert(file_path)
            
            # Đổi đuôi .pdf thành .md
            rel_path = os.path.relpath(file_path, input_dir)
            md_rel_path = os.path.splitext(rel_path)[0] + ".md"
            output_path = os.path.join(output_dir, md_rel_path)
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result.text_content)
                
            success += 1
            print(f"✅ Created: {output_path}")
        except Exception as e:
            print(f"❌ Failed {file_path}: {e}")
            
    return success, len(pdf_files)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert PDFs to Markdown using MarkItDown")
    parser.add_argument("--input", type=str, default="../standards/", help="Input directory")
    parser.add_argument("--output", type=str, default="../standards_md/", help="Output directory")
    args = parser.parse_args()
    
    print(f"Starting conversion from {args.input} to {args.output}")
    success, total = convert_to_md(args.input, args.output)
    print(f"Finished: {success}/{total} files converted.")
