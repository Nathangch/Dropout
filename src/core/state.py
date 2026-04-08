class GameState:
    MENU = "MENU"
    PLAYING = "PLAYING"
    GAME_OVER = "GAME_OVER"
    ENDING = "ENDING"
    STORY = "STORY"
    EXIT = "EXIT"
    TUTORIAL = "TUTORIAL"
    OPTIONS = "OPTIONS"
    PAUSED = "PAUSED"

current_state = "MENU"
fade_alpha = 0

music_volume = 0.5
sfx_volume = 0.5
