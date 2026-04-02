import pygame
import sys
import os
import random
import state
from ui import MenuUI, GameOverUI, EndingUI, StoryUI
from biome import BiomeManager
from player import Player
from monster import MonsterManager
from background import BackgroundManager
from particles import ParticleManager

WIDTH = 800
HEIGHT = 600

class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.y = 300
        self.look_ahead = 0
        self.shake = 0
        
    def update(self, player_rect, current_speed, dt):
        # O player X é fixo na tela em ~100 mais variações de dash/momentum
        # Mas aqui queremos seguir a posição Y principalmente
        self.target_y = player_rect.centery
        
        # LERP Suave (Follow delay)
        # Segue o player no Y para manter o enquadramento centralizado
        self.y += (self.target_y - self.y) * 4.5 * dt
        
        # Look ahead horizontal baseado na velocidade
        target_look_ahead = current_speed * 0.12
        self.look_ahead += (target_look_ahead - self.look_ahead) * 2.0 * dt
        
        # Shake decay
        self.shake *= 0.9

def reset_game(player, monster_manager, biome_manager, bg_manager, camera):
    biome_manager.reset()
    monster_manager.reset()
    bg_manager.current_bg = bg_manager.backgrounds["plains"]
    bg_manager.previous_bg = None
    bg_manager.transition_progress = 1.0
    initial_y = biome_manager.get_ground_height(100 + biome_manager.camera_offset)
    if initial_y is None: initial_y = 400 # Fallback de proteção
    player.__init__(100, initial_y)
    camera.y = initial_y
    state.fade_alpha = 0
    # Reset da suavização de velocidade para o novo jogo
    if hasattr(state, 'smooth_speed'):
        state.smooth_speed = biome_manager.current_speed + player.momentum
    
    state.avalanche_active = False
    state.avalanche_running = False
    state.avalanche_timer = 0.0
    state.avalanche_world_x = 0.0
    state.avalanche_triggered_once = False

def draw_avalanche(screen, camera_offset, world_x):
    ava_screen_x = world_x - camera_offset
    height = screen.get_height()
    if ava_screen_x > -800:
        # Fundo massivo da avalanche
        pygame.draw.rect(screen, (240, 240, 250), (-1000, 0, ava_screen_x + 1000, height))
        # Bordas irregulares para dar textura
        for i in range(25):
            offset_y = (i * (height / 20))
            pygame.draw.circle(screen, (240, 240, 250), (int(ava_screen_x), int(offset_y)), 40)

