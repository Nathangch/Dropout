import os
import pygame
import math

def generate_seamless_layer(filename, color, width, height, wave_func=None):
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    if wave_func is None:
        surface.fill(color)
    else:
        # Draw sky/clear background
        # Leave transparent top, fill bottom according to wave
        for x in range(width):
            y = wave_func(x)
            pygame.draw.line(surface, color, (x, y), (x, height))
            
    pygame.image.save(surface, filename)

def generate_sky_gradient(filename, color_top, color_bottom, width, height):
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        t = y / height
        r = int(color_top[0] * (1 - t) + color_bottom[0] * t)
        g = int(color_top[1] * (1 - t) + color_bottom[1] * t)
        b = int(color_top[2] * (1 - t) + color_bottom[2] * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))
    pygame.image.save(surface, filename)

def generate_plains_trees(filename, width, height, p_tree):
    import random
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Base ground curve periodic (Darker green for background depth)
    for x in range(width):
        y = 480 + math.sin(x * p_tree) * 15
        pygame.draw.line(surface, (25, 70, 25), (x, y), (x, height))
        
    # Draw some stylized pine trees
    random.seed(42) 
    for _ in range(35):
        # Aumentei o clamp para garantir que metade da árvore (25px) não passe da fronteira
        x = random.randint(50, width - 50)
        y = int(480 + math.sin(x * p_tree) * 15) - random.randint(0, 10)
        
        # Trunk
        pygame.draw.rect(surface, (101, 67, 33), (x-4, y-10, 8, 20))
        # Leaves Base
        pygame.draw.polygon(surface, (20, 100, 20), [(x, y-40), (x-25, y), (x+25, y)])
        # Leaves Top
        pygame.draw.polygon(surface, (25, 115, 25), [(x, y-60), (x-18, y-15), (x+18, y-15)])
        
    pygame.image.save(surface, filename)

def generate_backgrounds():
    pygame.init()
    
    base_dir = "assets/backgrounds"
    os.makedirs(base_dir, exist_ok=True)
    
    width, height = 1280, 720 # Upgrade resolution
    
    # Períodos modulares exatos baseados em múltiplos de 2*PI / width
    k1 = (math.pi * 2) / width
    k2 = (math.pi * 4) / width
    k3 = (math.pi * 6) / width
    k4 = (math.pi * 8) / width
    
    # 1. Plains (Upgraded Visuals)
    generate_sky_gradient(os.path.join(base_dir, "sky.png"), (100, 150, 230), (210, 235, 255), width, height)
    generate_seamless_layer(os.path.join(base_dir, "mountains.png"), (80, 140, 120), width, height, 
                           lambda x: 350 + math.sin(x * k1) * 80 + math.cos(x * k2) * 40)
    generate_plains_trees(os.path.join(base_dir, "trees.png"), width, height, k4)
                           
    # 2. Desert
    generate_seamless_layer(os.path.join(base_dir, "sky_desert.png"), (244, 164, 96), width, height)
    generate_seamless_layer(os.path.join(base_dir, "dunes.png"), (210, 180, 140), width, height,
                           lambda x: 350 + math.sin(x * k2) * 80)
    
    # Sun (static or moving very slowly)
    sun = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.circle(sun, (255, 223, 0), (600, 200), 50)
    pygame.image.save(sun, os.path.join(base_dir, "sun.png"))
    
    # 3. Snow
    generate_seamless_layer(os.path.join(base_dir, "sky_snow.png"), (200, 230, 255), width, height)
    generate_seamless_layer(os.path.join(base_dir, "snow_mountains.png"), (140, 180, 220), width, height,
                           lambda x: 250 + math.sin(x * k1) * 150 + math.cos(x * k3) * 60)
    generate_seamless_layer(os.path.join(base_dir, "fog.png"), (255, 255, 255, 100), width, height,
                           lambda x: 500 + math.sin(x * k2) * 30)

if __name__ == "__main__":
    generate_backgrounds()
