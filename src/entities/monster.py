import pygame
import random
import os
import math
from utils.utils import resource_path

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
            self.rect.centerx = world_x 
            self.rect.top = initial_ground_y - self.image.get_height()
        else:
            size = 30 if m_type == "bird" else 40
            self.image = pygame.Surface((size, size))
            self.image.fill((255, 0, 0))
            self.rect = pygame.Rect(0, initial_ground_y - size, size, size)
            self.rect.centerx = world_x
            
        self.vy = 0
        self.vx = 0
        self.angle = 0 # Adicionado para inclinação
        
    def load_sprites(self):
        path = resource_path(f"assets/enemies/{self.m_type}/")
        if os.path.exists(path):
            files = sorted([f for f in os.listdir(path) if f.endswith('.png')])
            if len(files) == 1:
                sheet = pygame.image.load(os.path.join(path, files[0])).convert_alpha()
                sheet_w, sheet_h = sheet.get_size()
                frame_w = sheet_w // 3
                for i in range(3):
                    frame = sheet.subsurface(pygame.Rect(i * frame_w, 0, frame_w, sheet_h))
                    pass # removemos o flip forçado
                    self.frames.append(frame)
            else:
                for file in files:
                    img = pygame.image.load(os.path.join(path, file)).convert_alpha()
                    pass # removemos o flip forçado
                    self.frames.append(img)
                    
    def animate(self):
        if not self.frames: return
        self.current_frame += self.animation_speed
        if self.current_frame >= len(self.frames):
            self.current_frame = 0
        self.image = self.frames[int(self.current_frame)]

    def apply_gravity_and_ground(self, dt, get_ground_height):
        current_ground_y = get_ground_height(self.world_x)
        if current_ground_y is not None:
            self.rect.bottom = current_ground_y
            self.vy = 0
        else:
            self.vy += 1500 * dt
            self.rect.y += self.vy * dt

    def move(self, dt, camera_offset, get_ground_height):
        pass

    def update(self, dt, camera_offset, get_ground_height, get_ground_slope=None):
        self.animate()
        self.move(dt, camera_offset, get_ground_height, get_ground_slope)

    def draw(self, surface, camera):
        zoom = camera.zoom
        offset_y = (surface.get_height() * 0.8) - camera.y * zoom
        
        # Scale world relative to focal 100
        screen_x = (self.rect.x - 100) * zoom + 100
        screen_y = self.rect.y * zoom + offset_y
        
        if self.image:
            scaled_img = pygame.transform.scale(self.image, (int(self.rect.width * zoom), int(self.rect.height * zoom)))
            surface.blit(scaled_img, (int(screen_x), int(screen_y)))

class Wolf(Monster):
    def __init__(self, world_x, initial_ground_y):
        super().__init__(world_x, initial_ground_y, "wolf")
        self.vx = -120 
        if self.frames:
            # Removido flip True (estava invertido)
            self.frames = [pygame.transform.scale(f, (int(f.get_width()*0.55), int(f.get_height()*0.55))) for f in self.frames]
            self.image = self.frames[0]
            self.rect = self.image.get_rect()
            self.rect.centerx = world_x
            self.rect.bottom = initial_ground_y

    def move(self, dt, camera_offset, get_ground_height, get_ground_slope=None):
        self.world_x += self.vx * dt
        self.rect.centerx = self.world_x - camera_offset
        self.apply_gravity_and_ground(dt, get_ground_height)
        
        # Acompanhar curvatura do terreno
        if get_ground_slope:
            slope = get_ground_slope(self.world_x)
            target_angle = math.degrees(math.atan2(slope, 1))
            self.angle += (target_angle - self.angle) * 10 * dt

    def draw(self, surface, camera):
        zoom = camera.zoom
        offset_y = (surface.get_height() * 0.8) - camera.y * zoom
        screen_x = (self.rect.x - 100) * zoom + 100
        screen_y = self.rect.y * zoom + offset_y
        
        if self.image:
            # Escalonar
            draw_w = int(self.rect.width * zoom)
            draw_h = int(self.rect.height * zoom)
            scaled_img = pygame.transform.scale(self.image, (draw_w, draw_h))
            
            # Rotacionar com base no slope
            rotated_img = pygame.transform.rotate(scaled_img, -self.angle)
            rot_rect = rotated_img.get_rect(center=(int(screen_x + draw_w/2), int(screen_y + draw_h/2)))
            surface.blit(rotated_img, rot_rect.topleft)