def draw_speed_lines(screen, total_speed):
    if total_speed < 550:
        return
        
    width = screen.get_width()
    height = screen.get_height()
    
    intensity = min((total_speed - 550) / 450.0, 1.0)
    num_lines = int(30 * intensity)
    
    for _ in range(num_lines):
        x = random.randint(int(width * 0.2), width + 200)
        y = random.randint(0, height)
        length = random.randint(50, 300)
        thickness = random.randint(1, 3)
        # Linhas brancas velozes com base no trailing horizontal
        pygame.draw.line(screen, (255, 255, 255), (x, y), (x - length, y), thickness)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Alto's Runner")
    clock = pygame.time.Clock()
    menu_ui = MenuUI(WIDTH, HEIGHT)
    story_ui = StoryUI(WIDTH, HEIGHT)
    game_over_ui = GameOverUI(WIDTH, HEIGHT)
    biome_manager = BiomeManager()
    bg_manager = BackgroundManager()
    camera = Camera(WIDTH, HEIGHT)
    ending_ui = EndingUI(WIDTH, HEIGHT)
    
    # Sound initialization placeholder
    try:
        pygame.mixer.init()
        # Se o usuário tiver um arquivo de som "sing.wav", ele tocará
        # Caso contrário, ignoramos para não quebrar o jogo
        wind_sound = None
        if os.path.exists("assets/wind.wav"):
            wind_sound = pygame.mixer.Sound("assets/wind.wav")
            wind_sound.play(-1)
            wind_sound.set_volume(0)
    except:
        sing_sound = None
        wind_sound = None
        
    current_wind_volume = 0.0
    
    initial_y = biome_manager.get_ground_height(100 + biome_manager.camera_offset)
    if initial_y is None: initial_y = 400
    player = Player(100, initial_y)
    camera.y = initial_y
    
    monster_manager = MonsterManager()
    particle_manager = ParticleManager(WIDTH, HEIGHT)
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        click_pos = None
        
        # 1. INPUT
        jump_pressed = False
        dash_pressed = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                state.current_state = state.GameState.EXIT
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click_pos = event.pos
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    jump_pressed = True
                elif event.key == pygame.K_x or event.key == pygame.K_LCTRL:
                    dash_pressed = True
                elif event.key == pygame.K_r and state.current_state == state.GameState.GAME_OVER:
                    state.current_state = state.GameState.PLAYING
                    reset_game(player, monster_manager, biome_manager, bg_manager, camera)
                elif event.key == pygame.K_RETURN and state.current_state == state.GameState.STORY:
                    state.current_state = state.GameState.PLAYING
                    reset_game(player, monster_manager, biome_manager, bg_manager, camera)
                    
        keys = pygame.key.get_pressed()

        # 2. LOGIC
        if state.current_state == state.GameState.EXIT:
            running = False
            continue
            
        elif state.current_state == state.GameState.MENU:
            if click_pos:
                new_state = menu_ui.handle_click(click_pos)
                if new_state:
                    state.current_state = getattr(state.GameState, new_state)
                        
        elif state.current_state == state.GameState.GAME_OVER:
            if click_pos:
                new_state = game_over_ui.handle_click(click_pos)
                if new_state:
                    state.current_state = getattr(state.GameState, new_state)
                    if state.current_state == state.GameState.PLAYING:
                        reset_game(player, monster_manager, biome_manager, bg_manager, camera)
                        
        elif state.current_state == state.GameState.ENDING:
            if click_pos:
                new_state = ending_ui.handle_click(click_pos)
                if new_state:
                    state.current_state = getattr(state.GameState, new_state)
                    if state.current_state == state.GameState.PLAYING:
                        reset_game(player, monster_manager, biome_manager, bg_manager, camera)

        elif state.current_state == state.GameState.PLAYING:
            biome_manager.update(dt)
            # A velocidade real é a soma da velocidade base com o momentum do player
            raw_total_speed = biome_manager.current_speed + player.momentum
            
            # FILTRO DE SUAVIZAÇÃO GLOBAL DE VELOCIDADE (Anti-Boost)
            # Garante que a velocidade do mundo não salte bruscamente
            if not hasattr(state, 'smooth_speed'): state.smooth_speed = raw_total_speed
            state.smooth_speed += (raw_total_speed - state.smooth_speed) * 0.8 * dt
            total_speed = state.smooth_speed
            
            # VENTO DINÂMICO
            if wind_sound:
                wind_target_volume = min(total_speed / 700.0, 1.0)
                if not player.is_grounded: wind_target_volume *= 1.5 # Vento mais forte no ar
                current_wind_volume += (wind_target_volume - current_wind_volume) * 2.0 * dt
                wind_sound.set_volume(min(current_wind_volume * 0.5, 1.0))
            
            # 0. VERIFICAR SE O BAÚ FOI ATINGIDO (Transição para Ending)
            collision_result = monster_manager.check_collision(player.rect)
            if collision_result == "ENDING":
                state.current_state = state.GameState.ENDING
                # Silenciar música de fundo
                try: pygame.mixer.music.fadeout(1000)
                except: pass
                # Efeito Visual de Partículas Mágicas
                particle_manager.spawn_burst(player.rect.centerx, player.rect.centery, (255, 255, 100), count=60)
                # Tocar som final
                if sing_sound:
                    sing_sound.play()
                pygame.time.delay(500) # Pequena pausa dramática


            
            current_biome = biome_manager.get_current()
            
            # --- AVALANCHE SYSTEM ---
            if biome_manager.current_idx == 2:
                if not state.avalanche_active and not state.avalanche_triggered_once:
                    # Fica obrigatório e dispara 3 segundos após o jogador entrar no bioma
                    if biome_manager.time_elapsed > 3.0:
                        state.avalanche_active = True
                        state.avalanche_timer = 0
                        state.avalanche_running = False
                        state.avalanche_triggered_once = True
                elif state.avalanche_active:
                    state.avalanche_timer += dt
                    
                    if state.avalanche_timer < 2.0:
                        camera.shake = max(camera.shake, 3.0)
                        particle_manager.spawn_avalanche_warning()
                    else:
                        if not state.avalanche_running:
                            state.avalanche_running = True
                            # Spawna na borda esquerda da tela, ligeiramente fora para ser contínuo
                            state.avalanche_world_x = biome_manager.camera_offset - 10
                        
                        # A avalanche tem a velocidade do bioma + um pequeno bônus
                        # Isso significa que o jogador precisa usar momentum (pulos/dash/descidas) para escapar!
                        # 30px a mais que a base, o que dá tempo razoável de escape se vacilar
                        avalanche_speed = biome_manager.current_speed + 30
                        state.avalanche_world_x += avalanche_speed * dt
                        
                        # Se o jogador estiver muito rápido, garante que a avalanche fique visível no limite da tela
                        if state.avalanche_world_x < biome_manager.camera_offset - 10:
                            state.avalanche_world_x = biome_manager.camera_offset - 10
                        
                        if (player.rect.centerx + biome_manager.camera_offset) < state.avalanche_world_x + 30:
                            state.current_state = state.GameState.GAME_OVER
            else:
                state.avalanche_active = False
                state.avalanche_running = False
            # ------------------------
            
            # Aplicar momentum no movimento da camera
            # Usamos a velocidade suavizada para evitar o tranco visual
            momentum_contribution = (total_speed - biome_manager.current_speed)
            biome_manager.camera_offset += momentum_contribution * dt
            
            bg_manager.set_biome(current_biome.name)
            bg_manager.update(total_speed, dt)
            
            # STATE PIPELINE DE HABILIDADES
            player.handle_input(dt, keys, jump_pressed, dash_pressed, current_biome.friction)
            
            # 2. UPDATES
            player.update(dt, biome_manager.camera_offset, biome_manager.get_ground_height, biome_manager.get_ground_slope)
            
            # 2.5 EVENTOS DE POUSO E RASTROS
            if player.just_landed:
                camera.shake = min(player.impact_force * 0.012, 12)
                offset_y = (HEIGHT * 0.6) - camera.y
                particle_manager.spawn_landing_particles(player.rect.centerx, player.rect.bottom + offset_y, player.impact_force)
                
            particle_manager.update_trail(player.is_grounded, player.rect.centerx + biome_manager.camera_offset, player.rect.bottom, current_biome.name)
            
            camera.update(player.rect, total_speed, dt)
            monster_manager.update(dt, current_biome, total_speed, biome_manager.camera_offset, biome_manager.get_ground_height, biome_manager.start_phase)
            particle_manager.update(dt, current_biome.name)
            
            # Turbilhão de Partículas Excesso de Velocidade
            if total_speed > 600 and random.random() < 0.5:
                particle_manager.spawn_particle(current_biome.name)
            
            # 1. VERIFICAR MORTE (COLISÃO OU QUEDA NO BURACO)
            if collision_result == True or player.fall_timer > 0.5:
                state.current_state = state.GameState.GAME_OVER
                
            # 3. VERIFICAR SPAWN DO BAÚ FINAL (No final do 3º Bioma)
            time_left = biome_manager.transition_time - biome_manager.time_elapsed
            if biome_manager.current_idx == 2 and time_left <= 5 and not monster_manager.final_chest:
                spawn_x = biome_manager.camera_offset + 900
                slope = biome_manager.get_ground_slope(spawn_x)
                
                # Evitar spawn em inclinação extrema
                if abs(slope) > 0.8:
                    spawn_x += 200  # procura área mais plana
                    
                ground_y = biome_manager.get_ground_height(spawn_x)
                if ground_y is not None:
                    monster_manager.spawn_final_chest(spawn_x, ground_y)

        # 3. RENDERING
        if state.current_state == state.GameState.MENU:
            menu_ui.draw(screen)
            
        elif state.current_state == state.GameState.STORY:
            story_ui.draw(screen)
            
        elif state.current_state == state.GameState.PLAYING:
            shake_y = random.uniform(-camera.shake, camera.shake) if camera.shake > 0.1 else 0
            draw_camera_y = camera.y + shake_y
            
            bg_manager.draw(screen)
            biome_manager.draw_ground(screen, draw_camera_y)
            particle_manager.draw_trail(screen, biome_manager.camera_offset, draw_camera_y)
            particle_manager.draw(screen)
            monster_manager.draw(screen, draw_camera_y)
            player.draw(screen, draw_camera_y)
            
            if getattr(state, 'avalanche_running', False):
                draw_avalanche(screen, biome_manager.camera_offset, state.avalanche_world_x)
            
            draw_speed_lines(screen, total_speed)
            
            player.draw_ui(screen)
            
            font = pygame.font.Font(None, 36)
            score_text = font.render(f"Biome: {biome_manager.get_current().name.capitalize()} | Time: {int(biome_manager.total_time_elapsed)}s", True, (0,0,0))
            screen.blit(score_text, (10, 10))
            
        elif state.current_state == state.GameState.GAME_OVER:
            bg_manager.draw(screen)
            biome_manager.draw_ground(screen, camera.y)
            particle_manager.draw(screen)
            monster_manager.draw(screen, camera.y)
            player.draw(screen, camera.y)
            
            if getattr(state, 'avalanche_running', False):
                draw_avalanche(screen, biome_manager.camera_offset, state.avalanche_world_x)
            
            game_over_ui.draw(screen)

        elif state.current_state == state.GameState.ENDING:
            # Renderiza o mundo estático ao fundo
            bg_manager.draw(screen)
            biome_manager.draw_ground(screen, camera.y)
            monster_manager.draw(screen, camera.y)
            player.draw(screen, camera.y)
            
            if getattr(state, 'avalanche_running', False):
                draw_avalanche(screen, biome_manager.camera_offset, state.avalanche_world_x)
            
            player.draw_ui(screen)
            
            # Fade and Text
            if state.fade_alpha < 255:
                state.fade_alpha = min(255, state.fade_alpha + 150 * dt)
                
            ending_ui.draw(screen)
            
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
