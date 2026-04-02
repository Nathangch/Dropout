import pygame
import math
class Biome:
    def __init__(self, name, bg_color, friction, enemy_types, amplitude, frequency, variation):
        self.name = name
        self.bg_color = bg_color
        self.friction = friction
        self.enemy_types = enemy_types
        self.amplitude = amplitude
        self.frequency = frequency
        self.variation = variation

import random
BIOMES = [
    # Plains: Fluid (Referência)
    Biome("plains", (20, 100, 180), friction=1.0, enemy_types=["wolf"], amplitude=70, frequency=0.003, variation=0.000002),
    # Desert: Suavemente mais ondulado (Diferença mínima para evitar boost)
    Biome("desert", (237, 201, 175), friction=1.0, enemy_types=["scorpion"], amplitude=78, frequency=0.0035, variation=0.000004),
    # Snow: Montanhoso mas controlado
    Biome("snow",   (200, 230, 255), friction=0.5, enemy_types=["ice_golem"], amplitude=90, frequency=0.004, variation=0.000005)
]

class BiomeManager:
    def __init__(self):
        self.biomes = BIOMES
        self.current_idx = 0
        self.time_elapsed = 0
        self.total_time_elapsed = 0
        self.transition_time = 30.0
        
        self.camera_offset = 0
        self.base_height = 400
        
        self.base_speed = 300
        self.max_speed = 700
        self.current_speed = self.base_speed
        
        # SINE WAVE STATE
        self.amplitude = 80
        self.frequency = 0.005
        self.phase = 0
        
        # SEGMENTED TERRAIN STATE
        self.chunk_step = 10
        self.heightmap = []
        self.heightmap_start_x = 0
        self.current_y = self.base_height + 250
        
        # GAPS LOGIC
        self.gap_zones = [] # [(start_x, end_x), ...]
        self.last_gap_gen_x = 0
        
        self.start_phase = True
        self.start_distance_limit = 1800 
        
    def reset(self):
        self.current_idx = 0
        self.time_elapsed = 0
        self.total_time_elapsed = 0
        self.camera_offset = 0
        self.current_speed = self.base_speed
        self.amplitude = 80
        self.frequency = 0.005
        self.phase = 0
        self.gap_zones = []
        self.last_gap_gen_x = 500 # Safe zone
        self.start_phase = True
        
        self._init_terrain()
        
        self._maintain_gaps()
        
    def _init_terrain(self):
        self.heightmap = []
        self.heightmap_start_x = 0
        limit_pts = int(self.start_distance_limit / self.chunk_step)
        for i in range(limit_pts):
            self.heightmap.append(400 + (i * self.chunk_step / self.start_distance_limit) * 250)
        self.current_y = 650

    def _maintain_terrain(self):
        # Maintain heightmap up to camera_offset + 3000
        end_x = self.heightmap_start_x + len(self.heightmap) * self.chunk_step
        while end_x < self.camera_offset + 3000:
            segment_length = random.randint(250, 500)
            
            rand_val = random.random()
            if rand_val < 0.45:
                slope = random.uniform(0.9, 1.3) # Downhill
            elif rand_val < 0.8:
                slope = random.uniform(-0.2, -0.45) # Uphill suavizado
            else:
                slope = random.uniform(-0.1, 0.1) # Flat
                
            future_y = self.current_y + slope * segment_length
            if future_y > 800:
                slope = random.uniform(-0.2, -0.45)
            elif future_y < 100:
                slope = random.uniform(0.9, 1.3)
                
            slope *= random.uniform(0.9, 1.1) # Variation
            
            pts = segment_length // self.chunk_step
            chunk = []
            for i in range(pts):
                chunk.append(self.current_y + slope * (i * self.chunk_step))
                
            self.current_y += slope * pts * self.chunk_step
            self.heightmap.extend(chunk)
            end_x += pts * self.chunk_step
            
        # Smooth the last added items except boundaries using Moving Average
        if len(self.heightmap) > 10:
            last = len(self.heightmap)
            # smooth last 150 elements approx
            start_smooth = max(2, last - 150)
            temp = list(self.heightmap)
            for i in range(start_smooth, last - 2):
                self.heightmap[i] = (temp[i-2] + temp[i-1] + temp[i] + temp[i+1] + temp[i+2]) / 5.0
                
        # Trim old heightmap points
        while len(self.heightmap) > 2 and (self.heightmap_start_x + self.chunk_step) < self.camera_offset - 1000:
            self.heightmap.pop(0)
            self.heightmap_start_x += self.chunk_step

    def _maintain_gaps(self):
        # Gera buracos para os próximos pixels à frente
        while self.last_gap_gen_x < self.camera_offset + 2000:
            # Pula um espaço de terreno sólido
            self.last_gap_gen_x += random.randint(800, 2000)
            
            # Decide se cria um buraco (não cria na start_phase)
            if self.last_gap_gen_x > self.start_distance_limit:
                if random.random() < 0.2: # 20% chance de buraco após o intervalo sólido
                    gap_len = random.randint(200, 400)
                    self.gap_zones.append((self.last_gap_gen_x, self.last_gap_gen_x + gap_len))
                    self.last_gap_gen_x += gap_len
        
        # Limpa gaps antigos
        self.gap_zones = [g for g in self.gap_zones if g[1] > self.camera_offset - 800]
        
    def update(self, dt):
        self.time_elapsed += dt
        self.total_time_elapsed += dt
        
        # 0. BIOME TRANSITION & SINE INTERPOLATION
        if self.time_elapsed > self.transition_time:
            self.time_elapsed -= self.transition_time
            self.current_idx = (self.current_idx + 1) % len(self.biomes)
            
        target_biome = self.get_current()
        
        # Suavização EXTREMAMENTE LENTA dos parâmetros para evitar picos de momentum
        # O relevo muda ao longo de quase 30 segundos agora
        lerp_speed = 0.1 * dt
        self.amplitude += (target_biome.amplitude - self.amplitude) * lerp_speed
        self.frequency += (target_biome.frequency - self.frequency) * lerp_speed
            
        # VARIAÇÃO PROCEDURAL (Procedural Drift)
        # Extremamente lenta para manter a fluidez total
        if abs(self.amplitude - target_biome.amplitude) < 5:
            # Variação sutil a cada biome/time
            self.frequency += random.uniform(-target_biome.variation, target_biome.variation) * 0.1
        
        # Limitar freq. para evitar serrilhados (LOW FREQUENCY ONLY)
        self.frequency = max(0.002, min(0.005, self.frequency))
        
        # ALONGAR DESCIDAS (FEELING ALTO'S)
        # Se estiver no bioma fluido (Plains) e rápido, alarga as ondas
        if target_biome.name == "plains" and self.current_speed > 450:
            self.frequency *= 0.9997 # Efeito sutil mas cumulativo
            
        # 1. ATUALIZAR DISTÂNCIA
        distance = self.camera_offset
        
        # 2. CALCULAR TARGET_SPEED (PROGRESSÃO LOGARÍTMICA)
        target_speed = self.base_speed + math.log(max(1, distance / 100.0 + 1)) * 45.0
        
        # 3. LIMITADOR (REMOVIDOS MULTIPLICADORES DE BIOMA PARA EVITAR PULO DE VELOCIDADE)
        target_speed = min(self.max_speed, target_speed)
            
        # 4. INTERPOLAÇÃO DE VELOCIDADE
        self.current_speed += (target_speed - self.current_speed) * 1.2 * dt
        
        # 6. ATUALIZAR CAMERA_OFFSET
        self.camera_offset += self.current_speed * dt
        
        # 7. MANTER GAPS E START PHASE
        if self.camera_offset > self.start_distance_limit:
            self.start_phase = False
        self._maintain_gaps()
        self._maintain_terrain()
                
    def get_current(self):
        return self.biomes[self.current_idx]
        
    def get_ground_height(self, world_x, ignore_holes=False):
        # 1. VERIFICAR BURACOS
        if not ignore_holes:
            for g_start, g_end in self.gap_zones:
                if g_start <= world_x <= g_end:
                    return None
        
        idx = int((world_x - self.heightmap_start_x) / self.chunk_step)
        if idx < 0: idx = 0
        if idx >= len(self.heightmap) - 1:
            if self.heightmap: return round(self.heightmap[-1], 0)
            return 650
            
        # Lerp
        y1 = self.heightmap[idx]
        y2 = self.heightmap[idx+1]
        rem = (world_x - self.heightmap_start_x) % self.chunk_step
        t = rem / self.chunk_step
        return round(y1 + (y2 - y1) * t, 0)
        
    def get_ground_slope(self, world_x):
        idx = int((world_x - self.heightmap_start_x) / self.chunk_step)
        if idx < 0: return 0
        if idx >= len(self.heightmap) - 1: return 0
        y1 = self.heightmap[idx]
        y2 = self.heightmap[idx+1]
        return (y2 - y1) / self.chunk_step
        
    def draw_background(self, surface):
        surface.fill(self.get_current().bg_color)
        
    def draw_ground(self, surface, camera_y):
        name = self.get_current().name
        ground_color = (100, 200, 100)
        
        if name == "plains": 
            ground_color = (40, 170, 40)
        elif name == "desert": 
            ground_color = (194, 178, 128)
        elif name == "snow": 
            ground_color = (255, 255, 255)
            
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        
        # Calculamos o deslocamento vertical para centralizar a visão no player
        # camera_y é o foco. Queremos que camera_y fique em aprox. 60% da tela.
        offset_y = (screen_height * 0.6) - camera_y
        
        current_points = []
        # Amostragem mais larga (step 15) para remover ruído
        for x in range(0, screen_width + 30, 15):
            world_x = x + self.camera_offset
            y = self.get_ground_height(world_x)
            
            if y is not None:
                current_points.append((x, y + offset_y))
            else:
                if len(current_points) > 1:
                    self._draw_poly(surface, current_points, ground_color, screen_height)
                current_points = []
                
        if len(current_points) > 1:
            self._draw_poly(surface, current_points, ground_color, screen_height)

    def _draw_poly(self, surface, points, color, screen_height):
        # Fill polygon
        poly_points = points.copy()
        # O polígono deve descer até bem abaixo da tela para não vermos o corte
        poly_points.append((points[-1][0], screen_height + 500))
        poly_points.append((points[0][0], screen_height + 500))
        pygame.draw.polygon(surface, color, poly_points)
        # Draw white top line
        pygame.draw.lines(surface, (255, 255, 255), False, points, 3)
