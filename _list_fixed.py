import json
notes = json.load(open('test/corpus/problem_notes.json', encoding='utf-8'))
for n in notes:
    if n.get('expected') == False and n.get('fixed_at'):
        print(n['note_id'][:12])