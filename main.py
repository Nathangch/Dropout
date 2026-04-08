import pygame
import sys
import os
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from core import state
from ui.ui import MenuUI, GameOverUI, EndingUI, StoryUI, TutorialUI, OptionsUI, PauseUI
from systems.biome import BiomeManager
from entities.player import Player
from entities.monster import MonsterManager
from systems.background import BackgroundManager
from systems.particles import ParticleManager
from utils.utils import resource_path
import random

WIDTH = 800
HEIGHT = 600

class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.y = 300
        self.target_y = 300
        self.look_ahead = 0
        self.zoom = 1.0
        self.target_zoom = 1.0
        
    def update(self, player_rect, current_speed, dt, is_on_hole=False, current_ground_y=None):
        # A câmera foca primariamente no cenário/chão, bloqueando solavancos em pulos longos.
        # A câmera foca primariamente no cenário/chão, bloqueando solavancos em pulos longos.
        look_ahead_ground = current_ground_y
        
        if is_on_hole:
            # Se cair no buraco, tenta olhar um pouco a frente para manter a camêra estável
            # mas não despenca para o abismo.
            pass
            
        if look_ahead_ground is not None:
             self.target_y = look_ahead_ground - 37
        else:
            # Caso extremo de gap total: mantém a última altura alvo segura
            pass
        
        # LERP Suave (Follow delay)
        # Segue o player no Y para manter o enquadramento centralizado
        self.y += (self.target_y - self.y) * 4.5 * dt
        
        # Zoom Suave
        self.zoom += (self.target_zoom - self.zoom) * 1.5 * dt
        
        # Look ahead horizontal baseado na velocidade
        target_look_ahead = current_speed * 0.12
        self.look_ahead += (target_look_ahead - self.look_ahead) * 2.0 * dt

