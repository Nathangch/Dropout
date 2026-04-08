import os
import re

def update_file(path, func):
    if not os.path.exists(path): return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = func(content)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_main(c):
    c = c.replace("audio_system['dash'] = load_sound(\"dash.wav\")", 
                  "audio_system['dash'] = load_sound(\"dash.wav\")\n        if audio_system.get('dash'): audio_system['dash'].set_volume(0.2)")
    c = c.replace("elif event.key == pygame.K_x or event.key == pygame.K_LCTRL:", 
                  "elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:")
    patch_pause = """                    if state.current_state == state.GameState.PLAYING:
                        state.current_state = state.GameState.PAUSED
                        try: pygame.mixer.pause()
                        except: pass
                    elif state.current_state == state.GameState.PAUSED:
                        state.current_state = state.GameState.PLAYING
                        try: pygame.mixer.unpause()
                        except: pass"""
    c = re.sub(r'                    if state\.current_state == state\.GameState\.PLAYING:[\s\S]*?state\.current_state = state\.GameState\.PLAYING', patch_pause, c)
    patch_unpause1 = """                if new_state == "RESTART":
                    try: pygame.mixer.unpause()
                    except: pass"""
    c = c.replace('                if new_state == "RESTART":', patch_unpause1)
    patch_unpause2 = """                elif new_state:
                    try: pygame.mixer.unpause()
                    except: pass
                    state.current_state = getattr(state.GameState, new_state)"""
    c = c.replace('                elif new_state:\n                    state.current_state = getattr(state.GameState, new_state)', patch_unpause2)
    return c

update_file('main.py', fix_main)

def fix_player(c):
    c = c.replace('40, 50', '60, 75')
    c = c.replace('spawn_y - 50', 'spawn_y - 75')
    c = c.replace('glide_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_z]', 'glide_pressed = keys[pygame.K_SPACE]')
    return c

update_file('src/entities/player.py', fix_player)

def fix_monster(c):
    c = c.replace('m_type = random.choice(biome.enemy_types)', 'm_type = random.choice(["wolf", "scorpion", "ice_golem"])')
    return c

update_file('src/entities/monster.py', fix_monster)

def fix_biome(c):
    c = c.replace('self.grass_tex = pygame.transform.scale(tex, (w, h))', 
                  'self.grass_tex = pygame.transform.scale(tex, (w, h))\n            \n            self.sand_tex = self.grass_tex.copy()\n            self.sand_tex.fill((220, 180, 80, 255), special_flags=pygame.BLEND_RGBA_MULT)\n            \n            self.snow_tex = self.grass_tex.copy()\n            self.snow_tex.fill((100, 100, 150, 0), special_flags=pygame.BLEND_RGB_ADD)')
    patch_grass1 = """        # Aplicação procedimental do arquivo grama.png no topo do relevo
        tex_to_draw = None
        if biome_name == "plains" and hasattr(self, 'grass_tex') and self.grass_tex: tex_to_draw = self.grass_tex
        elif biome_name == "desert" and hasattr(self, 'sand_tex') and self.sand_tex: tex_to_draw = self.sand_tex
        elif biome_name == "snow" and hasattr(self, 'snow_tex') and self.snow_tex: tex_to_draw = self.snow_tex
        
        if tex_to_draw:
            tex_w = tex_to_draw.get_width()
            tex_h = tex_to_draw.get_height()
            
            for i in range(len(points) - 1):
                px, py = points[i]
                nxt_px, nxt_py = points[i+1]
                slice_w = int(nxt_px - px) + 2
                if slice_w <= 0: continue
                
                world_x = (px - 100) / camera.zoom + 100 + self.camera_offset
                src_x = int(world_x) % tex_w
                
                crop = pygame.Rect(src_x, 0, min(slice_w, tex_w - src_x), tex_h)
                surface.blit(tex_to_draw, (px, py - 3), area=crop)
                
                leftover = slice_w - crop.width
                if leftover > 0:
                    surface.blit(tex_to_draw, (px + crop.width, py - 3), area=pygame.Rect(0, 0, leftover, tex_h))"""
    c = re.sub(r"        # Aplicação procedimental[\s\S]*?leftover, tex_h\)\)", patch_grass1, c)
    return c

update_file('src/systems/biome.py', fix_biome)

def fix_ui(c):
    patch = """        text_surf = self.font.render(self.text, True, text_color)
        shadow_surf = self.font.render(self.text, True, (50, 20, 0))
        
        if text_surf.get_width() > self.rect.width - 20:
            scale = (self.rect.width - 20) / float(text_surf.get_width())
            new_w = int(text_surf.get_width() * scale)
            new_h = int(text_surf.get_height() * scale)
            text_surf = pygame.transform.scale(text_surf, (new_w, new_h))
            shadow_surf = pygame.transform.scale(shadow_surf, (new_w, new_h))
            
        text_rect = text_surf.get_rect(midleft=(icon_x + 25 if self.icon_type else base_rect.x + 20, icon_y))
        if not self.icon_type: text_rect.centerx = base_rect.centerx"""
    c = re.sub(r'        text_surf = self\.font\.render\(self\.text, True, text_color\)[\s\S]*?if not self\.icon_type: text_rect\.centerx = base_rect\.centerx', patch, c)
    return c

update_file('src/ui/ui.py', fix_ui)

print("Batch fixes OK")
