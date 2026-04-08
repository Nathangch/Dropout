import os
import pygame
from utils.utils import resource_path

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
            final_path = resource_path(path)
            if os.path.exists(final_path):
                img = pygame.image.load(final_path).convert_alpha()
                # Escalar perfeitamente imagens pixel art / variadas para cobrir a altura exata da tela (600)
                if img.get_height() != 600:
                    aspect_ratio = img.get_width() / img.get_height()
                    new_w = int(600 * aspect_ratio)
                    img = pygame.transform.scale(img, (new_w, 600))
                self.layers.append(img)
            else:
                # Fallback empty surface
                surface = pygame.Surface((800, 600), pygame.SRCALPHA)
                surface.fill((255, 0, 255)) # erro visual
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
            
            surface.blit(layer, (x, 0))
            if x + width < surface.get_width():
                surface.blit(layer, (x + width, 0))


class BackgroundManager:
    def __init__(self):
        base = "assets/backgrounds"
        self.backgrounds = {
            "plains": Background("plains", [
                f"{base}/florest/5 - Sky_color.png",
                f"{base}/florest/4 - Cloud_cover_2.png",
                f"{base}/florest/3 - Cloud_cover_1.png",
                f"{base}/florest/2 - Hills.png",
                f"{base}/florest/1 - Foreground_scenery.png"
            ], [0.0, 0.1, 0.3, 0.6, 1.0]),
            "desert": Background("desert", [
                f"{base}/desert/5 - Sky_color.png",
                f"{base}/desert/4 - Cloud_cover_2.png",
                f"{base}/desert/3 - Cloud_cover_1.png",
                f"{base}/desert/2 - Hills.png",
                f"{base}/desert/1 - Foreground_scenery.png"
            ], [0.0, 0.1, 0.3, 0.6, 1.0]),
            "snow": Background("snow", [
                f"{base}/snow/5 - Sky_color.png",
                f"{base}/snow/4 - Cloud_cover_2.png",
                f"{base}/snow/3 - Cloud_cover_1.png",
                f"{base}/snow/2 - Hills.png",
                f"{base}/snow/1 - Foreground_scenery.png"
            ], [0.0, 0.1, 0.3, 0.6, 1.0])
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
