import os
import re

class Toolbelt:
    def __init__(self):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def apply_code_changes(self, llm_response):
        """
        Parses Markdown code blocks from LLM and writes them to files.
        Format expected: 
        ### FILE: path/to/file.py
        ```python
        code...
        ```
        """
        # Regex to find file blocks
        pattern = r"### FILE: (.+)\n```\w+\n(.*?)```"
        matches = re.findall(pattern, llm_response, re.DOTALL)
        
        applied_files = []
        for filepath, content in matches:
            # Security: Prevent escaping project root
            full_path = os.path.normpath(os.path.join(self.root_dir, filepath.strip()))
            if not full_path.startswith(self.root_dir):
                print(f"⚠️ Skipped unsafe write: {filepath}")
                continue
                
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content.strip())
            applied_files.append(filepath)
            
        return applied_files

    def capture_screenshot(self, url="http://localhost:3000", output="snapshot.png"):
        """Uses Playwright CLI to capture state."""
        # Note: This requires 'npx playwright' to be available
        cmd = f"npx playwright screenshot --url {url} --path {output} --full-page"
        return cmd
