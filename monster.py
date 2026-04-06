import pygame
import random
import os
import math

class Monster:
    def __init__(self, world_x, initial_ground_y, m_type):
        self.m_type = m_type
        self.world_x = world_x
        
        self.frames = []
        self.current_frame = 0
        self.animation_speed = 0.15
        
        self.load_sprites()
        if self.frames:
            self.image = self.frames[0]
            self.rect = self.image.get_rect()
            self.rect.centerx = world_x # Will be shifted by screen later in display
            self.rect.top = initial_ground_y - self.image.get_height()
        else:
            self.image = pygame.Surface((40, 40))
            self.image.fill((255, 0, 0))
            self.rect = pygame.Rect(0, initial_ground_y - 40, 40, 40)
            self.rect.centerx = world_x
            
        self.vy = 0
        if m_type == "wolf":
            self.vx = 0
        elif m_type == "scorpion":
            self.vx = -100
        elif m_type == "ice_golem":
            self.vx = 100 # Moves slower than the camera
        else:
            self.vx = 0
            
    def load_sprites(self):
        path = f"assets/enemies/{self.m_type}/"
        if os.path.exists(path):
            for file in sorted(os.listdir(path)):
                if file.endswith('.png'):
                    img = pygame.image.load(os.path.join(path, file)).convert_alpha()
                    img = pygame.transform.flip(img, True, False)
                    self.frames.append(img)
                    
    def animate(self):
        if not self.frames: return
        self.current_frame += self.animation_speed
        if self.current_frame >= len(self.frames):
            self.current_frame = 0
        self.image = self.frames[int(self.current_frame)]

    def move(self, dt, camera_offset, get_ground_height):
        # Move on world map
        self.world_x += self.vx * dt
        
        # Project to screen
        self.rect.centerx = self.world_x - camera_offset
        
        current_ground_y = get_ground_height(self.world_x)
        
        if current_ground_y is not None:
            if self.m_type == "scorpion":
                self.vy += 1500 * dt
                self.rect.y += self.vy * dt
                if self.rect.bottom >= current_ground_y:
                    self.rect.bottom = current_ground_y
                    self.vy = random.uniform(-400, -200)
            else:
                self.rect.bottom = current_ground_y
                self.vy = 0
        else:
            # No ground: Monster falls
            self.vy += 1500 * dt
            self.rect.y += self.vy * dt

    def update(self, dt, camera_offset, get_ground_height):
        self.animate()
        self.move(dt, camera_offset, get_ground_height)
                
    def draw(self, surface, camera):
        zoom = camera.zoom
        offset_y = (surface.get_height() * 0.6) - camera.y * zoom
        
        # Scale world relative to focal 100
        screen_x = (self.rect.x - 100) * zoom + 100
        screen_y = self.rect.y * zoom + offset_y
        
        if self.image:
            scaled_img = pygame.transform.scale(self.image, (int(self.rect.width * zoom), int(self.rect.height * zoom)))
            surface.blit(scaled_img, (int(screen_x), int(screen_y)))

class MonsterManager:
    def __init__(self):
        self.monsters = []
        self.spawn_timer = 0
        self.final_chest = None
        
    def reset(self):
        self.monsters.clear()
        self.spawn_timer = 0
        self.final_chest = None
        
    def update(self, dt, current_biome, current_speed, camera_offset, get_ground_height, start_phase=False):
        self.spawn_timer -= dt
        if self.spawn_timer <= 0 and not start_phase and not self.final_chest:
            self.spawn(current_biome, camera_offset, get_ground_height)
            base_time = 1.0 + (300 / current_speed)
            self.spawn_timer = base_time + random.uniform(0.1, 1.2)
            
        for m in self.monsters:
            m.update(dt, camera_offset, get_ground_height)
            
        if self.final_chest:
            self.final_chest.update(camera_offset)
            
        self.monsters = [m for m in self.monsters if m.rect.right > 0 and m.rect.top < 1200]
        
    def spawn(self, biome, camera_offset, get_ground_height):
        m_type = random.choice(biome.enemy_types)
        spawn_screen_x = 850
        world_x = spawn_screen_x + camera_offset
        initial_ground_y = get_ground_height(world_x)
        if initial_ground_y is None: 
            return # Don't spawn on gaps
            
        m = Monster(world_x, initial_ground_y, m_type) # spawn with world_x
        self.monsters.append(m)
        
    def spawn_final_chest(self, world_x, ground_y):
        if not self.final_chest:
            self.final_chest = Chest(world_x, ground_y)

    def check_collision(self, player_rect):
        if self.final_chest and self.final_chest.rect.colliderect(player_rect):
            self.final_chest.opened = True
            return "ENDING"

        for m in self.monsters:
            # simple AABB
            if m.rect.colliderect(player_rect):
                return True
        return False
        
    def draw(self, surface, camera):
        for m in self.monsters:
            m.draw(surface, camera)
        if self.final_chest:
            self.final_chest.draw(surface, camera)

