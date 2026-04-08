import os

def update_file(path, replacements):
    if not os.path.exists(path): return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements:
        content = content.replace(old, new)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

update_file('src/entities/player.py', [
    ('60, 75', '40, 50'),
    ('spawn_y - 75', 'spawn_y - 50'),
    ('* 0.6)', '* 0.8)')
])

update_file('src/entities/monster.py', [
    ('* 0.6)', '* 0.8)')
])

update_file('src/systems/particles.py', [
    ('* 0.6)', '* 0.8)')
])

print("Scale fixed successfully")
