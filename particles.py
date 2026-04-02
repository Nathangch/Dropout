import pygame
import random

class Particle:
    def __init__(self, x, y, vx, vy, size, lifetime, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color

    def update(self, dt):
        self.x += self.vx * 60 * dt
        self.y += self.vy * 60 * dt
        self.lifetime -= 60 * dt

    def draw(self, screen):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        if alpha <= 0: return
        
        # Create a tiny surface for the particle with alpha
        # Note: For even better performance with many particles, pre-rendering different sizes/alphas or using individual pixels would be faster.
        # But for 100 particles, this is perfectly fine.
        surf = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (self.size, self.size), self.size)
        screen.blit(surf, (int(self.x - self.size), int(self.y - self.size)))

class ParticleManager:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.particles = []
        self.max_particles = 100
        self.spawn_timer = 0

    def spawn_particle(self, biome_name):
        if len(self.particles) >= self.max_particles:
            return

        if biome_name == "snow":
            x = random.randint(0, self.width)
            y = -10
            vx = random.uniform(-0.5, 0.5)
            vy = random.uniform(1, 2.5)
            size = random.randint(1, 3)
            lifetime = random.randint(200, 400)
            color = (255, 255, 255)
            self.particles.append(Particle(x, y, vx, vy, size, lifetime, color))

        elif biome_name == "desert":
            x = self.width + 10
            y = random.randint(0, self.height)
            vx = random.uniform(-4, -2)
            vy = random.uniform(-0.5, 0.5)
            size = random.randint(1, 2)
            lifetime = random.randint(80, 150)
            color = (194, 178, 128)
            self.particles.append(Particle(x, y, vx, vy, size, lifetime, color))

        elif biome_name == "plains":
            x = random.randint(0, self.width)
            y = random.randint(-10, self.height)
            vx = random.uniform(-1, 0.5)
            vy = random.uniform(0.2, 1.0)
            size = random.randint(1, 3)
            lifetime = random.randint(150, 300)
            color = (76, 153, 0) # Green leaf color
            self.particles.append(Particle(x, y, vx, vy, size, lifetime, color))

    def spawn_burst(self, x, y, color, count=20):
        for _ in range(count):
            vx = random.uniform(-4, 4)
            vy = random.uniform(-6, -1)
            size = random.randint(3, 7)
            lifetime = random.randint(40, 100)
            self.particles.append(Particle(x, y, vx, vy, size, lifetime, color))

    def update(self, dt, biome_name):
        self.spawn_timer += dt
        if self.spawn_timer > 0.05: # Spawn every 50ms approx
            self.spawn_particle(biome_name)
            self.spawn_timer = 0

        for p in self.particles:
            p.update(dt)

        self.particles = [p for p in self.particles if p.lifetime > 0]

    def draw(self, screen):
        for p in self.particles:
            p.draw(screen)

