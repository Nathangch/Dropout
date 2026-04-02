class GameState:
    MENU = "MENU"
    STORY = "STORY"
    PLAYING = "PLAYING"
    GAME_OVER = "GAME_OVER"
    ENDING = "ENDING"
    EXIT = "EXIT"

current_state = GameState.MENU
fade_alpha = 0

# Avalanche States
avalanche_active = False
avalanche_running = False
avalanche_timer = 0.0
avalanche_world_x = 0.0
avalanche_triggered_once = False
