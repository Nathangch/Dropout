import pygame
import math

class Player:
    _cached_idle_frames = None
    _cached_fallback_image = None
    
    def __init__(self, x, initial_ground_y):
        spawn_y = initial_ground_y if initial_ground_y is not None else 400
        self.base_width = 60
        self.base_height = 75
        self.rect = pygame.Rect(x, spawn_y - self.base_height, self.base_width, self.base_height)
        self.vy = 0
        self.jump_strength = -650 
        
        self.momentum = 0
        self.max_momentum = 250
        self.angle = 0
        self.jump_count = 0
        self.max_jumps = 2
        self.is_grounded = False
        
        self.max_stamina = 100
        self.stamina = 100
        self.stamina_cost_dash = 30
        self.stamina_recovery = 30.0 
        
        self.is_dashing = False
        self.dash_speed = 600
        self.dash_duration = 0.25 
        self.dash_timer = 0
        self.dash_cooldown = 0
        
        self.is_gliding = False
        self.glide_gravity = 300
        self.normal_gravity = 1500
        
        # Carregar a animação usando cache de classe para evitar lag
        if Player._cached_idle_frames is None:
            Player._cached_idle_frames = []
            if not hasattr(Player, '_cached_dash_frames'): Player._cached_dash_frames = []
            try:
                import os
                # Idle
                full_sheet = pygame.image.load("assets/sprites/idle.png").convert_alpha()
                sheet_w = full_sheet.get_width()
                sheet_h = full_sheet.get_height()
                frame_w = sheet_w // 6
                for i in range(6):
                    frame = full_sheet.subsurface(pygame.Rect(i*frame_w, 0, frame_w, sheet_h))
                    scaled = pygame.transform.scale(frame, (60, 75))
                    Player._cached_idle_frames.append(scaled)
                    
                # Dash
                dash_sheet = pygame.image.load("assets/sprites/dash.png").convert_alpha()
                d_sheet_w = dash_sheet.get_width()
                d_sheet_h = dash_sheet.get_height()
                d_frame_w = d_sheet_w // 5
                for i in range(5):
                    d_frame = dash_sheet.subsurface(pygame.Rect(i*d_frame_w, 0, d_frame_w, d_sheet_h))
                    d_scaled = pygame.transform.scale(d_frame, (60, 75))
                    Player._cached_dash_frames.append(d_scaled)
                    
                # Jump 
                if not hasattr(Player, '_cached_jump_frames'): Player._cached_jump_frames = []
                jump_sheet = pygame.image.load("assets/sprites/jump.png").convert_alpha()
                j_sheet_w = jump_sheet.get_width()
                j_sheet_h = jump_sheet.get_height()
                j_frame_w = j_sheet_w // 6
                for i in range(6):
                    j_frame = jump_sheet.subsurface(pygame.Rect(i*j_frame_w, 0, j_frame_w, j_sheet_h))
                    j_scaled = pygame.transform.scale(j_frame, (60, 75))
                    Player._cached_jump_frames.append(j_scaled)
                    
            except Exception: pass
            
            if not Player._cached_idle_frames:
                try:
                    img = pygame.image.load("assets/sprites/bode.png").convert_alpha()
                    Player._cached_fallback_image = pygame.transform.scale(img, (60, 75))
                except: pass
                
        self.idle_frames = Player._cached_idle_frames
        self.dash_frames = getattr(Player, '_cached_dash_frames', [])
        self.jump_frames = getattr(Player, '_cached_jump_frames', [])
        self.current_frame = 0
        self.anim_timer = 0
        self.image = self.idle_frames[0] if self.idle_frames else Player._cached_fallback_image
        
    def handle_input(self, dt, keys, jump_pressed, dash_pressed, biome_friction):
        # 6. PLANAGEM 
        glide_pressed = keys[pygame.K_SPACE]
        if not self.is_grounded and glide_pressed and not self.is_dashing and self.stamina > 0 and self.vy > -50:
            self.is_gliding = True
            self.stamina -= 25 * dt # Gasta estamina proporcionalmente ao tempo no ar
            if self.stamina < 0: self.stamina = 0
        else:
            self.is_gliding = False

        # 4. RECUPERAÇÃO DE ESTAMINA
        if not self.is_dashing and not self.is_gliding:
            self.stamina += self.stamina_recovery * dt
            self.stamina = min(self.stamina, self.max_stamina)
            if self.dash_cooldown > 0:
                self.dash_cooldown -= dt
                
        # 3. DASH
        if dash_pressed and not self.is_dashing and self.stamina >= self.stamina_cost_dash and self.dash_cooldown <= 0:
            self.is_dashing = True
            
            from core import state
            if hasattr(state, 'audio_system') and state.audio_system.get('dash'):
                state.audio_system['dash'].play()
                
            self.dash_timer = self.dash_duration
            self.stamina -= self.stamina_cost_dash
            self.dash_cooldown = 0.5
            
            # Reset animation for dash
            self.current_frame = 0
            self.anim_timer = 0
            
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
        # ANIMAÇÃO (IDLE, DASH ou JUMP)
        if self.is_dashing and self.dash_frames:
            active_frames = self.dash_frames
            fps = 24.0
        elif not self.is_grounded and self.jump_frames:
            active_frames = self.jump_frames
            fps = 12.0 # Animação de pulo tende a ser mais majestosa e ligeiramente mais lenta
        else:
            active_frames = self.idle_frames
            fps = 15.0
            
        if active_frames:
            self.anim_timer += dt
            if self.anim_timer >= 1.0 / fps: 
                self.anim_timer = 0
                self.current_frame = (self.current_frame + 1) % len(active_frames)
                self.image = active_frames[self.current_frame]

        # FALAS ALEATÓRIAS
        if not hasattr(self, 'speech_timer'):
            self.speech_timer = 0
            import random
            self.speech_cooldown = random.uniform(5.0, 15.0)
            
        self.speech_timer += dt
        if self.speech_timer > self.speech_cooldown:
            self.speech_timer = 0
            import random
            self.speech_cooldown = random.uniform(8.0, 20.0)
            from core import state
            if hasattr(state, 'audio_system'):
                falas = [state.audio_system.get("fala1"), state.audio_system.get("fala2"), state.audio_system.get("fala3")]
                valid_falas = [f for f in falas if f is not None]
                if valid_falas:
                    voice_channel = state.audio_system.get('voice_channel')
                    if voice_channel and not voice_channel.get_busy():
                        voice_channel.play(random.choice(valid_falas))

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
            
            # Abaixa a hitbox para passar por baixo dos pássaros, preservando a posição do chão
            if self.rect.height != 35:
                bottom_at_start = self.rect.bottom
                self.rect.height = 35 
                self.rect.bottom = bottom_at_start
                
            self.rect.x += self.dash_speed * dt
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_dashing = False
                # Volta ao normal preservando a posição do chão
                bottom_at_end = self.rect.bottom
                self.rect.height = self.base_height
                self.rect.bottom = bottom_at_end
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
        offset_y = (surface.get_height() * 0.8) - camera.y * zoom
        
        # O player X é fixo perto de 100, mas o zoom afeta a escala de tudo
        # Vamos manter o foco no player em ~100
        screen_x = (self.rect.x - 100) * zoom + 100
        screen_y = self.rect.y * zoom + offset_y
        
        # Dimensões escaladas para desenho (independente da hitbox)
        draw_w = int(self.base_width * zoom)
        draw_h = int(self.base_height * zoom)
        
        # Hitbox real para referência (pode estar menor no dash)
        rect_w, rect_h = int(self.rect.width * zoom), int(self.rect.height * zoom)
        
        # Surface temporária com alpha e escala
        player_surf = pygame.Surface((draw_w, draw_h), pygame.SRCALPHA)
        color = (50, 255, 150) if self.is_gliding else ((255, 200, 50) if self.is_dashing else (50, 150, 255))
        
        if hasattr(self, 'image') and self.image:
            scaled_img = pygame.transform.scale(self.image, (draw_w, draw_h)) if zoom != 1.0 else self.image
            player_surf.blit(scaled_img, (0, 0))
        else:
            pygame.draw.rect(player_surf, color, (0, 0, draw_w, draw_h), border_radius=max(1, int(5 * zoom)))
            pygame.draw.rect(player_surf, (0, 0, 0), (0, 0, draw_w, draw_h), max(1, int(2 * zoom)), border_radius=max(1, int(5 * zoom)))
            
        # Rotacionar com base no slope
        rotated_player = pygame.transform.rotate(player_surf, -self.angle)
        # Centralizar o desenho na parte inferior da hitbox para manter os pés no chão
        draw_center_x = screen_x + rect_w / 2
        draw_center_y = screen_y + rect_h - draw_h / 2
        rot_rect = rotated_player.get_rect(center=(int(draw_center_x), int(draw_center_y)))
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
