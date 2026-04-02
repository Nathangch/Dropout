import pygame
import sys
import os
import state
from ui import MenuUI, GameOverUI, EndingUI
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
        self.target_y = 300
        self.look_ahead = 0
        
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

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Alto's Runner")
    clock = pygame.time.Clock()
    
    menu_ui = MenuUI(WIDTH, HEIGHT)
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
        sing_sound = None
        if os.path.exists("assets/sing.wav"):
            sing_sound = pygame.mixer.Sound("assets/sing.wav")
    except:
        sing_sound = None
    
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
                    if state.current_state == state.GameState.PLAYING:
                        reset_game(player, monster_manager, biome_manager, bg_manager, camera)
                        
                    if state.current_state == state.GameState.PLAYING:
                        reset_game(player, monster_manager, biome_manager, bg_manager, camera)
                        
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
            camera.update(player.rect, total_speed, dt)
            monster_manager.update(dt, current_biome, total_speed, biome_manager.camera_offset, biome_manager.get_ground_height, biome_manager.start_phase)
            particle_manager.update(dt, current_biome.name)
            
            # 1. VERIFICAR MORTE (COLISÃO OU QUEDA)
            # A queda é baseada na posição vertical relativa à câmera (screen y)
            player_screen_y = player.rect.centery + ((HEIGHT * 0.6) - camera.y)
            
            if collision_result == True or player_screen_y > HEIGHT + 100:
                state.current_state = state.GameState.GAME_OVER
                
            # 3. VERIFICAR SPAWN DO BAÚ FINAL (No final do 3º Bioma)
            # Spawn quando estiver no bioma 3 (Snow) e após percorrer a distância final
            # Usando time_elapsed como proxy para distância (6s * 400px/s ~= 2400 units)
            if biome_manager.current_idx == 2 and biome_manager.time_elapsed > 6 and not monster_manager.final_chest:
                # Procurar terreno plano à frente
                spawn_x = biome_manager.camera_offset + 900
                slope = biome_manager.get_ground_slope(spawn_x)
                if abs(slope) < 0.05: # Terreno plano
                    ground_y = biome_manager.get_ground_height(spawn_x)
                    if ground_y:
                        monster_manager.spawn_final_chest(spawn_x, ground_y)

        # 3. RENDERING
        if state.current_state == state.GameState.MENU:
            menu_ui.draw(screen)
            
        elif state.current_state == state.GameState.PLAYING:
            bg_manager.draw(screen)
            biome_manager.draw_ground(screen, camera.y)
            particle_manager.draw(screen)
            monster_manager.draw(screen, camera.y)
            player.draw(screen, camera.y)
            
            font = pygame.font.Font(None, 36)
            score_text = font.render(f"Biome: {biome_manager.get_current().name.capitalize()} | Time: {int(biome_manager.total_time_elapsed)}s", True, (0,0,0))
            screen.blit(score_text, (10, 10))
            
        elif state.current_state == state.GameState.GAME_OVER:
            bg_manager.draw(screen)
            biome_manager.draw_ground(screen, camera.y)
            particle_manager.draw(screen)
            monster_manager.draw(screen, camera.y)
            player.draw(screen, camera.y)
            
            game_over_ui.draw(screen)

        elif state.current_state == state.GameState.ENDING:
            # Renderiza o mundo estático ao fundo
            bg_manager.draw(screen)
            biome_manager.draw_ground(screen, camera.y)
            monster_manager.draw(screen, camera.y)
            player.draw(screen, camera.y)
            
            # Fade and Text
            if state.fade_alpha < 255:
                state.fade_alpha = min(255, state.fade_alpha + 150 * dt)
                
            ending_ui.draw(screen)
            
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