class IceGolem(Monster):
    def __init__(self, world_x, initial_ground_y):
        super().__init__(world_x, initial_ground_y, "ice_golem")
        self.vx = -160 # Agora ele anda para frente (esquerda)
        if self.frames:
            # Removido flip (estava invertido)
            self.image = self.frames[0]

    def move(self, dt, camera_offset, get_ground_height, get_ground_slope=None):
        self.world_x += self.vx * dt
        self.rect.centerx = self.world_x - camera_offset
        self.apply_gravity_and_ground(dt, get_ground_height)

class Scorpion(Monster):
    def __init__(self, world_x, initial_ground_y):
        super().__init__(world_x, initial_ground_y, "scorpion")
        self.vx = -100
        if self.frames:
            # Escalonar conforme solicitado (sem inverter)
            self.frames = [pygame.transform.scale(f, (int(f.get_width()*0.55), int(f.get_height()*0.55))) for f in self.frames]
            self.image = self.frames[0]
            self.rect = self.image.get_rect()
            self.rect.centerx = world_x
            self.rect.bottom = initial_ground_y

    def move(self, dt, camera_offset, get_ground_height, get_ground_slope=None):
        self.world_x += self.vx * dt
        self.rect.centerx = self.world_x - camera_offset
        current_ground_y = get_ground_height(self.world_x)
        if current_ground_y is not None:
            self.vy += 1500 * dt
            self.rect.y += self.vy * dt
            if self.rect.bottom >= current_ground_y:
                self.rect.bottom = current_ground_y
                self.vy = random.uniform(-400, -200)
        else:
            self.vy += 1500 * dt
            self.rect.y += self.vy * dt
            
class MonsterFactory:
    @staticmethod
    def create(m_type, world_x, initial_ground_y):
        if m_type == "wolf": return Wolf(world_x, initial_ground_y)
        if m_type == "scorpion": return Scorpion(world_x, initial_ground_y)
        if m_type == "ice_golem": return IceGolem(world_x, initial_ground_y)
        return Wolf(world_x, initial_ground_y)

class MonsterManager:
    def __init__(self):
        self.monsters = []
        self.spawn_timer = 0
        self.final_chest = None
        
    def reset(self):
        self.monsters.clear()
        self.spawn_timer = 0
        self.final_chest = None
        
    def update(self, dt, current_biome, current_speed, camera_offset, get_ground_height, get_ground_slope=None, start_phase=False):
        self.spawn_timer -= dt
        if self.spawn_timer <= 0 and not start_phase and not self.final_chest:
            self.spawn(current_biome, camera_offset, get_ground_height)
            base_time = 1.0 + (300 / current_speed)
            self.spawn_timer = base_time + random.uniform(0.1, 1.2)
            
        for m in self.monsters:
            m.update(dt, camera_offset, get_ground_height, get_ground_slope)
            
        if self.final_chest:
            self.final_chest.update(camera_offset)
            
        self.monsters = [m for m in self.monsters if m.rect.right > -100]
        
    def spawn(self, biome, camera_offset, get_ground_height):
        m_type = random.choice(biome.enemy_types)
        spawn_screen_x = 850
        world_x = spawn_screen_x + camera_offset
        initial_ground_y = get_ground_height(world_x)
        if initial_ground_y is None: 
            return # Don't spawn on gaps
            
        m = MonsterFactory.create(m_type, world_x, initial_ground_y)
        self.monsters.append(m)
        
    def spawn_final_chest(self, world_x, ground_y):
        if not self.final_chest:
            self.final_chest = Chest(world_x, ground_y)
            self.monsters.clear() # Limpa inimigos espalhados para nao nascerem em cima do bau

    def check_collision(self, player_rect):
        if self.final_chest and self.final_chest.rect.colliderect(player_rect):
            self.final_chest.opened = True
            return "ENDING"

        for m in self.monsters:
            # Reduz as hitboxes agressivamente pra perdoar pulos raspando (Fairness)
            hitbox = m.rect.inflate(-m.rect.width * 0.5, -m.rect.height * 0.4)
            hitbox.bottom = m.rect.bottom
            if hitbox.colliderect(player_rect):
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
        offset_y = (surface.get_height() * 0.8) - camera.y * zoom
        
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
