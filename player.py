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
        self.max_momentum = 500
        self.angle = 0
        
        # PULO DUPLO
        self.jump_count = 0
        self.max_jumps = 2
        self.is_grounded = False
        self.was_in_air = False
        self.just_landed = False
        self.impact_force = 0
        self.falling_into_hole = False
        self.fall_timer = 0
        
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
            if slope > 0.05: # Descida
                self.momentum += (slope * 600) * dt
            elif slope < -0.05: # Subida
                # slope é negativo na subida, então somar diminui o momentum
                self.momentum += (slope * 500) * dt
            else: # Plano
                self.momentum -= 60 * dt
                
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
            self.rect.x += self.dash_speed * dt
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_dashing = False
        else:
            # Puxar o jogador lentamente de volta ao X padrão
            target_x = 100
            if self.rect.x > target_x:
                # Se estiver com muito momentum, demora mais pra voltar (ou avança mais)
                pullback_speed = 200 if not self.is_grounded else 100
                self.rect.x = max(target_x, self.rect.x - pullback_speed * dt)
            elif self.rect.x < target_x:
                self.rect.x = min(target_x, self.rect.x + 200 * dt)
               # 3. MOVEMENT VERTCAL
        if not self.is_grounded:
            self.vy += 1500 * dt
        self.rect.y += self.vy * dt
        
        # CHECAGEM DO CHÃO
        self.was_in_air = not self.is_grounded
        vy_before_landing = self.vy
        self.just_landed = False
        
        current_ground_y = get_ground_height(world_x)
        expected_ground_y = get_ground_height(world_x, ignore_holes=True)
        
        if current_ground_y is not None:
            self.falling_into_hole = False
            self.fall_timer = 0
            if self.rect.bottom >= current_ground_y:
                self.rect.bottom = current_ground_y
                if self.vy > 0:
                    self.vy = 0
                if self.was_in_air:
                    self.just_landed = True
                    self.impact_force = abs(vy_before_landing)
                self.is_grounded = True
                self.jump_count = 0 # Reseta os pulos ao tocar o chão
            elif self.was_grounded and self.vy >= 0:
                diff = current_ground_y - self.rect.bottom
                if 0 < diff < 150: # Evitar voar para fora da pista
                    # Interpolação suave para snap no chão
                    self.rect.bottom += max(1, int(diff * 0.4))
                    self.vy = 0
                    self.is_grounded = True
                else:
                    self.is_grounded = False
            else:
                self.is_grounded = False
        else:
            self.is_grounded = False
            # O jogador só caiu no buraco se o pé dele estiver abaixo da linha teórica do cenário
            if expected_ground_y is not None and self.rect.bottom >= expected_ground_y:
                self.falling_into_hole = True
            else:
                self.falling_into_hole = False
            
        if self.falling_into_hole:
            self.fall_timer += dt
            
    def draw(self, surface, camera_y):
        # Deslocamento vertical da câmera
        offset_y = (surface.get_height() * 0.6) - camera_y
        
        # Criar retângulo de exibição na tela
        screen_rect = self.rect.copy()
        screen_rect.y += offset_y
        
        # Desenho rotacionado do player
        color = (50, 255, 150) if self.is_gliding else ((255, 200, 50) if self.is_dashing else (50, 150, 255))
        
        # Surface temporária com alpha
        player_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(player_surf, color, (0, 0, self.rect.width, self.rect.height), border_radius=5)
        pygame.draw.rect(player_surf, (0, 0, 0), (0, 0, self.rect.width, self.rect.height), 2, border_radius=5)
        
        # Rotacionar com base no slope
        rotated_player = pygame.transform.rotate(player_surf, -self.angle)
        rot_rect = rotated_player.get_rect(center=screen_rect.center)
        surface.blit(rotated_player, rot_rect)
        
    def draw_ui(self, surface):
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
