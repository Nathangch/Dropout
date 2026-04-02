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
        self.zoom = 1.0
        self.target_zoom = 1.0
        
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
        
        # Zoom Lerp
        self.zoom += (self.target_zoom - self.zoom) * 2.0 * dt

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
    # Posição X da avalanche na tela (world_x é a posição absoluta do topo da avalanche)
    # A avalanche cresce para a ESQUERDA, mas world_x é a ponta DIREITA dela
    ava_screen_x = world_x - camera_offset
    
    width = screen.get_width()
    height = screen.get_height()
    
    # A avalanche só é visível se estiver na tela ou perto
    if ava_screen_x > -width:
        # Desenhar uma parede de neve branca gigante que cobre toda a esquerda
        # O gradiente dá a ideia de densidade
        for i in range(10):
            # Camadas de neve com alfa diferente
            alpha = 255 - (i * 20)
            offset_x = i * 15
            # A caixa da avalanche
            ava_rect = pygame.Rect(-width, 0, ava_screen_x + width - offset_x, height)
            
            # Surface com alpha
            s = pygame.Surface((ava_rect.width, ava_rect.height), pygame.SRCALPHA)
            color = (250, 250, 255, alpha)
            pygame.draw.rect(s, color, (0, 0, ava_rect.width, ava_rect.height))
            
            # Adicionar textura de partículas na parede de neve
            for _ in range(5):
                px = random.randint(0, ava_rect.width)
                py = random.randint(0, ava_rect.height)
                pygame.draw.circle(s, (255, 255, 255, alpha), (px, py), random.randint(2, 5))
                
            screen.blit(s, (ava_rect.x, ava_rect.y))
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
        script_dir = os.path.dirname(os.path.abspath(__file__))
        wind_path = os.path.join(script_dir, "assets", "wind.wav")
        # Se o usuário tiver um arquivo de som "wind.wav", ele tocará
        # Caso contrário, ignoramos para não quebrar o jogo
        wind_sound = None
        if os.path.exists(wind_path):
            wind_sound = pygame.mixer.Sound(wind_path)
            wind_sound.play(-1)
            wind_sound.set_volume(0)
    except:
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
            
            # --- AVALANCHE SYSTEM (Cinematic Event) ---
            if biome_manager.current_idx == 2: # Snow Biome
                if not state.avalanche_active and not state.avalanche_triggered_once:
                    # Tira a dúvida: Dispara exatamente aos 15 segundos
                    if biome_manager.time_elapsed >= 15.0:
                        state.avalanche_active = True
                        state.avalanche_timer = 0
                        state.avalanche_running = False
                        state.avalanche_triggered_once = True
                        state.avalanche_ending = False
                        # GARANTIR TERRENO LIMPO E SEGURO
                        monster_manager.clear()
                        biome_manager.clear_gaps()
                        # ZOOM-OUT suave no início
                        camera.target_zoom = 0.85
                
                elif state.avalanche_active:
                    state.avalanche_timer += dt
                    
                    # 1. BOOST DE MOMENTUM (Garantir sensação de velocidade)
                    player.momentum += 15 * dt
                    
                    if state.avalanche_timer < 2.0:
                        # Warning period
                        camera.shake = max(camera.shake, 4.0)
                        particle_manager.spawn_avalanche_warning()
                    else:
                        if not state.avalanche_running:
                            state.avalanche_running = True
                            state.avalanche_world_x = biome_manager.camera_offset - 400
                        
                        # 2. MOVIMENTO DA AVALANCHE (Baseado na velocidade do player)
                        # avalanche_speed = player.speed * 0.95
                        avalanche_speed = total_speed * 0.94
                        state.avalanche_world_x += avalanche_speed * dt
                        
                        # Morte ao ser pego pela parede branca
                        player_world_x = player.rect.centerx + biome_manager.camera_offset
                        if player_world_x < state.avalanche_world_x + 50:
                            state.current_state = state.GameState.GAME_OVER
                    
                    # 3. FINALIZAR EVENTO (Começa a reta aos 10s de fuga)
                    if state.avalanche_timer > 10.0 and not state.avalanche_ending:
                        state.avalanche_ending = True
                        # Spawn do baú garantido na reta à frente
                        spawn_x = biome_manager.camera_offset + 1000
                        ground_y = biome_manager.get_ground_height(spawn_x, ignore_holes=True)
                        monster_manager.spawn_final_chest(spawn_x, ground_y)
                    
                    # FIM REAL (13s): Para a avalanche e volta zoom
                    if state.avalanche_timer > 13.0:
                        state.avalanche_active = False
                        state.avalanche_running = False
                        state.avalanche_ending = False
                        camera.target_zoom = 1.0
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
            if collision_result == True or player.fall_timer > 0.2:
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
        # 1. CÁLCULO DO VIEWPORT VIRTUAL (Para suportar o ZOOM real)
        v_width = int(WIDTH / camera.zoom)
        v_height = int(HEIGHT / camera.zoom)
        game_surface = pygame.Surface((v_width, v_height))
        
        # Sincronizar o ParticleManager com as dimensões virtuais (Para neve/poeira cobrir tudo)
        particle_manager.width = v_width
        particle_manager.height = v_height
        
        # 2. CALCULAR OFFSETS DE DESENHO (Para manter o player focado)
        # Queremos que o player.x=100 na tela final original (800x600)
        # screen_x = (world_x - draw_offset_x) * zoom => 100.
        # draw_offset_x = (player_world_x) - (100 / zoom)
        player_world_x = player.rect.centerx + biome_manager.camera_offset
        draw_camera_offset = player_world_x - (100 / camera.zoom)
        
        # Para o Y: queremos manter o foco do player na posição relativa 60%
        # draw_camera_y = camera.y (foco central)
        # O offset_y nas funções de draw já cuida de centralizar no 0.6 * surface_height
        # Mas como a v_height mudou, as funções usarão v_height automaticamente.
        draw_camera_y = camera.y 
        
        if state.current_state == state.GameState.MENU:
            menu_ui.draw(game_surface)
            
        elif state.current_state == state.GameState.STORY:
            story_ui.draw(game_surface)
            
        elif state.current_state == state.GameState.PLAYING:
            shake_y = random.uniform(-camera.shake, camera.shake) if camera.shake > 0.1 else 0
            # Aplicamos o shake no foco
            draw_camera_y_with_shake = draw_camera_y + shake_y
            
            bg_manager.draw(game_surface)
            biome_manager.draw_ground(game_surface, draw_camera_y_with_shake, draw_camera_offset)
            particle_manager.draw_trail(game_surface, draw_camera_offset, draw_camera_y_with_shake)
            particle_manager.draw(game_surface)
            monster_manager.draw(game_surface, draw_camera_y_with_shake, draw_camera_offset)
            player.draw_at_world(game_surface, draw_camera_y_with_shake, draw_camera_offset, player_world_x)
            
            if getattr(state, 'avalanche_running', False):
                draw_avalanche(game_surface, draw_camera_offset, state.avalanche_world_x)
            
            draw_speed_lines(game_surface, total_speed)
            
            player.draw_ui(game_surface)
            
            font = pygame.font.Font(None, 36)
            score_text = font.render(f"Biome: {biome_manager.get_current().name.capitalize()} | Time: {int(biome_manager.total_time_elapsed)}s", True, (0,0,0))
            game_surface.blit(score_text, (10, 10))
            
        elif state.current_state == state.GameState.GAME_OVER:
            bg_manager.draw(game_surface)
            biome_manager.draw_ground(game_surface, draw_camera_y, draw_camera_offset)
            particle_manager.draw(game_surface)
            monster_manager.draw(game_surface, draw_camera_y, draw_camera_offset)
            player.draw_at_world(game_surface, draw_camera_y, draw_camera_offset, player_world_x)
            
            if getattr(state, 'avalanche_running', False):
                draw_avalanche(game_surface, draw_camera_offset, state.avalanche_world_x)
            
            game_over_ui.draw(game_surface)

        elif state.current_state == state.GameState.ENDING:
            # Renderiza o mundo estático ao fundo
            bg_manager.draw(game_surface)
            # Na reta final a camera fica no player
            biome_manager.draw_ground(game_surface, draw_camera_y, draw_camera_offset)
            monster_manager.draw(game_surface, draw_camera_y, draw_camera_offset)
            player.draw_at_world(game_surface, draw_camera_y, draw_camera_offset, player_world_x)
            
            if getattr(state, 'avalanche_running', False):
                draw_avalanche(game_surface, draw_camera_offset, state.avalanche_world_x)
            
            player.draw_ui(game_surface)
            
            # Fade and Text
            if state.fade_alpha < 255:
                state.fade_alpha = min(255, state.fade_alpha + 150 * dt)
                
            ending_ui.draw(game_surface)
            
        # APLICAÇÃO DO ZOOM FINAL (Scale Down)
        # Sempre redimensionamos para 800x600 para preencher a tela original
        final_surface = pygame.transform.smoothscale(game_surface, (WIDTH, HEIGHT))
        screen.blit(final_surface, (0, 0))
            
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
