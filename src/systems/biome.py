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
        
        # Carregar Texturas de Chao Específicas
        try:
            tex = pygame.image.load("assets/backgrounds/grama.png").convert_alpha()
            h = min(200, tex.get_height())
            w = int(h * (tex.get_width() / tex.get_height()))
            self.grass_tex = pygame.transform.scale(tex, (w, h))
        except: self.grass_tex = None

        try:
            t_sand = pygame.image.load("assets/backgrounds/areia.jpg").convert_alpha()
            h = min(200, t_sand.get_height())
            w = int(h * (t_sand.get_width() / t_sand.get_height()))
            self.sand_tex = pygame.transform.scale(t_sand, (w, h))
        except: self.sand_tex = None
        
        try:
            t_snow = pygame.image.load("assets/backgrounds/neve.jpg").convert_alpha()
            h = min(200, t_snow.get_height())
            w = int(h * (t_snow.get_width() / t_snow.get_height()))
            self.snow_tex = pygame.transform.scale(t_snow, (w, h))
        except: self.snow_tex = None

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
        if self.is_final_stretch:
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
        
        # Terreno rigorosamente estático para evitar "ebulição" (boiling hills) -> Enjoo
        # A variação das ondas é puramente baseada na frente/atrás (coordenadas x).
        self.amplitude = 80
        self.frequency = 0.003
            
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
            
            pygame.mixer.stop()
            try: pygame.mixer.music.stop()
            except: pass
            
            avalanche_duration = 15.0 # Fallback
            from core import state
            if hasattr(state, 'audio_system') and state.audio_system.get('avalanche'):
                av_sound = state.audio_system['avalanche']
                av_sound.play()
                avalanche_duration = av_sound.get_length()
                
            self.end_trigger_x = self.camera_offset
            self.final_trigger_x = self.camera_offset + avalanche_duration * self.current_speed
            
        # Marcar fim da avalanche
        if self.is_avalanche and self.camera_offset > self.final_trigger_x:
            self.is_avalanche = False
            self.is_final_stretch = True
            
        self._maintain_gaps()
                
    def get_current(self):
        return self.biomes[self.current_idx]
        
    def _get_base_raw_height(self, world_x):
        freq = self.frequency
        amp = self.amplitude
        
        # 1. Macro relevo (Montanhas e vales massivos)
        y = (amp * 1.8) * math.sin(freq * 0.3 * world_x + self.phase)
        
        # 2. Relevo médio (Ondulações padrão)
        y += amp * math.sin(freq * world_x)
        
        # 3. Micro relevo (Pequenos solavancos imprevisíveis)
        y += (amp * 0.4) * math.sin(freq * 2.7 * world_x + 45)
        
        y += self.base_height
        
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
        # 1. VERIFICAR BURACOS
        if not self.is_final_stretch:
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
            
        freq = self.frequency
        amp = self.amplitude
        
        # Derivadas harmônicas combinadas (Macro + Médio + Micro)
        slope = (amp * 1.8) * (freq * 0.3) * math.cos(freq * 0.3 * world_x + self.phase)
        slope += amp * freq * math.cos(freq * world_x)
        slope += (amp * 0.4) * (freq * 2.7) * math.cos(freq * 2.7 * world_x + 45)
        
        # Ajuste da rampa inicial na inclinação (apenas enquanto world_x < limit)
        if world_x < self.start_distance_limit:
            slope += 250 / self.start_distance_limit
            
        return slope
        
    def draw_background(self, surface):
        surface.fill(self.get_current().bg_color)
        
    def draw_ground(self, surface, camera):
        name = self.get_current().name
        zoom = camera.zoom
        
        if name == "plains": 
            ground_color = (92, 64, 51)  # Terra escura pro subsolo
        elif name == "desert": 
            ground_color = (194, 178, 128)
        elif name == "snow": 
            ground_color = (255, 255, 255)
        else:
            ground_color = (100, 200, 100)
            
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        
        # Deslocamento vertical escalado (80% da tela para deixar 80% pro ceu e horizonte)
        offset_y = (screen_height * 0.8) - camera.y * zoom
        
        current_points = []
        step = int(4 * zoom) if zoom > 1.0 else 4
        
        for x in range(0, int(screen_width / zoom) + 100, step):
            world_x = x + self.camera_offset
            y = self.get_ground_height(world_x)
            
            if y is not None:
                display_x = (x - 100) * zoom + 100
                display_y = y * zoom + offset_y
                current_points.append((display_x, display_y))
            else:
                if len(current_points) > 1:
                    self._draw_poly(surface, current_points, ground_color, screen_height, camera, name)
                current_points = []
                
        if len(current_points) > 1:
            self._draw_poly(surface, current_points, ground_color, screen_height, camera, name)

    def _draw_poly(self, surface, points, color, screen_height, camera, biome_name):
        # 1. Base imediata
        poly_points = points.copy()
        poly_points.append((points[-1][0], screen_height + 2000))
        poly_points.append((points[0][0], screen_height + 2000))
        pygame.draw.polygon(surface, color, poly_points)
        
        # 2. Adicionar Estratos geológicos (camadas de terra profundas)
        if biome_name == "plains":
            deep_p = [(p[0], p[1] + 160 * camera.zoom) for p in points]
            deep_p.append((deep_p[-1][0], screen_height + 2000))
            deep_p.append((deep_p[0][0], screen_height + 2000))
            pygame.draw.polygon(surface, (54, 34, 4), deep_p) # Núcleo escuro
            
            core_p = [(p[0], p[1] + 350 * camera.zoom) for p in points]
            core_p.append((core_p[-1][0], screen_height + 2000))
            core_p.append((core_p[0][0], screen_height + 2000))
            pygame.draw.polygon(surface, (25, 15, 0), core_p) # Sombra abissal
            
        elif biome_name == "desert":
            deep_p = [(p[0], p[1] + 200 * camera.zoom) for p in points]
            deep_p.append((deep_p[-1][0], screen_height + 2000))
            deep_p.append((deep_p[0][0], screen_height + 2000))
            pygame.draw.polygon(surface, (140, 100, 70), deep_p) 
        
        # Aplicação procedimental do arquivo grama.png no topo do relevo
        tex_to_draw = None
        if biome_name == "plains" and hasattr(self, 'grass_tex') and self.grass_tex: tex_to_draw = self.grass_tex
        elif biome_name == "desert" and hasattr(self, 'sand_tex') and self.sand_tex: tex_to_draw = self.sand_tex
        elif biome_name == "snow" and hasattr(self, 'snow_tex') and self.snow_tex: tex_to_draw = self.snow_tex
        
        if tex_to_draw:
            tex_w = tex_to_draw.get_width()
            tex_h = tex_to_draw.get_height()
            
            for i in range(len(points) - 1):
                px, py = points[i]
                nxt_px, nxt_py = points[i+1]
                slice_w = int(nxt_px - px) + 2
                if slice_w <= 0: continue
                
                world_x = (px - 100) / camera.zoom + 100 + self.camera_offset
                src_x = int(world_x) % tex_w
                
                crop = pygame.Rect(src_x, 0, min(slice_w, tex_w - src_x), tex_h)
                surface.blit(tex_to_draw, (px, py - 3), area=crop)
                
                leftover = slice_w - crop.width
                if leftover > 0:
                    surface.blit(tex_to_draw, (px + crop.width, py - 3), area=pygame.Rect(0, 0, leftover, tex_h))
        else:
            # Manter padrão para os outros biomas
            line_c = (255,255,255) if biome_name == "snow" else (255, 230, 180)
            pygame.draw.lines(surface, line_c, False, points, 3)

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
