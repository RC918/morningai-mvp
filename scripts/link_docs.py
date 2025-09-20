#!/usr/bin/env python3
"""
Docs ↔ 實作鏈接 - 在文檔中嵌入指向關鍵程式與 workflow 的永久連結，形成閉環
"""

import os
import re
from typing import List, Dict, Tuple

# 配置
REPO_URL = "https://github.com/RC918/morningai-mvp"
DOCS_DIR = "docs"
SOURCE_DIRS = ["apps/api/src", "apps/web/src", ".github/workflows"]
FILE_EXTENSIONS = [".py", ".jsx", ".yml", ".md"]

# 正則表達式，用於匹配文檔中的鏈接標記
# 格式：[link-to: path/to/file.py#L10-L20]
LINK_REGEX = re.compile(r"\b(link-to):\s*([\w\/\.\-]+)(?:#L(\d+)(?:-L(\d+))?)?\b")

def find_files_to_process(directories: List[str], extensions: List[str]) -> List[str]:
    """查找需要處理的源文件和文檔文件"""
    files = []
    for directory in directories:
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if any(filename.endswith(ext) for ext in extensions):
                    files.append(os.path.join(root, filename))
    return files

def generate_permalink(file_path: str, start_line: int = None, end_line: int = None) -> str:
    """生成 GitHub 永久鏈接"""
    # 獲取當前 commit hash (模擬)
    # 在實際 CI 環境中，應該從環境變數獲取
    try:
        commit_hash = os.popen("git rev-parse HEAD").read().strip()
    except:
        commit_hash = "main"  # Fallback
    
    link = f"{REPO_URL}/blob/{commit_hash}/{file_path}"
    
    if start_line:
        link += f"#L{start_line}"
        if end_line and end_line > start_line:
            link += f"-L{end_line}"
            
    return link

def process_file_content(content: str) -> Tuple[str, List[Dict]]:
    """處理文件內容，替換鏈接標記並記錄鏈接"""
    updated_content = content
    links_found = []
    
    for match in LINK_REGEX.finditer(content):
        full_match = match.group(0)
        target_path = match.group(2)
        start_line = int(match.group(3)) if match.group(3) else None
        end_line = int(match.group(4)) if match.group(4) else None
        
        # 生成永久鏈接
        permalink = generate_permalink(target_path, start_line, end_line)
        
        # 替換為 Markdown 鏈接
        # 格式：[path/to/file.py#L10-L20](permalink)
        link_text = f"{target_path}"
        if start_line:
            link_text += f"#L{start_line}"
            if end_line:
                link_text += f"-L{end_line}"
        
        markdown_link = f"[`{link_text}`]({permalink})"
        
        updated_content = updated_content.replace(full_match, markdown_link)
        
        links_found.append({
            "original_text": full_match,
            "target_path": target_path,
            "start_line": start_line,
            "end_line": end_line,
            "permalink": permalink,
            "markdown_link": markdown_link
        })
        
    return updated_content, links_found

def main():
    """主函數"""
    print("Starting Docs ↔ Implementation linking process...")
    
    # 查找所有文檔文件
    doc_files = find_files_to_process([DOCS_DIR], [".md"])
    
    if not doc_files:
        print("No documentation files found in 'docs' directory. Creating a sample file.")
        os.makedirs(DOCS_DIR, exist_ok=True)
        sample_doc_path = os.path.join(DOCS_DIR, "sample_doc.md")
        with open(sample_doc_path, "w", encoding="utf-8") as f:
            f.write("# Sample Documentation\n\n")
            f.write("This is a sample documentation file.\n\n")
            f.write("Here is a link to a specific function: `link-to: apps/api/src/main.py#L20-L30`\n")
            f.write("And a link to a workflow file: `link-to: .github/workflows/ci-check.yml`\n")
        doc_files.append(sample_doc_path)

    total_links_updated = 0
    
    for doc_file in doc_files:
        print(f"\nProcessing document: {doc_file}")
        
        try:
            with open(doc_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            updated_content, links_found = process_file_content(content)
            
            if links_found:
                print(f"  Found {len(links_found)} links to update.")
                
                # 寫回更新後的內容
                with open(doc_file, "w", encoding="utf-8") as f:
                    f.write(updated_content)
                
                for link in links_found:
                    print(f"    - Updated: {link['original_text']} -> {link['markdown_link']}")
                
                total_links_updated += len(links_found)
            else:
                print("  No links to update in this file.")
                
        except Exception as e:
            print(f"  Error processing file {doc_file}: {e}")
            
    print(f"\nProcess finished. Total links updated: {total_links_updated}")

if __name__ == "__main__":
    main()
