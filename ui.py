import pygame

class Button:
    def __init__(self, x, y, width, height, text, font, bg_color=(200, 200, 200), text_color=(0, 0, 0)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color
        
    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)
        
    def draw(self, surface):
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, (0,0,0), self.rect, 2)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class MenuUI:
    def __init__(self, width, height):
        self.font = pygame.font.Font(None, 48)
        self.btn_iniciar = Button(width//2 - 100, height//2 - 60, 200, 50, "Iniciar Jogo", self.font)
        self.btn_sair = Button(width//2 - 100, height//2 + 20, 200, 50, "Sair", self.font)
        
    def handle_click(self, mouse_pos):
        if self.btn_iniciar.is_clicked(mouse_pos):
            return "STORY"
        if self.btn_sair.is_clicked(mouse_pos):
            return "EXIT"
        return None
        
    def draw(self, surface):
        surface.fill((50, 50, 50))
        title_font = pygame.font.Font(None, 72)
        title_surf = title_font.render("Runner Game", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(surface.get_width()//2, surface.get_height()//4))
        surface.blit(title_surf, title_rect)
        
        self.btn_iniciar.draw(surface)
        self.btn_sair.draw(surface)

class GameOverUI:
    def __init__(self, width, height):
        self.font = pygame.font.Font(None, 48)
        self.btn_reiniciar = Button(width//2 - 100, height//2 - 60, 200, 50, "Reiniciar", self.font)
        self.btn_sair = Button(width//2 - 100, height//2 + 20, 200, 50, "Sair", self.font)
        
    def handle_click(self, mouse_pos):
        if self.btn_reiniciar.is_clicked(mouse_pos):
            return "PLAYING"
        if self.btn_sair.is_clicked(mouse_pos):
            return "EXIT"
        return None
        
    def draw(self, surface):
        # Draw a semi-transparent black layer
        overlay = pygame.Surface((surface.get_width(), surface.get_height()))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        title_font = pygame.font.Font(None, 72)
        title_surf = title_font.render("GAME OVER", True, (255, 50, 50))
        title_rect = title_surf.get_rect(center=(surface.get_width()//2, surface.get_height()//4))
        surface.blit(title_surf, title_rect)
        
        self.btn_reiniciar.draw(surface)
        self.btn_sair.draw(surface)

class EndingUI:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font_text = pygame.font.Font(None, 32)
        self.font_title = pygame.font.Font(None, 64)
        self.font_button = pygame.font.Font(None, 36)
        
        self.btn_reiniciar = Button(width//2 - 120, height - 135, 240, 50, "Jogar Novamente", self.font_button, bg_color=(50, 200, 100), text_color=(255, 255, 255))
        self.btn_sair = Button(width//2 - 120, height - 70, 240, 50, "Sair do Jogo", self.font_button, bg_color=(200, 50, 50), text_color=(255, 255, 255))
        
        self.narrative = [
            "Após atravessar montanhas, nevascas e perigos,",
            "o bode finalmente encontra o artefato perdido.",
            "",
            "A maldição que o fazia cantar...",
            "começa a desaparecer.",
            "",
            "Pela primeira vez em muito tempo,",
            "o silêncio traz paz.",
            "",
            "Sua jornada chega ao fim…",
            "",
            "mas sua lenda apenas começou."
        ]
        self.text_timer = 0
        self.visible_lines = 0

    def handle_click(self, mouse_pos):
        if self.btn_reiniciar.is_clicked(mouse_pos):
            self.text_timer = 0
            self.visible_lines = 0
            return "PLAYING"
        if self.btn_sair.is_clicked(mouse_pos):
            return "EXIT"
        return None

    def draw(self, surface):
        import state # Import inside draw to access global state
        
        # 1. Dark Gradient Overlay with Global Fade
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Use state.fade_alpha to control the overall darkness
        overlay_alpha = max(state.fade_alpha * 0.7, 180) 
        overlay.fill((10, 15, 30, overlay_alpha))
        surface.blit(overlay, (0, 0))
        
        # Draw gradient on top
        for i in range(10):
            grad_alpha = int(min(255, state.fade_alpha) * (i / 10) * 0.5)
            s = pygame.Surface((self.width, self.height // 10), pygame.SRCALPHA)
            s.fill((10, 15, 30, grad_alpha))
            surface.blit(s, (0, i * (self.height // 10)))

        
        # 2. Animated Narrative
        self.text_timer += 1
        if self.text_timer % 40 == 0 and self.visible_lines < len(self.narrative):
            self.visible_lines += 1
            
        # Title with Glow
        title_surf = self.font_title.render("JORNADA CONCLUÍDA", True, (255, 255, 150))
        title_rect = title_surf.get_rect(center=(self.width//2, 80))
        
        # Simple Glow Shadow
        shadow_surf = self.font_title.render("JORNADA CONCLUÍDA", True, (150, 150, 0))
        surface.blit(shadow_surf, (title_rect.x + 2, title_rect.y + 2))
        surface.blit(title_surf, title_rect)
        
        # Lines
        for i in range(self.visible_lines):
            line = self.narrative[i]
            color = (230, 230, 230)
            if "silêncio" in line: color = (150, 200, 255)
            if "lenda" in line: color = (255, 215, 0)
            
            text_surf = self.font_text.render(line, True, color)
            # Ajustado para 130 e espaçamento de 24
            text_rect = text_surf.get_rect(center=(self.width//2, 130 + i * 24))
            
            # Fade in effect for the last visible line
            if i == self.visible_lines - 1:
                alpha = min(255, (self.text_timer % 40) * 8)
                text_surf.set_alpha(alpha)
                
            surface.blit(text_surf, text_rect)
            
        # 3. Buttons (only show if narrative is mostly done)
        if self.visible_lines >= len(self.narrative) - 1:
            self.btn_reiniciar.draw(surface)
            self.btn_sair.draw(surface)

class StoryUI:
    def __init__(self, width, height, font_text, font_title, font_btn):
        self.width = width
        self.height = height
        self.font_text = font_text
        self.font_title = font_title
        self.font_btn = font_btn
        
        self.btn_comecar = Button(width//2 - 140, height - 100, 280, 50, "Pressione para Jogar", self.font_btn, bg_color=(50, 200, 100), text_color=(255, 255, 255))
        
        self.story = [
            "Você provavelmente já ouviu falar de mim...",
            "Eu sou Japeth, o bode das montanhas.",
            "",
            "Há muito tempo, fui amaldiçoado por uma bruxa,",
            "e agora sou condenada a cantar tudo o que digo.",
            "ISSO MESMO... TUDO!",
            "",
            "Minha única esperança é encontrar o 'Berrante Silencioso',",
            "escondido além das neves eternas.",
            "",
            "Eu preciso correr, saltar e desviar de perigos...",
            "antes que minha voz desapareça para sempre!",
            "",
            "Ajude-me a quebrar essa maldição musical!"
        ]
        
    def handle_click(self, mouse_pos):
        if self.btn_comecar.is_clicked(mouse_pos):
            return "PLAYING"
        return None
        
    def draw(self, surface):
        surface.fill((20, 25, 40)) # Tom escuro azulado
        
        # Desenhar borda decorativa
        pygame.draw.rect(surface, (255, 255, 200), (40, 40, self.width - 80, self.height - 80), 3)
        
        title_surf = self.font_title.render("A MISSÃO DE JAPETH", True, (255, 255, 100))
        title_rect = title_surf.get_rect(center=(self.width//2, 80))
        surface.blit(title_surf, title_rect)
        
        for i, line in enumerate(self.story):
            color = (230, 230, 230)
            if "cantando" in line or "cantar" in line or "musica" in line: color = (150, 200, 255)
            if "Japeth" in line: color = (255, 215, 100)
            
            text_surf = self.font_text.render(line, True, color)
            # Iniciando em 135 e espaçamento de 24 para garantir o encaixe
            text_rect = text_surf.get_rect(center=(self.width//2, 135 + i * 24))
            surface.blit(text_surf, text_rect)
            
        self.btn_comecar.draw(surface)
