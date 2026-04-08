import pygame
import random

class Particle:
    def __init__(self, x, y, vx, vy, size, lifetime, color, is_world_space=False):
        self.x = x # Se is_world_space for True, isso é world_x
        self.y = y # Se is_world_space for True, isso é world_y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
        self.is_world_space = is_world_space

    def update(self, dt):
        self.x += self.vx * 60 * dt
        self.y += self.vy * 60 * dt
        self.lifetime -= 60 * dt

    def draw(self, screen, camera, camera_offset=0):
        zoom = camera.zoom
        
        if self.is_world_space:
            # Coordenadas relativas ao mundo e câmera
            display_x = (self.x - camera_offset - 100) * zoom + 100
            display_y = (self.y - camera.y) * zoom + (screen.get_height() * 0.6)
        else:
            # Efeito fixo na tela (paralaxe/clima)
            display_x = (self.x - 100) * zoom + 100
            display_y = (self.y - (screen.get_height() * 0.6)) * zoom + (screen.get_height() * 0.6)
            
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        if alpha <= 0: return
        
        scaled_size = max(1, int(self.size * zoom))
        
        # Desenho
        if alpha < 200:
            surf = pygame.Surface((scaled_size*2, scaled_size*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, alpha), (scaled_size, scaled_size), scaled_size)
            screen.blit(surf, (int(display_x - scaled_size), int(display_y - scaled_size)))
        else:
            pygame.draw.circle(screen, self.color, (int(display_x), int(display_y)), scaled_size)

class ParticleManager:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.particles = []
        self.max_particles = 400
        self.spawn_timer = 0
        self.current_biome = "plains"
        
        # Pre-render overlays for performance
        self.overlays = {
            "desert": pygame.Surface((width, height), pygame.SRCALPHA),
            "plains": pygame.Surface((width, height), pygame.SRCALPHA),
            "snow": pygame.Surface((width, height), pygame.SRCALPHA)
        }
        self.overlays["desert"].fill((210, 180, 140, 80)) # Cor de areia transparente
        self.overlays["plains"].fill((220, 230, 210, 60)) # Névoa verdeada clara
        self.overlays["snow"].fill((255, 255, 255, 40))   # Névoa de neve leve

    def spawn_particle(self, biome_name, camera_offset=0, camera_y=0):
        if len(self.particles) >= self.max_particles:
            return

        if biome_name == "snow":
            x, y = random.randint(0, self.width), -10
            vx, vy = random.uniform(-0.5, 0.5), random.uniform(1, 2.5)
            self.particles.append(Particle(x, y, vx, vy, random.randint(1, 3), random.randint(200, 400), (255, 255, 255)))

        elif biome_name == "avalanche":
            # Avalanche: Criar uma "parede" de neve vindo de trás/cima
            for _ in range(25): # Densidade extrema
                # Spawna ao redor da câmera, concentrando "atrás" (esquerda) do player
                wx = camera_offset + random.randint(-400, 1000)
                wy = camera_y + random.randint(-600, 400)
                
                # Velocidade alta para um efeito de "blizzard"
                vx = random.uniform(-18, -8) 
                vy = random.uniform(4, 10)
                
                # Cores variadas para profundidade
                color = random.choice([(255, 255, 255), (220, 240, 255), (180, 200, 230), (255, 255, 240)])
                size = random.randint(4, 12) # Partículas maiores para cobrir "buracos" visuais
                self.particles.append(Particle(wx, wy, vx, vy, size, random.randint(40, 90), color, is_world_space=True))

        elif biome_name == "desert":
            x, y = self.width + 10, random.randint(0, self.height)
            vx, vy = random.uniform(-4, -2), random.uniform(-0.5, 0.5)
            self.particles.append(Particle(x, y, vx, vy, random.randint(1, 2), random.randint(80, 150), (194, 178, 128)))

        elif biome_name == "plains":
            x, y = random.randint(0, self.width), random.randint(-10, self.height)
            vx, vy = random.uniform(-1, 0.5), random.uniform(0.2, 1.0)
            self.particles.append(Particle(x, y, vx, vy, random.randint(1, 3), random.randint(150, 300), (76, 153, 0)))

    def spawn_burst(self, x, y, color, count=20):
        for _ in range(count):
            self.particles.append(Particle(x, y, random.uniform(-4, 4), random.uniform(-6, -1), random.randint(3, 7), random.randint(40, 100), color))

    def update(self, dt, biome_name, camera_offset=0, camera_y=0):
        self.current_biome = biome_name
        self.spawn_timer += dt
        spawn_rate = 0.015 if biome_name == "avalanche" else 0.05
        if self.spawn_timer > spawn_rate:
            self.spawn_particle(biome_name, camera_offset, camera_y)
            self.spawn_timer = 0
        for p in self.particles: p.update(dt)
        self.particles = [p for p in self.particles if p.lifetime > 0]

    def draw(self, screen, camera, camera_offset=0):
        # 1. Desenhar partículas
        for p in self.particles:
            p.draw(screen, camera, camera_offset)
            
        # 2. Desenhar overlays de clima (Tempestade/Névoa)
        import math
        time_factor = pygame.time.get_ticks() * 0.001
        
        if self.current_biome in self.overlays:
            overlay = self.overlays[self.current_biome]
            # Efeito de pulsação na opacidade para parecer dinâmico
            alpha_mod = math.sin(time_factor * 0.5) * 15
            
            # Criar uma cópia temporária se precisarmos mudar o alpha dinamicamente 
            # (ou apenas blit com um valor se for suportado, mas blit surface é mais rápido)
            if self.current_biome == "desert":
                # Tempestade de areia mais intensa
                screen.blit(overlay, (0, 0))
            elif self.current_biome == "plains":
                # Névoa ondulante
                screen.blit(overlay, (0, 0))
            elif self.current_biome == "avalanche":
                # Névoa branca pesada na avalanche
                screen.blit(self.overlays["snow"], (0, 0))
                # Adiciona um segundo overlay para "branquear" mais a tela
                snow_overlay = self.overlays["snow"].copy()
                snow_overlay.set_alpha(100 + int(alpha_mod))
                screen.blit(snow_overlay, (0, 0))

