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
    Biome("plains", (20, 100, 180), friction=1.0, enemy_types=["wolf", "bird"], amplitude=70, frequency=0.003, variation=0.000002),
    # Desert: Suavemente mais ondulado (Diferença mínima para evitar boost)
    Biome("desert", (237, 201, 175), friction=1.0, enemy_types=["scorpion", "bird"], amplitude=78, frequency=0.0035, variation=0.000004),
    # Snow: Montanhoso mas controlado
    Biome("snow",   (200, 230, 255), friction=0.5, enemy_types=["ice_golem", "bird"], amplitude=90, frequency=0.004, variation=0.000005)
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
        
        # ENDING SEQUENCE STATE
        self.is_avalanche = False
        self.is_final_stretch = False
        self.end_trigger_x = 0
        self.final_trigger_x = 0
        
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
        
        # ENDING SEQUENCE
        self.is_avalanche = False
        self.is_final_stretch = False
        self.end_trigger_x = 0
        self.final_trigger_x = 0
        
        self._maintain_gaps()
        
    def _maintain_gaps(self):
        # SUPPRESS GAPS IN ENDING SEQUENCE
        if self.is_avalanche or self.is_final_stretch:
            self.gap_zones = []
            return

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
            
        # TRIGGER AVALANCHE (Ending Sequence)
        # 15s após entrar no Bioma 3 (Snow)
        if self.current_idx == 2 and self.time_elapsed > 15 and not self.is_avalanche and not self.is_final_stretch:
            self.is_avalanche = True
            self.end_trigger_x = self.camera_offset
            # A avalanche dura aproximadamente 15 segundos
            self.final_trigger_x = self.camera_offset + 15 * self.current_speed
            
        # Marcar fim da avalanche
        if self.is_avalanche and self.camera_offset > self.final_trigger_x:
            self.is_avalanche = False
            self.is_final_stretch = True
            
        self._maintain_gaps()
                
    def get_current(self):
        return self.biomes[self.current_idx]
        
    def _get_base_raw_height(self, world_x):
        # Calcula a altura teórica do terreno ignorando buracos
        y = self.amplitude * math.sin(self.frequency * world_x + self.phase) + self.base_height
        
        # Start Phase: rampa linear suave descendente
        if world_x < self.start_distance_limit:
            y += (world_x / self.start_distance_limit) * 250
        else:
            y += 250
            
        return round(y, 0)

    def get_raw_ground_height(self, world_x):
        # 1. FINAL STRETCH (Reta final plana)
        if self.is_final_stretch and world_x > self.final_trigger_x:
             # Manter a altura onde a avalanche terminou
             return self._get_base_raw_height(self.end_trigger_x) + (self.final_trigger_x - self.end_trigger_x) * 0.18
             
        # 2. AVALANCHE (Descida contínua)
        if (self.is_avalanche or self.is_final_stretch) and world_x > self.end_trigger_x:
             # Descida constante a partir do ponto de trigger
             return self._get_base_raw_height(self.end_trigger_x) + (world_x - self.end_trigger_x) * 0.18
             
        return self._get_base_raw_height(world_x)

    def get_ground_height(self, world_x):
        # 1. VERIFICAR BURACOS (Apenas se não for avalanche)
        if not self.is_avalanche and not self.is_final_stretch:
            for g_start, g_end in self.gap_zones:
                if g_start <= world_x <= g_end:
                    return None
        
        return self.get_raw_ground_height(world_x)
        
    def get_ground_slope(self, world_x):
        # 1. FINAL STRETCH (Reta Plana)
        if self.is_final_stretch and world_x > self.final_trigger_x:
            return 0.0
            
        # 2. AVALANCHE (Descida Constante)
        if (self.is_avalanche or self.is_final_stretch) and world_x > self.end_trigger_x:
            return 0.18 # Slope constante de descida
            
        # Derivada da função seno: y' = A * f * cos(f * x + phase)
        slope = self.amplitude * self.frequency * math.cos(self.frequency * world_x + self.phase)
        
        # Ajuste da rampa inicial na inclinação (apenas enquanto world_x < limit)
        if world_x < self.start_distance_limit:
            slope += 250 / self.start_distance_limit
            
        return slope
        
    def draw_background(self, surface):
        surface.fill(self.get_current().bg_color)
        
    def draw_ground(self, surface, camera):
        name = self.get_current().name
        zoom = camera.zoom
        ground_color = (100, 200, 100)
        
        if name == "plains": 
            ground_color = (40, 170, 40)
        elif name == "desert": 
            ground_color = (194, 178, 128)
        elif name == "snow": 
            ground_color = (255, 255, 255)
            
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        
        # Deslocamento vertical escalado
        offset_y = (screen_height * 0.6) - camera.y * zoom
        
        current_points = []
        # Amostragem ajustada pelo zoom (mais pontos se zoom out?)
        # Na verdade Mantendo o passo 15 e escalando o X final
        step = int(15 * zoom) if zoom > 1.0 else 15
        
        for x in range(0, int(screen_width / zoom) + 100, step):
            world_x = x + self.camera_offset
            y = self.get_ground_height(world_x)
            
            if y is not None:
                # Escala a partir do foco X=100
                display_x = (x - 100) * zoom + 100
                display_y = y * zoom + offset_y
                current_points.append((display_x, display_y))
            else:
                if len(current_points) > 1:
                    self._draw_poly(surface, current_points, ground_color, screen_height)
                current_points = []
                
        if len(current_points) > 1:
            self._draw_poly(surface, current_points, ground_color, screen_height)

    def _draw_poly(self, surface, points, color, screen_height):
        # Fill polygon
        poly_points = points.copy()
        # O polígono deve descer até BEM abaixo da tela para evitar partes em branco no zoom
        poly_points.append((points[-1][0], screen_height + 2000))
        poly_points.append((points[0][0], screen_height + 2000))
        pygame.draw.polygon(surface, color, poly_points)
        # Draw white top line
        pygame.draw.lines(surface, (255, 255, 255), False, points, 3)

    def draw_avalanche(self, surface, camera):
        """Desenha uma parede de neve massiva que persegue o jogador"""
        if not self.is_avalanche and not self.is_final_stretch:
            return
            
        zoom = camera.zoom
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        
        # Posição horizontal da 'frente' da avalanche na tela
        # O player costuma estar em display_x ~ 100.
        base_x = 50 
        
        # Transição de entrada (fade in progressivo)
        intro_dist = 500
        intro_progress = min(1.0, (self.camera_offset - self.end_trigger_x) / intro_dist) if self.is_avalanche else 1.0
        
        if self.is_final_stretch:
            # Na reta final, a avalanche fica para trás
            dist_past = self.camera_offset - self.final_trigger_x
            base_x -= dist_past * 0.8
            if base_x < -800: return

        # Ajuste de base_x para a animação de entrada
        current_base_x = base_x - (1.0 - intro_progress) * 400

        # Desenhar camadas (do fundo para a frente)
        layers = [
            {"color": (200, 220, 240), "offset": 80, "speed": 0.03},  # Camada interna/sombra
            {"color": (230, 240, 255), "offset": 40, "speed": 0.05},  # Camada média
            {"color": (255, 255, 255), "offset": 0,  "speed": 0.07}   # Camada frontal branca
        ]

        for layer in layers:
            points = []
            l_offset = layer["offset"]
            l_speed = layer["speed"]
            
            for y in range(-200, screen_height + 400, 40):
                time_var = self.camera_offset * l_speed
                variation = math.sin(y * 0.02 + time_var) * 30
                variation += math.cos(y * 0.05 - time_var * 0.5) * 15
                
                px = current_base_x - l_offset + variation
                
                # Cálculo de posição na tela usando o player (X=100) como âncora do zoom
                px_screen = (px - 100) * zoom + 100
                
                # Efeito de 'onda' na base (a avalanche se espalha no chão)
                world_x = self.camera_offset + (px - 100)
                ground_y = self.get_ground_height(world_x)
                if ground_y:
                    # offset_y local baseado na câmera
                    screen_ground_y = ground_y * zoom + (screen_height * 0.6) - camera.y * zoom
                    if y > screen_ground_y - 20:
                        px_screen += (y - (screen_ground_y - 20)) * 0.6
                
                points.append((px_screen, y))
            
            # Fechar o polígono na esquerda (bem longe)
            points.append((-1500, screen_height + 400))
            points.append((-1500, -200))
            
            # Desenhar a camada
            pygame.draw.polygon(surface, layer["color"], points)
            
            # Adicionar 'bolas' de neve na crista da camada frontal para parecer fofo/volumoso
            if layer["color"] == (255, 255, 255):
                for i in range(0, len(points), 3):
                    p = points[i]
                    if p[0] > -100: # Apenas se visível
                        r = (40 + math.sin(i + self.camera_offset * 0.1) * 20) * zoom
                        pygame.draw.circle(surface, (255, 255, 255), (int(p[0]), int(p[1])), int(r))
