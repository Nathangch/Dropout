import os
import re
import shutil

dirs = ['src/core', 'src/entities', 'src/systems', 'src/ui', 'src/utils']
for d in dirs:
    os.makedirs(d, exist_ok=True)
    init_file = os.path.join(d, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            pass
if not os.path.exists('src/__init__.py'):
    with open('src/__init__.py', 'w') as f:
        pass

moves = {
    'state.py': 'src/core/state.py',
    'player.py': 'src/entities/player.py',
    'monster.py': 'src/entities/monster.py',
    'biome.py': 'src/systems/biome.py',
    'background.py': 'src/systems/background.py',
    'particles.py': 'src/systems/particles.py',
    'ui.py': 'src/ui/ui.py',
    'utils.py': 'src/utils/utils.py'
}

for src_file, dest_file in moves.items():
    if os.path.exists(src_file):
        shutil.move(src_file, dest_file)

def patch_file(filepath):
    if not os.path.exists(filepath): return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    # Regex fixes
    if 'main.py' in filepath:
        if '"src"' not in content:
            # Append path injection cleanly
            def replacer(m):
                # Retain the exact indentation
                indent = m.group(1)
                return f'{indent}import sys\n{indent}import os\n{indent}sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))\n{indent}from core import state'
            content = re.sub(r'^(\s*)import state\b', replacer, content, flags=re.MULTILINE, count=1)
            # Replaces any trailing imports safely
            content = re.sub(r'^(\s*)import state\b', r'\1from core import state', content, flags=re.MULTILINE)
    else:
        # Inside modules
        content = re.sub(r'^(\s*)import state\b', r'\1from core import state', content, flags=re.MULTILINE)

    content = re.sub(r'\bfrom ui import\b', 'from ui.ui import', content)
    content = re.sub(r'\bfrom biome import\b', 'from systems.biome import', content)
    content = re.sub(r'\bfrom player import\b', 'from entities.player import', content)
    content = re.sub(r'\bfrom monster import\b', 'from entities.monster import', content)
    content = re.sub(r'\bfrom background import\b', 'from systems.background import', content)
    content = re.sub(r'\bfrom particles import\b', 'from systems.particles import', content)
    content = re.sub(r'\bfrom utils import\b', 'from utils.utils import', content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

for root, _, files in os.walk('src'):
    for file in files:
        if file.endswith('.py'):
            patch_file(os.path.join(root, file))

patch_file('main.py')
print("Migration done")
