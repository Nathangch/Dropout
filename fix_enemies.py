import os

path = 'src/entities/monster.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Invertendo: removo a flag de Flip prévia
text = text.replace("frame = pygame.transform.flip(frame, True, False)", "pass # removemos o flip forçado")
text = text.replace("img = pygame.transform.flip(img, True, False)", "pass # removemos o flip forçado")

# 2. Hitbox menor
old_collision = """        for m in self.monsters:
            # simple AABB
            if m.rect.colliderect(player_rect):"""

new_collision = """        for m in self.monsters:
            # Reduz as hitboxes agressivamente pra perdoar pulos raspando (Fairness)
            hitbox = m.rect.inflate(-m.rect.width * 0.5, -m.rect.height * 0.4)
            hitbox.bottom = m.rect.bottom
            if hitbox.colliderect(player_rect):"""

text = text.replace(old_collision, new_collision)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Hitbox Fix applied!")
