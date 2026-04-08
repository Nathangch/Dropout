import pygame
from core import state
from utils.utils import resource_path

def draw_wooden_panel(surface, rect, alpha=255):
    panel_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (110, 50, 20, alpha), (0, 0, rect.width, rect.height), border_radius=15)
    pygame.draw.rect(panel_surf, (150, 75, 30, alpha), (5, 5, rect.width-10, rect.height-10), border_radius=10)
    pygame.draw.rect(panel_surf, (80, 30, 10, alpha), (0, 0, rect.width, rect.height), 4, border_radius=15)
    surface.blit(panel_surf, rect.topleft)

class WoodenButton:
    def __init__(self, x, y, width, height, text, font, icon_type=None, theme='brown', is_primary=False):
        self.base_rect = pygame.Rect(x, y, width, height)
        self.rect = self.base_rect.copy()
        self.text = text
        self.font = font
        self.icon_type = icon_type
        self.theme = theme
        self.is_hovered = False
        self.is_primary = is_primary
        self.hover_progress = 0.0
        self.time = 0.0
        self.last_time = None
        
    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)
        
    def draw(self, surface, mouse_pos):
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
        
        offset_y = 2 if self.is_hovered else 0
        
        if self.theme == 'red':
            shadow_color, base_color, top_color = (60, 10, 10), (180, 40, 40) if not self.is_hovered else (220, 60, 60), (220, 80, 80) if not self.is_hovered else (255, 100, 100)
        elif self.theme == 'green':
            shadow_color, base_color, top_color = (10, 50, 10), (40, 150, 40) if not self.is_hovered else (60, 180, 60), (80, 190, 80) if not self.is_hovered else (100, 220, 100)
        else: # brown
            shadow_color, base_color, top_color = (60, 30, 10), (139, 69, 19) if not self.is_hovered else (160, 82, 45), (180, 100, 40) if not self.is_hovered else (205, 133, 63)

        text_color = (255, 245, 220)
        pygame.draw.rect(surface, shadow_color, (base_rect.x, base_rect.y + 4, base_rect.width, base_rect.height), border_radius=15)
        pygame.draw.rect(surface, base_color, (base_rect.x, base_rect.y + offset_y, base_rect.width, base_rect.height), border_radius=15)
        pygame.draw.rect(surface, top_color, (base_rect.x + 4, base_rect.y + 2 + offset_y, base_rect.width - 8, base_rect.height - 10), border_radius=10)

        pygame.draw.circle(surface, (50, 20, 0), (base_rect.x + 15, base_rect.y + base_rect.height//2 + offset_y), 4)
        pygame.draw.circle(surface, (50, 20, 0), (base_rect.right - 15, base_rect.y + base_rect.height//2 + offset_y), 4)

        icon_x = base_rect.x + 35
        icon_y = base_rect.y + base_rect.height//2 + offset_y
        
        if self.icon_type:
            if self.icon_type == 'play':
                pygame.draw.polygon(surface, (255,255,200), [(icon_x-8, icon_y-10), (icon_x-8, icon_y+10), (icon_x+12, icon_y)])
            elif self.icon_type == 'book':
                pygame.draw.rect(surface, (200,220,250), (icon_x-10, icon_y-8, 20, 16), border_radius=2)
                pygame.draw.line(surface, (255,255,255), (icon_x, icon_y-8), (icon_x, icon_y+8), 2)
            elif self.icon_type == 'gear':
                pygame.draw.circle(surface, (200,200,200), (icon_x, icon_y), 8, 3)
                pygame.draw.line(surface, (200,200,200), (icon_x-10, icon_y), (icon_x+10, icon_y), 3)
                pygame.draw.line(surface, (200,200,200), (icon_x, icon_y-10), (icon_x, icon_y+10), 3)
            elif self.icon_type == 'exit' or self.icon_type == 'back':
                pygame.draw.line(surface, (255,100,100), (icon_x-8, icon_y-8), (icon_x+8, icon_y+8), 5)
                pygame.draw.line(surface, (255,100,100), (icon_x-8, icon_y+8), (icon_x+8, icon_y-8), 5)
            elif self.icon_type == 'restart':
                pygame.draw.arc(surface, (255,255,200), (icon_x-10, icon_y-10, 20, 20), 0, 4.7, 3)
                pygame.draw.polygon(surface, (255,255,200), [(icon_x+5, icon_y-2), (icon_x+15, icon_y-2), (icon_x+10, icon_y+8)])

        text_surf = self.font.render(self.text, True, text_color)
        shadow_surf = self.font.render(self.text, True, (50, 20, 0))
        
        available_width = self.rect.width - 80 if self.icon_type else self.rect.width - 20
        
        if text_surf.get_width() > available_width:
            scale = available_width / float(text_surf.get_width())
            new_w = int(text_surf.get_width() * scale)
            new_h = int(text_surf.get_height() * scale)
            text_surf = pygame.transform.scale(text_surf, (new_w, new_h))
            shadow_surf = pygame.transform.scale(shadow_surf, (new_w, new_h))
            
        text_rect = text_surf.get_rect(midleft=(icon_x + 25 if self.icon_type else base_rect.x + 20, icon_y))
        if not self.icon_type: text_rect.centerx = base_rect.centerx
        
        surface.blit(shadow_surf, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text_surf, text_rect)

class Slider:
    def __init__(self, x, y, width, height, text, font, initial_val=0.5):
        self.rect = pygame.Rect(x, y, width, height)
        self.val = initial_val
        self.text = text
        self.font = font
        self.is_dragging = False
        
    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(mouse_pos):
                self.is_dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False
            
        if self.is_dragging or (event.type == pygame.MOUSEMOTION and self.is_dragging):
            rel_x = mouse_pos[0] - self.rect.x
            self.val = max(0.0, min(1.0, rel_x / self.rect.width))
            return True
        return False
            
    def draw(self, surface):
        track_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height//2 - 5, self.rect.width, 10)
        pygame.draw.rect(surface, (60, 30, 10), track_rect, border_radius=5)
        
        fill_width = int(self.rect.width * self.val)
        if fill_width > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height//2 - 5, fill_width, 10)
            pygame.draw.rect(surface, (205, 133, 63), fill_rect, border_radius=5)
            
        knob_x = self.rect.x + fill_width
        knob_y = self.rect.y + self.rect.height//2
        pygame.draw.circle(surface, (100, 50, 20), (knob_x, knob_y + 2), 12)
        pygame.draw.circle(surface, (180, 100, 40), (knob_x, knob_y), 12)
        pygame.draw.circle(surface, (205, 133, 63), (knob_x, knob_y), 10)
        
        text_surf = self.font.render(f"{self.text}: {int(self.val * 100)}%", True, (255, 245, 220))
        shadow_surf = self.font.render(f"{self.text}: {int(self.val * 100)}%", True, (50, 20, 0))
        text_rect = text_surf.get_rect(midbottom=(self.rect.centerx, self.rect.y - 10))
        surface.blit(shadow_surf, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text_surf, text_rect)

class MenuUI:
    def __init__(self, width, height):
        self.font = pygame.font.Font(None, 42)
        self.big_font = pygame.font.Font(None, 56)
        self.giant_font = pygame.font.Font(None, 120)
        btn_w, btn_h = 240, 60
        btn_x = width - btn_w - 70 
        start_y = 150
        gap = 85
        self.btn_iniciar = WoodenButton(btn_x - 10, start_y - 10, btn_w + 20, btn_h + 20, "JOGAR", self.big_font, 'play', 'green', is_primary=True)
        self.btn_tutorial = WoodenButton(btn_x, start_y + gap + 30, btn_w, btn_h, "Tutorial", self.font, 'book', 'brown')
        self.btn_opcoes = WoodenButton(btn_x, start_y + gap*2 + 30, btn_w, btn_h, "Opções", self.font, 'gear', 'brown')
        self.btn_sair = WoodenButton(btn_x, start_y + gap*3 + 30, btn_w, btn_h, "Sair", self.font, 'exit', 'red')
        
        from utils.utils import resource_path
        import os
        bg_path = resource_path("assets/backgrounds/menu_bg.jpg")
        self.bg_image = pygame.image.load(bg_path).convert() if os.path.exists(bg_path) else None
        if self.bg_image: self.bg_image = pygame.transform.scale(self.bg_image, (width, height))
            
    def handle_click(self, mouse_pos):
        if self.btn_iniciar.is_clicked(mouse_pos): return "STORY"
        if self.btn_tutorial.is_clicked(mouse_pos): return "TUTORIAL"
        if self.btn_opcoes.is_clicked(mouse_pos): return "OPTIONS"
        if self.btn_sair.is_clicked(mouse_pos): return "EXIT"
        return None
        
    def draw(self, surface):
        if self.bg_image: surface.blit(self.bg_image, (0, 0))
        else: surface.fill((210, 180, 140))
        
        # Draw game title
        title_text = "DROPOUT"
        title_surf = self.giant_font.render(title_text, True, (255, 230, 100))
        shadow_surf = self.giant_font.render(title_text, True, (50, 20, 0))
        
        t_rect = title_surf.get_rect(midtop=(surface.get_width() // 2, 40))
        
        # Add a subtle floating effect
        import math
        current_time = pygame.time.get_ticks() / 1000.0
        t_rect.y += math.sin(current_time * 2) * 10
        
        surface.blit(shadow_surf, (t_rect.x+6, t_rect.y+6))
        surface.blit(title_surf, t_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        self.btn_iniciar.draw(surface, mouse_pos)
        self.btn_tutorial.draw(surface, mouse_pos)
        self.btn_opcoes.draw(surface, mouse_pos)
        self.btn_sair.draw(surface, mouse_pos)

class OptionsUI:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font = pygame.font.Font(None, 42)
        self.title_font = pygame.font.Font(None, 72)
        self.panel_rect = pygame.Rect(width//2 - 250, height//2 - 200, 500, 400)
        
        self.music_slider = Slider(self.panel_rect.x + 50, self.panel_rect.y + 120, 400, 40, "Música", self.font, state.music_volume)
        self.sfx_slider = Slider(self.panel_rect.x + 50, self.panel_rect.y + 220, 400, 40, "Efeitos Sonoros", self.font, state.sfx_volume)
        self.btn_voltar = WoodenButton(width//2 - 100, self.panel_rect.bottom - 80, 200, 50, "Voltar", self.font, 'back', 'red')
        
    def handle_event(self, event, mouse_pos):
        if self.music_slider.handle_event(event, mouse_pos):
            state.music_volume = self.music_slider.val
            if hasattr(state, 'audio_system'):
                try: pygame.mixer.music.set_volume(state.music_volume)
                except: pass
        if self.sfx_slider.handle_event(event, mouse_pos):
            state.sfx_volume = self.sfx_slider.val
            if hasattr(state, 'audio_system'):
                for key, snd in state.audio_system.items():
                    if isinstance(snd, pygame.mixer.Sound):
                        snd.set_volume(state.sfx_volume)
                        
    def handle_click(self, mouse_pos):
        if self.btn_voltar.is_clicked(mouse_pos): return "MENU"
        return None

    def draw(self, surface):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0,0))
        draw_wooden_panel(surface, self.panel_rect)
        
        title_surf = self.title_font.render("Opções", True, (255, 230, 150))
        shadow = self.title_font.render("Opções", True, (50, 20, 0))
        t_rect = title_surf.get_rect(center=(self.width//2, self.panel_rect.y + 50))
        surface.blit(shadow, (t_rect.x+2, t_rect.y+2))
        surface.blit(title_surf, t_rect)
        
        self.music_slider.draw(surface)
        self.sfx_slider.draw(surface)
        self.btn_voltar.draw(surface, pygame.mouse.get_pos())

class TutorialUI:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 64)
        self.panel_rect = pygame.Rect(width//2 - 300, height//2 - 220, 600, 440)
        self.btn_voltar = WoodenButton(width//2 - 100, self.panel_rect.bottom - 70, 200, 50, "Ciente!", self.font, 'play', 'green')
        self.lines = [
            "OBJETIVO:",
            " - Encontre o Berrante Silencioso para",
            "   curar a sua maldição musical!",
            "",
            "CONTROLES:",
            " - [ ESPAÇO ] ou [ SETA CIMA ] para Pular.",
            "   (Você pode dar pulo duplo no ar!)",
            " - Segure [ ESPAÇO ] no ar para Planar.",
            " - [ SHIFT ] para usar impulso (Dash)."
        ]
        
    def handle_click(self, mouse_pos):
        if self.btn_voltar.is_clicked(mouse_pos): return "MENU"
        return None
        
    def draw(self, surface):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0,0))
        draw_wooden_panel(surface, self.panel_rect)
        
        title_surf = self.title_font.render("Tutorial", True, (255, 230, 150))
        shadow = self.title_font.render("Tutorial", True, (50, 20, 0))
        t_rect = title_surf.get_rect(center=(self.width//2, self.panel_rect.y + 40))
        surface.blit(shadow, (t_rect.x+2, t_rect.y+2))
        surface.blit(title_surf, t_rect)
        
        for i, line in enumerate(self.lines):
            c = (255,255,255) if not line.startswith(" -") else (200,230,255)
            s = self.font.render(line, True, c)
            sh = self.font.render(line, True, (50,20,0))
            r = s.get_rect(topleft=(self.panel_rect.x + 40, self.panel_rect.y + 90 + i*28))
            surface.blit(sh, (r.x+1, r.y+1))
            surface.blit(s, r)
            
        self.btn_voltar.draw(surface, pygame.mouse.get_pos())

class PauseUI:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font = pygame.font.Font(None, 42)
        self.title_font = pygame.font.Font(None, 72)
        self.panel_rect = pygame.Rect(width//2 - 150, height//2 - 180, 300, 360)
        self.btn_resume = WoodenButton(width//2 - 110, self.panel_rect.y + 100, 220, 55, "Continuar", self.font, 'play', 'green')
        self.btn_restart = WoodenButton(width//2 - 110, self.panel_rect.y + 175, 220, 55, "Reiniciar", self.font, 'restart', 'brown')
        self.btn_menu = WoodenButton(width//2 - 110, self.panel_rect.y + 250, 220, 55, "Menu Inicial", self.font, 'back', 'red')
        
    def handle_click(self, mouse_pos):
        if self.btn_resume.is_clicked(mouse_pos): return "PLAYING"
        if self.btn_restart.is_clicked(mouse_pos): return "RESTART"
        if self.btn_menu.is_clicked(mouse_pos): return "MENU"
        return None
        
    def draw(self, surface):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0,0))
        draw_wooden_panel(surface, self.panel_rect)
        
        title_surf = self.title_font.render("PAUSADO", True, (255, 230, 150))
        shadow = self.title_font.render("PAUSADO", True, (50, 20, 0))
        t_rect = title_surf.get_rect(center=(self.width//2, self.panel_rect.y + 50))
        surface.blit(shadow, (t_rect.x+2, t_rect.y+2))
        surface.blit(title_surf, t_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        self.btn_resume.draw(surface, mouse_pos)
        self.btn_restart.draw(surface, mouse_pos)
        self.btn_menu.draw(surface, mouse_pos)

class GameOverUI:
    def __init__(self, width, height):
        self.font = pygame.font.Font(None, 48)
        self.title_font = pygame.font.Font(None, 72)
        self.panel_rect = pygame.Rect(width//2 - 200, height//2 - 150, 400, 300)
        self.btn_reiniciar = WoodenButton(width//2 - 140, self.panel_rect.y + 120, 280, 55, "Nova Partida", self.font, 'restart', 'green')
        self.btn_sair = WoodenButton(width//2 - 140, self.panel_rect.y + 200, 280, 55, "Menu Inicial", self.font, 'back', 'red')
        
    def handle_click(self, mouse_pos):
        if self.btn_reiniciar.is_clicked(mouse_pos): return "PLAYING"
        if self.btn_sair.is_clicked(mouse_pos): return "MENU"
        return None
        
    def draw(self, surface):
        overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        draw_wooden_panel(surface, self.panel_rect)
        
        title_surf = self.title_font.render("FIM DA LINHA", True, (255, 100, 100))
        shadow = self.title_font.render("FIM DA LINHA", True, (50, 0, 0))
        t_rect = title_surf.get_rect(center=(surface.get_width()//2, self.panel_rect.y + 60))
        surface.blit(shadow, (t_rect.x+2, t_rect.y+2))
        surface.blit(title_surf, t_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        self.btn_reiniciar.draw(surface, mouse_pos)
        self.btn_sair.draw(surface, mouse_pos)

class EndingUI:
    def __init__(self, width, height, font_text, font_title, font_button):
        self.width = width
        self.height = height
        self.font_text = font_text
        self.font_title = font_title
        
        self.panel_rect = pygame.Rect(width//2 - 350, 20, 700, 560)
        self.btn_reiniciar = WoodenButton(width//2 - 250, self.panel_rect.bottom - 75, 240, 55, "Jogar Novamente", font_button, 'restart', 'green')
        self.btn_sair = WoodenButton(width//2 + 10, self.panel_rect.bottom - 75, 240, 55, "Menu Inicial", font_button, 'back', 'red')
        
        self.narrative = [
            "Após atravessar montanhas e perigos,",
            "o bode finalmente encontra o artefato.",
            "",
            "A maldição que o fazia cantar...",
            "começa a desaparecer.",
            "",
            "Pela primeira vez, o silêncio traz paz.",
            "Sua jornada chega ao fim…",
            "mas sua lenda apenas começou."
        ]
        self.text_timer = 0
        self.visible_lines = 0

    def handle_click(self, mouse_pos):
        if self.btn_reiniciar.is_clicked(mouse_pos):
            self.text_timer = 0
            self.visible_lines = 0
            return "PLAYING"
        if self.btn_sair.is_clicked(mouse_pos): return "MENU"
        return None

    def draw(self, surface):
        from core import state 
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay_alpha = max(state.fade_alpha * 0.7, 180) 
        overlay.fill((10, 15, 30, overlay_alpha))
        surface.blit(overlay, (0, 0))
        
        draw_wooden_panel(surface, self.panel_rect, alpha=min(255, state.fade_alpha*2))
        
        self.text_timer += 1
        if self.text_timer % 40 == 0 and self.visible_lines < len(self.narrative):
            self.visible_lines += 1
            
        title_surf = self.font_title.render("JORNADA CONCLUÍDA", True, (255, 255, 150))
        shadow = self.font_title.render("JORNADA CONCLUÍDA", True, (150, 150, 0))
        t_rect = title_surf.get_rect(center=(self.width//2, self.panel_rect.y + 60))
        surface.blit(shadow, (t_rect.x+2, t_rect.y+2))
        surface.blit(title_surf, t_rect)
        
        for i in range(self.visible_lines):
            line = self.narrative[i]
            color = (230, 230, 230)
            if "silêncio" in line: color = (150, 200, 255)
            if "lenda" in line: color = (255, 215, 0)
            text_surf = self.font_text.render(line, True, color)
            text_rect = text_surf.get_rect(center=(self.width//2, self.panel_rect.y + 130 + i * 30))
            if i == self.visible_lines - 1:
                text_surf.set_alpha(min(255, (self.text_timer % 40) * 8))
            surface.blit(text_surf, text_rect)
            
        if self.visible_lines >= len(self.narrative) - 1:
            mouse_pos = pygame.mouse.get_pos()
            self.btn_reiniciar.draw(surface, mouse_pos)
            self.btn_sair.draw(surface, mouse_pos)

class StoryUI:
    def __init__(self, width, height, font_text, font_title, font_btn):
        self.width = width
        self.height = height
        self.font_text = font_text
        self.font_title = font_title
        
        self.panel_rect = pygame.Rect(width//2 - 350, height//2 - 250, 700, 500)
        self.btn_comecar = WoodenButton(width//2 - 140, self.panel_rect.bottom - 80, 280, 55, "Pular e Jogar", font_btn, 'play', 'green')
        
        self.story = [
            "Eu sou Japeth, o pequeno bode das montanhas.",
            "",
            "Há muito tempo fui amaldiçoado, e agora",
            "sou condenado a cantar tudo o que digo.",
            "ISSO MESMO... TUDO!",
            "",
            "Minha esperança é achar o 'Berrante Silencioso',",
            "escondido na nevasca final.",
            "",
            "Corra, pule e desvie de perigos...",
            "antes que minha voz acabe para sempre!"
        ]
        
    def handle_click(self, mouse_pos):
        if self.btn_comecar.is_clicked(mouse_pos): return "PLAYING"
        return None
        
    def draw(self, surface):
        surface.fill((20, 25, 40)) 
        draw_wooden_panel(surface, self.panel_rect)
        
        title_surf = self.font_title.render("A MISSÃO DE JAPETH", True, (255, 240, 150))
        shadow = self.font_title.render("A MISSÃO DE JAPETH", True, (80, 40, 0))
        t_rect = title_surf.get_rect(center=(self.width//2, self.panel_rect.y + 50))
        surface.blit(shadow, (t_rect.x+2, t_rect.y+2))
        surface.blit(title_surf, t_rect)
        
        for i, line in enumerate(self.story):
            color = (250, 240, 220)
            if "Japeth" in line: color = (255, 215, 100)
            if "Berrante" in line: color = (200, 255, 200)
            text_surf = self.font_text.render(line, True, color)
            text_rect = text_surf.get_rect(center=(self.width//2, self.panel_rect.y + 110 + i * 26))
            surface.blit(text_surf, text_rect)
            
        mouse_pos = pygame.mouse.get_pos()
        self.btn_comecar.draw(surface, mouse_pos)
