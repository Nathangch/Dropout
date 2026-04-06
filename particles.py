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
        self.spawn_timer += dt
        spawn_rate = 0.015 if biome_name == "avalanche" else 0.05
        if self.spawn_timer > spawn_rate:
            self.spawn_particle(biome_name, camera_offset, camera_y)
            self.spawn_timer = 0
        for p in self.particles: p.update(dt)
        self.particles = [p for p in self.particles if p.lifetime > 0]

    def draw(self, screen, camera, camera_offset=0):
        for p in self.particles:
            p.draw(screen, camera, camera_offset)

