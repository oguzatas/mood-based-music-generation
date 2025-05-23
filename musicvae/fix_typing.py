from typing import Dict, List, Set, Tuple
import re
from pathlib import Path

TYPING_REPLACEMENTS = {
    'list': 'List',
    'dict': 'Dict',
    'tuple': 'Tuple',
    'set': 'Set'
}

def convert_annotations(code: str) -> str:
    # Replace built-in generics with typing generics
    for builtin, typing_version in TYPING_REPLACEMENTS.items():
        # only replace when used as a generic: e.g., List[Path]
        code = re.sub(rf'\b{builtin}\[', f'{typing_version}[', code)
    return code

def ensure_typing_imports(code: str) -> str:
    existing_imports = re.findall(r'from typing import (.+)', code)
    required_imports = set(TYPING_REPLACEMENTS.values())

    already_imported = set()
    for line in existing_imports:
        already_imported.update(name.strip() for name in line.split(','))

    needed_imports = required_imports - already_imported
    if not needed_imports:
        return code

    insert_point = code.find('import')
    import_line = f"from typing import {', '.join(sorted(needed_imports))}\n"
    return code[:insert_point] + import_line + code[insert_point:]

def process_file(file_path: Path):
    code = file_path.read_text(encoding="utf-8")
    new_code = convert_annotations(code)
    new_code = ensure_typing_imports(new_code)
    if new_code != code:
        file_path.write_text(new_code, encoding="utf-8")
        print(f"✅ Updated: {file_path}")

def main():
    project_root = Path(".")  # current directory
    py_files = list(project_root.rglob("*.py"))
    print(f"🔍 Scanning {len(py_files)} Python files...\n")
    for py_file in py_files:
        process_file(py_file)

if __name__ == "__main__":
    main()
