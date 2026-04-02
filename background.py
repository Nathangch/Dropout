import pygame
import os

class Background:
    def __init__(self, biome_name, layer_paths, speeds):
        self.biome_name = biome_name
        self.layer_paths = layer_paths
        self.layers = []
        self.offsets = []
        self.speeds = speeds
        
    def load_layers(self):
        self.layers = []
        self.offsets = []
        for path in self.layer_paths:
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                self.layers.append(img)
            else:
                # Fallback empty surface
                surface = pygame.Surface((800, 600), pygame.SRCALPHA)
                surface.fill((30, 30, 50)) # Azul escuro neutro em vez de pink
                self.layers.append(surface)
            self.offsets.append(0)
            
    def update(self, world_speed, dt):
        for i in range(len(self.offsets)):
            # Velocidade do parallax = Velocidade do mundo * multiplicador da camada
            self.offsets[i] += world_speed * self.speeds[i] * dt
            
    def draw(self, surface, alpha=255):
        for i, layer in enumerate(self.layers):
            width = layer.get_width()
            if width == 0: continue
            
            x = -(self.offsets[i] % width)
            
            if alpha < 255:
                layer.set_alpha(alpha)
            else:
                layer.set_alpha(255)
            
            # Repetir o desenho para cobrir toda a largura da superfície (importante para o zoom-out)
            while x < surface.get_width():
                surface.blit(layer, (x, 0))
                x += width


class BackgroundManager:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base = os.path.join(script_dir, "assets", "backgrounds")
        self.backgrounds = {
            "plains": Background("plains", [os.path.join(base, "sky.png"), os.path.join(base, "mountains.png"), os.path.join(base, "trees.png")], [0.2, 0.5, 1.0]),
            "desert": Background("desert", [os.path.join(base, "sky_desert.png"), os.path.join(base, "sun.png"), os.path.join(base, "dunes.png")], [0.0, 0.2, 0.8]),
            "snow": Background("snow", [os.path.join(base, "sky_snow.png"), os.path.join(base, "snow_mountains.png"), os.path.join(base, "fog.png")], [0.2, 0.6, 1.2])
        }
        
        for bg in self.backgrounds.values():
            bg.load_layers()
            
        self.current_bg = self.backgrounds["plains"]
        self.previous_bg = None
        self.transition_progress = 1.0
        
    def set_biome(self, biome_name):
        if self.current_bg.biome_name != biome_name:
            self.previous_bg = self.current_bg
            self.current_bg = self.backgrounds[biome_name]
            self.transition_progress = 0.0
            
    def update(self, world_speed, dt):
        self.current_bg.update(world_speed, dt)
        if self.previous_bg and self.transition_progress < 1.0:
            self.previous_bg.update(world_speed, dt)
            
            # Fade em 2 segundos
            self.transition_progress += 0.5 * dt 
            if self.transition_progress >= 1.0:
                self.transition_progress = 1.0
                self.previous_bg = None
                
    def draw(self, surface):
        if self.previous_bg and self.transition_progress < 1.0:
            # Render anterior sólido e render current com Opacity (Fade-In)
            self.previous_bg.draw(surface, 255)
            alpha = int(255 * self.transition_progress)
            self.current_bg.draw(surface, alpha)
        else:
            self.current_bg.draw(surface, 255)
