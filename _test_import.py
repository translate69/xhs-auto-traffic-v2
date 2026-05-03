import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
try:
    from core.note_detail import NoteDetailCollector
    print("Import OK")
except SyntaxError as e:
    print(f"SyntaxError: {e}")
except Exception as e:
    print(f"Error: {e}")