class Chest:
    def __init__(self, world_x, ground_y):
        self.world_x = world_x
        self.ground_y = ground_y
        self.width = 60
        self.height = 50
        self.rect = pygame.Rect(0, ground_y - self.height, self.width, self.height)
        self.rect.centerx = world_x
        self.opened = False
        self.glow_timer = 0
        
    def update(self, camera_offset):
        self.rect.centerx = self.world_x - camera_offset
        self.glow_timer += 0.05
        
    def draw(self, surface, camera):
        zoom = camera.zoom
        offset_y = (surface.get_height() * 0.6) - camera.y * zoom
        
        # Scale world relative to focal 100
        screen_x = (self.rect.x - 100) * zoom + 100
        screen_y = self.rect.y * zoom + offset_y
        scaled_w = int(self.rect.width * zoom)
        scaled_h = int(self.rect.height * zoom)
        
        # 1. Pulsing Glow (Scaled)
        pulse = math.sin(self.glow_timer) * 10 * zoom
        glow_size = (120 * zoom) + pulse
        glow_surf = pygame.Surface((int(glow_size), int(glow_size)), pygame.SRCALPHA)
        color = (255, 255, 100, 80) if not self.opened else (100, 255, 100, 50)
        pygame.draw.circle(glow_surf, color, (int(glow_size//2), int(glow_size//2)), int(glow_size//2.5))
        surface.blit(glow_surf, (int(screen_x + scaled_w/2 - glow_size//2), int(screen_y + scaled_h/2 - glow_size//2)), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # 2. Chest Body (Scaled)
        body_color = (139, 69, 19) # Golden wood
        if self.opened: body_color = (80, 40, 10)
        
        rect_scaled = pygame.Rect(int(screen_x), int(screen_y), scaled_w, scaled_h)
        pygame.draw.rect(surface, body_color, rect_scaled, border_radius=max(1, int(3 * zoom)))
        pygame.draw.rect(surface, (0, 0, 0), rect_scaled, max(1, int(2 * zoom)), border_radius=max(1, int(3 * zoom)))
        
        # Detail: Lid (Scaled)
        lid_h = int(15 * zoom)
        lid_rect = pygame.Rect(int(screen_x), int(screen_y), scaled_w, lid_h)
        if self.opened:
            lid_rect.y -= int(10 * zoom)
            # Draw treasures inside (Scaled)
            pygame.draw.circle(surface, (255, 215, 0), (int(screen_x + scaled_w/2 - 10*zoom), int(screen_y + 10*zoom)), int(5*zoom))
            pygame.draw.circle(surface, (255, 215, 0), (int(screen_x + scaled_w/2 + 10*zoom), int(screen_y + 10*zoom)), int(4*zoom))
            pygame.draw.circle(surface, (255, 215, 0), (int(screen_x + scaled_w/2), int(screen_y + 5*zoom)), int(6*zoom))
            
        pygame.draw.rect(surface, (101, 67, 33), lid_rect, border_radius=max(1, int(3 * zoom)))
        pygame.draw.rect(surface, (0, 0, 0), lid_rect, max(1, int(2 * zoom)), border_radius=max(1, int(3 * zoom)))
        
        # Lock (Scaled)
        lock_size = int(10 * zoom)
        lock_rect = pygame.Rect(int(screen_x + scaled_w/2 - lock_size/2), lid_rect.bottom - int(5*zoom), lock_size, lock_size)
        pygame.draw.rect(surface, (212, 175, 55), lock_rect, border_radius=max(1, int(2 * zoom)))
        pygame.draw.rect(surface, (0, 0, 0), lock_rect, max(1, int(1 * zoom)), border_radius=max(1, int(2 * zoom)))
