import pygame
import math

class Player:
    def __init__(self, x, initial_ground_y):
        # Fallback de segurança para evitar TypeError no início do jogo
        spawn_y = initial_ground_y if initial_ground_y is not None else 400
        self.rect = pygame.Rect(x, spawn_y - 50, 40, 50)
        self.vy = 0
        self.jump_strength = -580
        
        # MOMENTUM (IMPULSO)
        self.momentum = 0
        self.max_momentum = 250
        self.angle = 0
        
        # PULO DUPLO
        self.jump_count = 0
        self.max_jumps = 2
        self.is_grounded = False
        
        # ESTAMINA
        self.max_stamina = 100
        self.stamina = 100
        self.stamina_cost_dash = 30
        self.stamina_recovery = 30.0 # por segundo (aprox 0.5 frame)
        
        # DASH
        self.is_dashing = False
        self.dash_speed = 600
        self.dash_duration = 0.25 # tempo real em dt
        self.dash_timer = 0
        self.dash_cooldown = 0
        
        # PLANAGEM
        self.is_gliding = False
        self.glide_gravity = 300
        self.normal_gravity = 1500
        
    def handle_input(self, dt, keys, jump_pressed, dash_pressed, biome_friction):
        # 4. RECUPERAÇÃO DE ESTAMINA
        if not self.is_dashing:
            self.stamina += self.stamina_recovery * dt
            self.stamina = min(self.stamina, self.max_stamina)
            if self.dash_cooldown > 0:
                self.dash_cooldown -= dt
                
        # 3. DASH
        if dash_pressed and not self.is_dashing and self.stamina >= self.stamina_cost_dash and self.dash_cooldown <= 0:
            self.is_dashing = True
            self.dash_timer = self.dash_duration
            self.stamina -= self.stamina_cost_dash
            self.dash_cooldown = 0.5
            
        # 6. PLANAGEM
        glide_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_z]
        if not self.is_grounded and glide_pressed and not self.is_dashing:
            self.is_gliding = True
        else:
            self.is_gliding = False
            
        # 5. PULO (DUPLO)
        if jump_pressed and self.jump_count < self.max_jumps:
            strength = self.jump_strength
            
            # BIOME INFLUENCE (ICE)
            if biome_friction < 1.0:
                 strength *= 1.15
                 
            # MOMENTUM INFLUENCE (Jumping higher when fast)
            momentum_bonus = self.momentum * 0.4
            self.vy = (strength - momentum_bonus)
            
            # MOMENTUM FORWARD BOOST
            if self.is_grounded:
                 self.rect.x += self.momentum * 0.15
            
            self.jump_count += 1
            self.is_grounded = False
            
    def update(self, dt, camera_offset, get_ground_height, get_ground_slope):
        # GRAVIDADE E PLANAGEM
        if self.is_gliding and self.vy >= 0:
            current_gravity = self.glide_gravity
            if self.vy > 150:
                self.vy = 150
        else:
            current_gravity = self.normal_gravity
            
        # 1. MOMENTUM E SLOPE
        world_x = self.rect.centerx + camera_offset
        slope = get_ground_slope(world_x)
        
        if self.is_grounded:
            if slope > 0.1: # Descida
                self.momentum += 200 * dt
            elif slope < -0.1: # Subida
                self.momentum -= 250 * dt
            else: # Plano
                self.momentum *= (1 - 0.4 * dt)
                
            # Alinhamento Visual
            target_angle = math.degrees(math.atan2(slope, 1))
            self.angle += (target_angle - self.angle) * 10 * dt
        else:
            # No ar: perde momentum mais devagar, inclina levemente
            self.momentum *= (1 - 0.2 * dt)
            self.angle += (0 - self.angle) * 5 * dt
            
        self.momentum = max(0, min(self.momentum, self.max_momentum))
            
        # 2. MOVIMENTO DASH HORIZONTAL
        if self.is_dashing:
            self.vy = 0 # Dash anula a queda temporalmente
            self.rect.height = 30 # Abaixa para passar por baixo dos pássaros
            self.rect.x += self.dash_speed * dt
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.rect.height = 50 # Volta ao normal
        else:
            # Puxar o jogador lentamente de volta ao X padrão
            target_x = 100
            if self.rect.x > target_x:
                # Se estiver com muito momentum, demora mais pra voltar (ou avança mais)
                pullback_speed = 200 if not self.is_grounded else 100
                self.rect.x = max(target_x, self.rect.x - pullback_speed * dt)
            elif self.rect.x < target_x:
                self.rect.x = min(target_x, self.rect.x + 200 * dt)
            
            # Gravidade apenas se não estiver grudado no chão
            if not self.is_grounded:
                self.vy += current_gravity * dt
                
        self.rect.y += self.vy * dt
        
        # CHECAGEM DO CHÃO (Sticky Ground para evitar quicar nas descidas)
        current_ground_y = get_ground_height(world_x)
        if current_ground_y is not None:
            # Diferença entre os pés do player e o chão real
            # Se for positiva: o player "atravessou" o chão
            # Se for negativa (pequena): o player está "perto" o suficiente para grudar
            ground_diff = self.rect.bottom - current_ground_y
            
            # Limite de 15 pixels para grudar (stickiness)
            # IMPORTANTE: Só grudar se estiver caindo ou no chão (vy >= 0)
            # Caso contrário, o player não consegue pular pois é sugado de volta
            if ground_diff >= -15 and self.vy >= 0:
                # Grudar no chão
                self.rect.bottom = current_ground_y
                self.vy = 0
                self.is_grounded = True
                self.jump_count = 0 
            else:
                self.is_grounded = False
        else:
            self.is_grounded = False
            
    def draw(self, surface, camera):
        zoom = camera.zoom
        # Deslocamento vertical ajustado pelo zoom
        offset_y = (surface.get_height() * 0.6) - camera.y * zoom
        
        # O player X é fixo perto de 100, mas o zoom afeta a escala de tudo
        # Vamos manter o foco no player em ~100
        screen_x = (self.rect.x - 100) * zoom + 100
        screen_y = self.rect.y * zoom + offset_y
        
        # Dimensões escaladas
        w, h = int(self.rect.width * zoom), int(self.rect.height * zoom)
        
        # Surface temporária com alpha e escala
        player_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        color = (50, 255, 150) if self.is_gliding else ((255, 200, 50) if self.is_dashing else (50, 150, 255))
        pygame.draw.rect(player_surf, color, (0, 0, w, h), border_radius=max(1, int(5 * zoom)))
        pygame.draw.rect(player_surf, (0, 0, 0), (0, 0, w, h), max(1, int(2 * zoom)), border_radius=max(1, int(5 * zoom)))
        
        # Rotacionar
        rotated_player = pygame.transform.rotate(player_surf, -self.angle)
        rot_rect = rotated_player.get_rect(center=(int(screen_x + w/2), int(screen_y + h/2)))
        surface.blit(rotated_player, rot_rect)
        
        # UI Estamina (Design mais premium)
        ui_x, ui_y = 20, 50
        pygame.draw.rect(surface, (30, 30, 30), (ui_x, ui_y, 104, 14)) # Borda
        pygame.draw.rect(surface, (80, 80, 80), (ui_x+2, ui_y+2, 100, 10)) # Fundo
        if self.stamina > 0:
            color = (50, 220, 50) if self.stamina > 30 else (220, 50, 50)
            pygame.draw.rect(surface, color, (ui_x+2, ui_y+2, self.stamina, 10))
            
        # UI Momentum (Flashy yellow)
        pygame.draw.rect(surface, (30, 30, 30), (ui_x, ui_y + 20, 104, 8))
        pygame.draw.rect(surface, (60, 60, 60), (ui_x+2, ui_y + 22, 100, 4))
        momentum_ratio = self.momentum / self.max_momentum
        if self.momentum > 0:
            pygame.draw.rect(surface, (255, 255, 0), (ui_x+2, ui_y + 22, int(100 * momentum_ratio), 4))
