import os
import re

ui_path = "src/ui/ui.py"
main_path = "main.py"

with open(ui_path, 'r', encoding='utf-8') as f:
    ui_code = f.read()

# 1. Update WoodenButton constructor
ui_code = ui_code.replace("def __init__(self, x, y, width, height, text, font, icon_type=None, theme='brown'):", "def __init__(self, x, y, width, height, text, font, icon_type=None, theme='brown', is_primary=False):")
ui_code = ui_code.replace("self.rect = self.base_rect.copy()", "self.rect = self.base_rect.copy()\n        self.is_primary = is_primary\n        self.hover_progress = 0.0\n        self.time = 0.0\n        self.last_time = None")

# 2. Update WoodenButton draw
old_draw = """    def draw(self, surface, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        offset_y = 2 if self.is_hovered else 0
        base_rect = self.rect.copy()"""

new_draw = """    def draw(self, surface, mouse_pos):
        import math
        current_time = pygame.time.get_ticks() / 1000.0
        if self.last_time is None: self.last_time = current_time
        dt = min(current_time - self.last_time, 0.1)
        self.last_time = current_time
        self.time += dt
        
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        target_hover = 1.0 if self.is_hovered else 0.0
        self.hover_progress += (target_hover - self.hover_progress) * 15.0 * dt
        
        expand = self.hover_progress * 10
        pulse = math.sin(self.time * 5) * 6 if self.is_primary and not self.is_hovered else 0
        
        base_rect = self.base_rect.inflate(expand + pulse, expand + pulse)
        self.rect = base_rect.copy()
        
        offset_y = 2 if self.is_hovered else 0"""

ui_code = ui_code.replace(old_draw, new_draw)

# 3. Update MenuUI constructor
old_menu_init = """    def __init__(self, width, height):
        self.font = pygame.font.Font(None, 42)
        btn_w, btn_h = 220, 55
        btn_x = width - btn_w - 50 
        start_y = 150
        gap = 75
        self.btn_iniciar = WoodenButton(btn_x, start_y, btn_w, btn_h, "Jogar", self.font, 'play', 'green')
        self.btn_tutorial = WoodenButton(btn_x, start_y + gap, btn_w, btn_h, "Tutorial", self.font, 'book', 'brown')
        self.btn_opcoes = WoodenButton(btn_x, start_y + gap*2, btn_w, btn_h, "Opções", self.font, 'gear', 'brown')
        self.btn_sair = WoodenButton(btn_x, start_y + gap*3, btn_w, btn_h, "Sair", self.font, 'exit', 'red')"""

new_menu_init = """    def __init__(self, width, height):
        self.font = pygame.font.Font(None, 42)
        self.big_font = pygame.font.Font(None, 56)
        self.giant_font = pygame.font.Font(None, 120)
        btn_w, btn_h = 240, 60
        btn_x = width - btn_w - 70 
        start_y = 150
        gap = 85
        self.btn_iniciar = WoodenButton(btn_x - 30, start_y - 20, btn_w + 60, btn_h + 30, "JOGAR", self.big_font, 'play', 'green', is_primary=True)
        self.btn_tutorial = WoodenButton(btn_x, start_y + gap + 30, btn_w, btn_h, "Tutorial", self.font, 'book', 'brown')
        self.btn_opcoes = WoodenButton(btn_x, start_y + gap*2 + 30, btn_w, btn_h, "Opções", self.font, 'gear', 'brown')
        self.btn_sair = WoodenButton(btn_x, start_y + gap*3 + 30, btn_w, btn_h, "Sair", self.font, 'exit', 'red')"""

ui_code = ui_code.replace(old_menu_init, new_menu_init)

# 4. Update MenuUI draw to add Title and hide legacy BG
old_menu_draw = """    def draw(self, surface):
        if self.bg_image: surface.blit(self.bg_image, (0, 0))
        else: surface.fill((210, 180, 140))
        
        mouse_pos = pygame.mouse.get_pos()"""

new_menu_draw = """    def draw(self, surface):
        # We rely on main.py rendering parallax now.
        
        # Draw game title
        title_text = "DROPOUT"
        title_surf = self.giant_font.render(title_text, True, (255, 230, 100))
        shadow_surf = self.giant_font.render(title_text, True, (50, 20, 0))
        
        t_rect = title_surf.get_rect(center=(surface.get_width()//2 - 130, surface.get_height()//2 - 50))
        
        # Add a subtle floating effect
        import math
        current_time = pygame.time.get_ticks() / 1000.0
        t_rect.y += math.sin(current_time * 2) * 10
        
        surface.blit(shadow_surf, (t_rect.x+6, t_rect.y+6))
        surface.blit(title_surf, t_rect)
        
        mouse_pos = pygame.mouse.get_pos()"""

ui_code = ui_code.replace(old_menu_draw, new_menu_draw)

with open(ui_path, 'w', encoding='utf-8') as f:
    f.write(ui_code)


# 5. Update main.py MENU loops
with open(main_path, 'r', encoding='utf-8') as f:
    main_code = f.read()

main_logic_menu = """        elif state.current_state == state.GameState.MENU:
            if click_pos:"""

new_main_logic_menu = """        elif state.current_state == state.GameState.MENU:
            bg_manager.set_biome("plains")
            bg_manager.update(50, dt) # Parallax lendo 50px/s fixo no menu
            particle_manager.update(dt, "plains", 0, camera.y)
            
            if click_pos:"""

main_code = main_code.replace(main_logic_menu, new_main_logic_menu)

main_render_menu = """        if state.current_state == state.GameState.MENU:
            menu_ui.draw(screen)"""

new_main_render_menu = """        if state.current_state == state.GameState.MENU:
            bg_manager.draw(screen)
            particle_manager.draw(screen, camera, 0)
            menu_ui.draw(screen)"""
            
main_code = main_code.replace(main_render_menu, new_main_render_menu)

with open(main_path, 'w', encoding='utf-8') as f:
    f.write(main_code)
print("Menu UI Polish finished!")
