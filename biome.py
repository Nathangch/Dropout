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
        self._maintain_gaps()
        
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
                
    def get_current(self):
        return self.biomes[self.current_idx]
        
    def get_ground_height(self, world_x):
        # 1. VERIFICAR BURACOS
        for g_start, g_end in self.gap_zones:
            if g_start <= world_x <= g_end:
                return None
        
        # y = A * sin(f * x + phase) + offset
        y = self.amplitude * math.sin(self.frequency * world_x + self.phase) + self.base_height
        
        # Start Phase: rampa linear suave descendente
        # Mantemos a continuidade: após o limite, o offset de 250px permanece constante
        if world_x < self.start_distance_limit:
            y += (world_x / self.start_distance_limit) * 250
        else:
            y += 250
            
        # Filtro de Arredondamento (Remove micro-oscilação invisível)
        return round(y, 0)
        
    def get_ground_slope(self, world_x):
        # Derivada da função seno: y' = A * f * cos(f * x + phase)
        slope = self.amplitude * self.frequency * math.cos(self.frequency * world_x + self.phase)
        
        # Ajuste da rampa inicial na inclinação (apenas enquanto world_x < limit)
        if world_x < self.start_distance_limit:
            slope += 250 / self.start_distance_limit
            
        return slope
        
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
