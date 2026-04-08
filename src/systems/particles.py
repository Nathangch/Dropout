import pygame
import random

class Particle:
    def __init__(self):
        self.active = False
        
    def spawn(self, x, y, vx, vy, size, lifetime, color, is_world_space=False):
        self.active = True
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
        self.is_world_space = is_world_space

    def update(self, dt):
        if not self.active: return
        self.x += self.vx * 60 * dt
        self.y += self.vy * 60 * dt
        self.lifetime -= 60 * dt
        if self.lifetime <= 0:
            self.active = False

    def draw(self, screen, camera, camera_offset=0):
        if not self.active: return
        zoom = camera.zoom
        
        if self.is_world_space:
            display_x = (self.x - camera_offset - 100) * zoom + 100
            display_y = (self.y - camera.y) * zoom + (screen.get_height() * 0.8)
        else:
            display_x = (self.x - 100) * zoom + 100
            display_y = (self.y - (screen.get_height() * 0.8)) * zoom + (screen.get_height() * 0.8)
            
        ratio = self.lifetime / self.max_lifetime
        if ratio <= 0: return
        
        # Scaling based on lifetime simulates fading intrinsically without expensive Surface SRCALPHA allocation loops
        scaled_size = max(1, int(self.size * zoom * ratio))
        pygame.draw.circle(screen, self.color, (int(display_x), int(display_y)), scaled_size)

class ParticleManager:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.max_particles = 400
        self.pool = [Particle() for _ in range(self.max_particles)]
        self.spawn_timer = 0
        
    def _get_free_particle(self):
        for p in self.pool:
            if not p.active: return p
        return None

    def spawn_particle(self, biome_name, camera_offset=0, camera_y=0):
        if biome_name == "snow":
            p = self._get_free_particle()
            if p:
                x, y = random.randint(0, self.width), -10
                vx, vy = random.uniform(-0.5, 0.5), random.uniform(1, 2.5)
                p.spawn(x, y, vx, vy, random.randint(1, 3), random.randint(200, 400), (255, 255, 255))

        elif biome_name == "avalanche":
            for _ in range(25):
                p = self._get_free_particle()
                if not p: break
                wx = camera_offset + random.randint(-400, 1000)
                wy = camera_y + random.randint(-600, 400)
                vx = random.uniform(-18, -8) 
                vy = random.uniform(4, 10)
                color = random.choice([(255, 255, 255), (220, 240, 255), (180, 200, 230), (255, 255, 240)])
                size = random.randint(4, 12)
                p.spawn(wx, wy, vx, vy, size, random.randint(40, 90), color, is_world_space=True)

        elif biome_name == "desert":
            p = self._get_free_particle()
            if p:
                x, y = self.width + 10, random.randint(0, self.height)
                vx, vy = random.uniform(-4, -2), random.uniform(-0.5, 0.5)
                p.spawn(x, y, vx, vy, random.randint(1, 2), random.randint(80, 150), (194, 178, 128))

        elif biome_name == "plains":
            p = self._get_free_particle()
            if p:
                x, y = random.randint(0, self.width), random.randint(-10, self.height)
                vx, vy = random.uniform(-1, 0.5), random.uniform(0.2, 1.0)
                p.spawn(x, y, vx, vy, random.randint(1, 3), random.randint(150, 300), (76, 153, 0))

    def spawn_burst(self, x, y, color, count=20):
        for _ in range(count):
            p = self._get_free_particle()
            if not p: break
            p.spawn(x, y, random.uniform(-4, 4), random.uniform(-6, -1), random.randint(3, 7), random.randint(40, 100), color)

    def update(self, dt, biome_name, camera_offset=0, camera_y=0):
        self.spawn_timer += dt
        spawn_rate = 0.015 if biome_name == "avalanche" else 0.05
        if self.spawn_timer > spawn_rate:
            self.spawn_particle(biome_name, camera_offset, camera_y)
            self.spawn_timer = 0
        for p in self.pool: 
            p.update(dt)

    def draw(self, screen, camera, camera_offset=0):
        for p in self.pool:
            p.draw(screen, camera, camera_offset)