def reset_game(player, monster_manager, biome_manager, bg_manager, camera):
    pygame.mixer.stop()
    try:
        pygame.mixer.music.play(-1)
        from core import state; state.current_music_volume = 0 # LERPs to full gently on startup
    except: pass
    biome_manager.reset()
    monster_manager.reset()
    bg_manager.current_bg = bg_manager.backgrounds["plains"]
    bg_manager.previous_bg = None
    bg_manager.transition_progress = 1.0
    initial_y = biome_manager.get_ground_height(100 + biome_manager.camera_offset)
    if initial_y is None: initial_y = 400 # Fallback de proteção
    player.__init__(100, initial_y)
    camera.y = initial_y
    camera.target_y = initial_y
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
    tutorial_ui = TutorialUI(WIDTH, HEIGHT)
    options_ui = OptionsUI(WIDTH, HEIGHT)
    pause_ui = PauseUI(WIDTH, HEIGHT)
    biome_manager = BiomeManager()
    bg_manager = BackgroundManager()
    camera = Camera(WIDTH, HEIGHT)
    
    # Pre-load fonts to prevent memory leaks/crashes in the EXE
    font_small = pygame.font.Font(None, 28)
    font_medium = pygame.font.Font(None, 36)
    font_large = pygame.font.Font(None, 48)
    font_giant = pygame.font.Font(None, 64)
    
    ending_ui = EndingUI(WIDTH, HEIGHT, font_small, font_giant, font_medium)
    story_ui = StoryUI(WIDTH, HEIGHT, font_small, font_large, font_medium)
    
    self_font_medium = font_medium # Local reference for main loop
    
    # Sound initialization
    audio_system = {}
    try:
        pygame.mixer.init()
        pygame.mixer.set_num_channels(8) # Garante que temos canais suficientes
        voice_channel = pygame.mixer.Channel(0) # Canal exclusivo para vozes/falas
        audio_system['voice_channel'] = voice_channel
        
        def load_sound(name):
            path = resource_path(f"assets/audio/{name}")
            if os.path.exists(path):
                return pygame.mixer.Sound(path)
            return None
            
        audio_system['fala1'] = load_sound("fala1.wav")
        audio_system['fala2'] = load_sound("fala2.mp3")
        audio_system['fala3'] = load_sound("fala3.wav")
        # audio_system['dash'] = load_sound("dash.wav")
        # if audio_system.get('dash'): audio_system['dash'].set_volume(0.2)
        audio_system['intro'] = load_sound("intro.wav")
        audio_system['avalanche'] = load_sound("avalanche.wav")
        
        music_path = resource_path("assets/audio/theme.mp3")
        if os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(state.music_volume)
                pygame.mixer.music.play(-1) # Loop infinito
            except Exception as e:
                print(f"Error loading theme: {e}")
                
        # Kept the old success singing if needed
        sound_path = resource_path("assets/sing.wav")
        audio_system['sing'] = pygame.mixer.Sound(sound_path) if os.path.exists(sound_path) else None
    except Exception as e:
        print(f"Error loading audio: {e}")
        
    state.audio_system = audio_system
    sing_sound = audio_system.get('sing')
    
    initial_y = biome_manager.get_ground_height(100 + biome_manager.camera_offset)
    if initial_y is None: initial_y = 400
    player = Player(100, initial_y)
    camera.y = initial_y
    
    monster_manager = MonsterManager()
    particle_manager = ParticleManager(WIDTH, HEIGHT)
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        dt = min(dt, 0.05) # Limitador de tempo de frame para estabilidade e combate de spikes
        click_pos = None
        
        # --- AUDIO DUCKING (Smooth music volume) ---
        if state.current_state not in [state.GameState.ENDING, state.GameState.GAME_OVER]:
            if hasattr(state, 'audio_system') and 'voice_channel' in state.audio_system:
                target_vol = state.music_volume
                
                # Diminui The Theme se o Voice Channel estiver rodando a introdução narrativa ou alguma fala do sapo/bode
                if state.audio_system['voice_channel'].get_busy():
                    target_vol = 0.0
                    
                if not hasattr(state, 'current_music_volume'):
                    state.current_music_volume = state.music_volume
                    
                if abs(state.current_music_volume - target_vol) > 0.01:
                    state.current_music_volume += (target_vol - state.current_music_volume) * 4.0 * dt
                    try:
                        pygame.mixer.music.set_volume(state.current_music_volume)
                    except: pass
        # ---------------------------------------------
        
        # 1. INPUT
        jump_pressed = False
        dash_pressed = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                state.current_state = state.GameState.EXIT
            
            if state.current_state == state.GameState.OPTIONS:
                options_ui.handle_event(event, pygame.mouse.get_pos())
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click_pos = event.pos
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    jump_pressed = True
                elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT or event.key == pygame.K_x:
                    dash_pressed = True
                elif event.key == pygame.K_ESCAPE:
                    if state.current_state == state.GameState.PLAYING:
                        state.current_state = state.GameState.PAUSED
                        try: pygame.mixer.pause()
                        except: pass
                    elif state.current_state == state.GameState.PAUSED:
                        state.current_state = state.GameState.PLAYING
                        try: pygame.mixer.unpause()
                        except: pass
                    
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
                        state.current_state = state.GameState.PAUSED
                        try: pygame.mixer.pause()
                        except: pass
                    elif state.current_state == state.GameState.PAUSED:
                        state.current_state = state.GameState.PLAYING
                        try: pygame.mixer.unpause()
                        except: pass
                elif new_state:
                    try: pygame.mixer.unpause()
                    except: pass
                    state.current_state = getattr(state.GameState, new_state)
                        
        elif state.current_state == state.GameState.TUTORIAL:
            if click_pos:
                new_state = tutorial_ui.handle_click(click_pos)
                if new_state: state.current_state = getattr(state.GameState, new_state)
                
        elif state.current_state == state.GameState.OPTIONS:
            if click_pos:
                new_state = options_ui.handle_click(click_pos)
                if new_state: state.current_state = getattr(state.GameState, new_state)

        elif state.current_state == state.GameState.STORY:
            if not hasattr(state, 'intro_playing'):
                state.intro_playing = True
                if state.audio_system.get('intro') and state.audio_system.get('voice_channel'):
                    # Toca a intro no canal exclusivo de vozes
                    state.audio_system['voice_channel'].play(state.audio_system['intro'])
                    
            if click_pos:
                new_state = story_ui.handle_click(click_pos)
                if new_state:
                    if state.audio_system.get('voice_channel'):
                        state.audio_system['voice_channel'].stop()
                        
                    state.current_state = getattr(state.GameState, new_state)
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

        elif state.current_state == state.GameState.PAUSED:
            if click_pos:
                new_state = pause_ui.handle_click(click_pos)
                if new_state == "PLAYING":
                    state.current_state = state.GameState.PLAYING
                    try: pygame.mixer.unpause()
                    except: pass
                elif new_state == "RESTART":
                    state.current_state = state.GameState.PLAYING
                    reset_game(player, monster_manager, biome_manager, bg_manager, camera)
                    try: pygame.mixer.unpause()
                    except: pass
                elif new_state == "MENU":
                    state.current_state = state.GameState.MENU
                    try: pygame.mixer.stop()
                    except: pass

        elif state.current_state == state.GameState.PLAYING:
            # 0. CONTROLAR ZOOM E ESTADOS ESPECIAIS (Avalanche)
            if biome_manager.is_avalanche:
                camera.target_zoom = 0.65
                # Screen shake sutil na avalanche
                camera.y += random.uniform(-2, 2)
            elif biome_manager.is_final_stretch:
                camera.target_zoom = 1.0 # Volta ao normal
            else:
                camera.target_zoom = 1.0
                
            # A velocidade real é a soma da velocidade base com o momentum do player
            raw_total_speed = biome_manager.current_speed + player.momentum
            
            # FILTRO DE SUAVIZAÇÃO GLOBAL DE VELOCIDADE (Anti-Boost)
            # Garante que a velocidade do mundo não salte bruscamente
            if not hasattr(state, 'smooth_speed'): state.smooth_speed = raw_total_speed
            state.smooth_speed += (raw_total_speed - state.smooth_speed) * 0.8 * dt
            total_speed = state.smooth_speed
            
            # 0. UPDATE BIOME E DISTÂNCIA (Sincronizado)
            biome_manager.update(dt, total_speed)
            
            # 0. VERIFICAR SE O BAÚ FOI ATINGIDO (Transição para Ending)
            collision_result = monster_manager.check_collision(player.rect)
            
            # Garantia de Forçar o Ending
            current_player_world_x = player.rect.centerx + biome_manager.camera_offset
            if monster_manager.final_chest and current_player_world_x > monster_manager.final_chest.world_x:
                monster_manager.final_chest.opened = True
                collision_result = "ENDING"
                
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
            # (Removido incremento duplicado de offset aqui, ja tratado no biome.update)
            
            bg_manager.set_biome(current_biome.name)
            bg_manager.update(total_speed, dt)
            
            # STATE PIPELINE DE HABILIDADES
            player.handle_input(dt, keys, jump_pressed, dash_pressed, current_biome.friction)
            
            # 2. UPDATES
            player.update(dt, biome_manager.camera_offset, biome_manager.get_ground_height, biome_manager.get_ground_slope)
            
            # Verificar se o jogador está sobre um buraco
            player_world_x = player.rect.centerx + biome_manager.camera_offset
            raw_ground_y = biome_manager.get_raw_ground_height(player_world_x)
            current_ground_y = biome_manager.get_ground_height(player_world_x)
            is_on_hole = current_ground_y is None
            
            camera.update(player.rect, total_speed, dt, is_on_hole, raw_ground_y)
            
            # Suprimir monstros na reta final (deixa os monstros na avalanche)
            stop_monsters = biome_manager.start_phase or biome_manager.is_final_stretch
            monster_manager.update(dt, current_biome, total_speed, biome_manager.camera_offset, biome_manager.get_ground_height, biome_manager.get_ground_slope, stop_monsters)
            
            # Efeito de Avalanche nas partículas
            particle_mode = "avalanche" if biome_manager.is_avalanche else current_biome.name
            particle_manager.update(dt, particle_mode, biome_manager.camera_offset, camera.y)
            
            # 1. VERIFICAR MORTE (COLISÃO OU QUEDA)
            # A morte ocorre se:
            # - Bateu em inimigo (collision_result == True)
            # - Caiu no buraco (está mais abaixo que o chão teórico)
            # - Foi engolido pela avalanche (se estiver muito à esquerda na tela)
            # - Caiu muito abaixo da tela (fallback)
            player_screen_y = player.rect.centery * camera.zoom + ((HEIGHT * 0.8) - camera.y * camera.zoom)
            player_screen_x = (player.rect.centerx - 100) * camera.zoom + 100
            
            # Avalanche catch check: A frente da avalanche está em base_x ≈ 50
            is_caught_by_avalanche = biome_manager.is_avalanche and player_screen_x < 50
            
            if (collision_result == True or 
                player.rect.top > raw_ground_y + 150 or 
                player_screen_y > HEIGHT + 150 or
                is_caught_by_avalanche):
                state.current_state = state.GameState.GAME_OVER
                pygame.mixer.stop()
                try: pygame.mixer.music.stop()
                except: pass
                
            # 3. VERIFICAR SPAWN DO BAÚ FINAL
            # Agora o spawn ocorre no final da reta final (is_final_stretch)
            if biome_manager.is_final_stretch and not monster_manager.final_chest:
                # Spawn 1000 pixels à frente do ponto de início da reta final
                spawn_x = biome_manager.final_trigger_x + 800
                ground_y = biome_manager.get_ground_height(spawn_x)
                if ground_y:
                    monster_manager.spawn_final_chest(spawn_x, ground_y)

        # 3. RENDERING
        # Limpar a tela para evitar efeito de "rastro" (sprites fantasmas)
        screen.fill((135, 206, 235))
        
        if state.current_state == state.GameState.MENU:
            menu_ui.draw(screen)
            
        elif state.current_state == state.GameState.STORY:
            story_ui.draw(screen)
            
        elif state.current_state == state.GameState.TUTORIAL:
            tutorial_ui.draw(screen)
            
        elif state.current_state == state.GameState.OPTIONS:
            options_ui.draw(screen)
            
        elif state.current_state in [state.GameState.PLAYING, state.GameState.PAUSED]:
            bg_manager.draw(screen)
            biome_manager.draw_ground(screen, camera)
            biome_manager.draw_avalanche(screen, camera)
            particle_manager.draw(screen, camera, biome_manager.camera_offset)
            monster_manager.draw(screen, camera)
            player.draw(screen, camera)
            
            # Use pre-loaded font
            score_text = self_font_medium.render(f"Biome: {biome_manager.get_current().name.capitalize()} | Time: {int(biome_manager.total_time_elapsed)}s", True, (0,0,0))
            screen.blit(score_text, (10, 10))
            
            if state.current_state == state.GameState.PAUSED:
                pause_ui.draw(screen)
            
        elif state.current_state == state.GameState.GAME_OVER:
            bg_manager.draw(screen)
            biome_manager.draw_ground(screen, camera)
            biome_manager.draw_avalanche(screen, camera)
            particle_manager.draw(screen, camera, biome_manager.camera_offset)
            monster_manager.draw(screen, camera)
            player.draw(screen, camera)
            
            game_over_ui.draw(screen)

        elif state.current_state == state.GameState.ENDING:
            # Renderiza o mundo estático ao fundo
            bg_manager.draw(screen)
            biome_manager.draw_ground(screen, camera)
            monster_manager.draw(screen, camera)
            player.draw(screen, camera)
            
            # Fade and Text
            if state.fade_alpha < 255:
                state.fade_alpha = min(255, state.fade_alpha + 150 * dt)
                
            ending_ui.draw(screen)
            
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
