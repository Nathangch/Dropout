import os
import pygame

def create_frame(color, size, frame_idx, total_frames, path):
    surface = pygame.Surface(size, pygame.SRCALPHA)
    surface.fill(color)
    
    # Draw a moving white eye/block to verify animation
    eye_x = int((frame_idx / max(1, total_frames - 1)) * (size[0] - 10))
    pygame.draw.rect(surface, (255, 255, 255), (eye_x, size[1]//4, 10, 10))
    
    # Simple outline
    pygame.draw.rect(surface, (0, 0, 0), surface.get_rect(), 2)
    
    pygame.image.save(surface, path)

def main():
    pygame.init()
    # For a headless environment, try to create a dummy display or just don't need it for surfaces.
    # pygame.display.set_mode((1, 1)) # Try not to initialize display unless required
    
    base_dir = "assets/enemies"
    enemies = {
        "wolf": {"color": (120, 120, 120), "size": (50, 30), "frames": 5},
        "scorpion": {"color": (200, 50, 50), "size": (40, 30), "frames": 4},
        "ice_golem": {"color": (100, 200, 255), "size": (60, 60), "frames": 4}
    }
    
    for name, data in enemies.items():
        path = os.path.join(base_dir, name)
        os.makedirs(path, exist_ok=True)
        for i in range(data["frames"]):
            create_frame(data["color"], data["size"], i, data["frames"], os.path.join(path, f"frame_{i}.png"))

if __name__ == "__main__":
    main()
