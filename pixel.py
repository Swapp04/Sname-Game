import pygame
import random
import sys
import time
import math
import json
import os

# Initialize pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
GAME_SPEED = 10  # Frames per second

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 150, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)
GOLD = (255, 215, 0)
PURPLE = (128, 0, 128)
YELLOW = (255, 255, 0)

# Background and textures
BG_COLOR = (10, 20, 30)  # Darker blue-black
GRID_COLOR = (30, 40, 50)  # Slightly lighter than background

# Directions
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Enhanced Snake Game")

# Font for text
font = pygame.font.SysFont('Arial', 25)
large_font = pygame.font.SysFont('Arial', 50)
small_font = pygame.font.SysFont('Arial', 16)

# Clock for controlling the frame rate
clock = pygame.time.Clock()

# Game states
MENU = "menu"
PLAYING = "playing"
PAUSED = "paused"
GAME_OVER = "game_over"
TUTORIAL = "tutorial"

# Difficulty settings
DIFFICULTIES = {
    "Easy": {"speed": 8, "power_up_chance": 0.015, "score_multiplier": 1.0},
    "Normal": {"speed": 10, "power_up_chance": 0.01, "score_multiplier": 1.5},
    "Hard": {"speed": 12, "power_up_chance": 0.008, "score_multiplier": 2.0}
}

# High score file
HIGH_SCORE_FILE = "high_scores.json"

def load_high_scores():
    if os.path.exists(HIGH_SCORE_FILE):
        with open(HIGH_SCORE_FILE, 'r') as f:
            return json.load(f)
    return {"Easy": 0, "Normal": 0, "Hard": 0}

def save_high_scores(scores):
    with open(HIGH_SCORE_FILE, 'w') as f:
        json.dump(scores, f)

# Sound functionality has been completely removed

class Particle:
    def __init__(self, x, y, color, size=3, speed=2):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.speed = speed
        self.angle = random.uniform(0, 2 * math.pi)
        self.lifetime = random.randint(10, 30)
    
    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.lifetime -= 1
        self.size = max(0, self.size - 0.1)
        return self.lifetime > 0 and self.size > 0
    
    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))

class ParticleSystem:
    def __init__(self):
        self.particles = []
    
    def add_particles(self, x, y, color, count=10):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))
    
    def update(self):
        self.particles = [p for p in self.particles if p.update()]
    
    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

class PowerUp:
    def __init__(self):
        self.position = (0, 0)
        self.color = GOLD
        self.active = False
        self.type = None
        self.spawn_time = 0
        self.duration = 10000  # 10 seconds in milliseconds
    
    def activate(self):
        self.active = True
        self.spawn_time = pygame.time.get_ticks()
        self.type = random.choice(['speed', 'slow', 'invincible', 'double_points'])
        self.randomize_position()
    
    def randomize_position(self):
        self.position = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
    
    def is_expired(self):
        return pygame.time.get_ticks() - self.spawn_time > self.duration
    
    def draw(self, surface):
        if not self.active:
            return
            
        # Flash the power-up when it's about to expire
        remaining = self.duration - (pygame.time.get_ticks() - self.spawn_time)
        if remaining < 3000 and (remaining // 200) % 2 == 0:
            return
            
        rect = pygame.Rect((self.position[0] * GRID_SIZE, self.position[1] * GRID_SIZE), (GRID_SIZE, GRID_SIZE))
        
        # Draw different power-ups with different appearances
        if self.type == 'speed':
            pygame.draw.rect(surface, BLUE, rect)
            pygame.draw.polygon(surface, WHITE, [
                (self.position[0] * GRID_SIZE + GRID_SIZE//2, self.position[1] * GRID_SIZE + 2),
                (self.position[0] * GRID_SIZE + GRID_SIZE - 2, self.position[1] * GRID_SIZE + GRID_SIZE//2),
                (self.position[0] * GRID_SIZE + GRID_SIZE//2, self.position[1] * GRID_SIZE + GRID_SIZE - 2),
                (self.position[0] * GRID_SIZE + 2, self.position[1] * GRID_SIZE + GRID_SIZE//2)
            ])
        elif self.type == 'slow':
            pygame.draw.rect(surface, PURPLE, rect)
            smaller_rect = pygame.Rect((self.position[0] * GRID_SIZE + 5, self.position[1] * GRID_SIZE + 5), (GRID_SIZE - 10, GRID_SIZE - 10))
            pygame.draw.rect(surface, WHITE, smaller_rect)
        elif self.type == 'invincible':
            pygame.draw.rect(surface, GOLD, rect)
            pygame.draw.circle(surface, WHITE, (self.position[0] * GRID_SIZE + GRID_SIZE//2, self.position[1] * GRID_SIZE + GRID_SIZE//2), GRID_SIZE//3)
        elif self.type == 'double_points':
            pygame.draw.rect(surface, (255, 105, 180), rect)  # Hot pink
            # Draw a "x2" text
            text = small_font.render("x2", True, WHITE)
            surface.blit(text, (self.position[0] * GRID_SIZE + 5, self.position[1] * GRID_SIZE + 5))

class Snake:
    def __init__(self):
        self.length = 3
        self.positions = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = RIGHT
        self.score = 0
        self.color = GREEN
        self.head_color = DARK_GREEN
        self.next_direction = RIGHT
        self.is_alive = True
        self.power_ups = {
            'speed': {'active': False, 'end_time': 0},
            'slow': {'active': False, 'end_time': 0},
            'invincible': {'active': False, 'end_time': 0},
            'double_points': {'active': False, 'end_time': 0}
        }
        self.trail = []
        self.trail_length = 5
        self.movement_effect = 0  # For smooth movement animation
        self.movement_speed = 0.2  # Speed of movement animation
    
    def get_head_position(self):
        return self.positions[0]
    
    def change_direction(self, direction):
        if self.length > 1 and (direction[0] * -1, direction[1] * -1) == self.direction:
            # Don't allow the snake to reverse on itself
            return
        self.next_direction = direction
    
    def apply_power_up(self, power_up_type):
        duration = 5000  # 5 seconds
        current_time = pygame.time.get_ticks()
        
        # Deactivate conflicting power-ups
        if power_up_type == 'speed' and self.power_ups['slow']['active']:
            self.power_ups['slow']['active'] = False
        elif power_up_type == 'slow' and self.power_ups['speed']['active']:
            self.power_ups['speed']['active'] = False
            
        self.power_ups[power_up_type]['active'] = True
        self.power_ups[power_up_type]['end_time'] = current_time + duration
    
    def update_power_ups(self):
        current_time = pygame.time.get_ticks()
        for power_up_type, status in self.power_ups.items():
            if status['active'] and current_time > status['end_time']:
                status['active'] = False
    
    def move(self):
        if not self.is_alive:
            return
        
        self.direction = self.next_direction
        head = self.get_head_position()
        new_x = (head[0] + self.direction[0]) % GRID_WIDTH
        new_y = (head[1] + self.direction[1]) % GRID_HEIGHT
        new_head = (new_x, new_y)
        
        # Check if the snake hit itself (unless invincible)
        if new_head in self.positions[1:] and not self.power_ups['invincible']['active']:
            self.is_alive = False
            return
        
        self.positions.insert(0, new_head)
        
        # Add trail particle at the tail position
        if len(self.positions) > self.length:
            tail = self.positions.pop()
            self.trail.append((tail[0] * GRID_SIZE + GRID_SIZE//2, tail[1] * GRID_SIZE + GRID_SIZE//2))
            if len(self.trail) > self.trail_length:
                self.trail.pop(0)
        
        # Update movement effect
        self.movement_effect = (self.movement_effect + self.movement_speed) % 1
    
    def grow(self, points=10):
        self.length += 1
        points_multiplier = 2 if self.power_ups['double_points']['active'] else 1
        self.score += points * points_multiplier
    
    def draw(self, surface):
        # Draw trail first so it appears behind the snake
        for i, pos in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)))  # Fade out older trail particles
            color = (0, alpha, 0)  # Green with varying alpha
            size = int(GRID_SIZE * 0.7 * (i / len(self.trail)))
            pygame.draw.circle(surface, color, pos, size)
        
        # Draw snake segments
        for i, p in enumerate(self.positions):
            rect = pygame.Rect((p[0] * GRID_SIZE, p[1] * GRID_SIZE), (GRID_SIZE, GRID_SIZE))
            
            # Apply visual effects for power-ups
            segment_color = self.color
            if self.power_ups['invincible']['active']:
                # Pulsating gold effect for invincibility
                pulse = (math.sin(pygame.time.get_ticks() / 100) + 1) / 2
                segment_color = (
                    int(self.color[0] * (1-pulse) + GOLD[0] * pulse),
                    int(self.color[1] * (1-pulse) + GOLD[1] * pulse),
                    int(self.color[2] * (1-pulse) + GOLD[2] * pulse)
                )
            
            # Draw the head with a different color
            if i == 0:
                head_color = DARK_GREEN
                if self.power_ups['invincible']['active']:
                    head_color = GOLD
                elif self.power_ups['speed']['active']:
                    head_color = BLUE
                elif self.power_ups['slow']['active']:
                    head_color = PURPLE
                
                # Draw a slightly rounded rectangle for the head
                pygame.draw.rect(surface, head_color, rect, border_radius=3)
                
                # Draw eyes
                eye_size = GRID_SIZE // 5
                eye_offset_x = GRID_SIZE // 3
                eye_offset_y = GRID_SIZE // 3
                
                # Adjust eye position based on direction
                if self.direction == UP:
                    eye1 = pygame.Rect(p[0] * GRID_SIZE + eye_offset_x, p[1] * GRID_SIZE + eye_offset_y, eye_size, eye_size)
                    eye2 = pygame.Rect(p[0] * GRID_SIZE + GRID_SIZE - eye_offset_x - eye_size, p[1] * GRID_SIZE + eye_offset_y, eye_size, eye_size)
                elif self.direction == DOWN:
                    eye1 = pygame.Rect(p[0] * GRID_SIZE + eye_offset_x, p[1] * GRID_SIZE + GRID_SIZE - eye_offset_y - eye_size, eye_size, eye_size)
                    eye2 = pygame.Rect(p[0] * GRID_SIZE + GRID_SIZE - eye_offset_x - eye_size, p[1] * GRID_SIZE + GRID_SIZE - eye_offset_y - eye_size, eye_size, eye_size)
                elif self.direction == LEFT:
                    eye1 = pygame.Rect(p[0] * GRID_SIZE + eye_offset_y, p[1] * GRID_SIZE + eye_offset_x, eye_size, eye_size)
                    eye2 = pygame.Rect(p[0] * GRID_SIZE + eye_offset_y, p[1] * GRID_SIZE + GRID_SIZE - eye_offset_x - eye_size, eye_size, eye_size)
                else:  # RIGHT
                    eye1 = pygame.Rect(p[0] * GRID_SIZE + GRID_SIZE - eye_offset_y - eye_size, p[1] * GRID_SIZE + eye_offset_x, eye_size, eye_size)
                    eye2 = pygame.Rect(p[0] * GRID_SIZE + GRID_SIZE - eye_offset_y - eye_size, p[1] * GRID_SIZE + GRID_SIZE - eye_offset_x - eye_size, eye_size, eye_size)
                
                pygame.draw.rect(surface, WHITE, eye1)
                pygame.draw.rect(surface, WHITE, eye2)
                
                # Add pupils that look in the direction the snake is moving
                pupil_size = eye_size // 2
                pupil_offset = eye_size // 4
                
                if self.direction == UP:
                    pupil_offset_y = 0
                    pupil_offset_x = pupil_offset
                elif self.direction == DOWN:
                    pupil_offset_y = pupil_offset * 2
                    pupil_offset_x = pupil_offset
                elif self.direction == LEFT:
                    pupil_offset_y = pupil_offset
                    pupil_offset_x = 0
                else:  # RIGHT
                    pupil_offset_y = pupil_offset
                    pupil_offset_x = pupil_offset * 2
                
                pupil1 = pygame.Rect(eye1.x + pupil_offset_x, eye1.y + pupil_offset_y, pupil_size, pupil_size)
                pupil2 = pygame.Rect(eye2.x + pupil_offset_x, eye2.y + pupil_offset_y, pupil_size, pupil_size)
                
                pygame.draw.rect(surface, BLACK, pupil1)
                pygame.draw.rect(surface, BLACK, pupil2)
            else:
                # Draw body segments
                # Add a gradient effect based on segment position
                gradient_factor = 1 - (i / self.length) * 0.5  # Gradually darker toward the tail
                segment_color = (
                    int(segment_color[0] * gradient_factor),
                    int(segment_color[1] * gradient_factor),
                    int(segment_color[2] * gradient_factor)
                )
                
                # Draw a rounded rectangle for body segments
                pygame.draw.rect(surface, segment_color, rect, border_radius=3)
                
                # Add a highlight to give a 3D effect
                smaller_rect = pygame.Rect((p[0] * GRID_SIZE + 2, p[1] * GRID_SIZE + 2), (GRID_SIZE - 4, GRID_SIZE - 4))
                highlight_color = (
                    min(255, segment_color[0] + 30),
                    min(255, segment_color[1] + 30),
                    min(255, segment_color[2] + 30)
                )
                pygame.draw.rect(surface, highlight_color, smaller_rect, border_radius=2)

class Food:
    def __init__(self):
        self.position = (0, 0)
        self.color = RED
        self.randomize_position()
        self.pulse_size = 0
        self.growing = True
    
    def randomize_position(self):
        self.position = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
    
    def update(self):
        # Create a pulsating effect
        if self.growing:
            self.pulse_size += 0.1
            if self.pulse_size >= 3:
                self.growing = False
        else:
            self.pulse_size -= 0.1
            if self.pulse_size <= 0:
                self.growing = True
    
    def draw(self, surface):
        center_x = self.position[0] * GRID_SIZE + GRID_SIZE // 2
        center_y = self.position[1] * GRID_SIZE + GRID_SIZE // 2
        
        # Draw a pulsating glow around the food
        glow_radius = GRID_SIZE // 2 + self.pulse_size
        pygame.draw.circle(surface, (255, 100, 100, 128), (center_x, center_y), glow_radius)
        
        # Draw the food as an apple shape
        apple_radius = GRID_SIZE // 2 - 2
        pygame.draw.circle(surface, RED, (center_x, center_y), apple_radius)
        
        # Draw a smaller circle inside to give a highlight
        pygame.draw.circle(surface, (255, 50, 50), (center_x - 2, center_y - 2), apple_radius // 2)
        
        # Draw a stem
        stem = pygame.Rect(center_x - 1, center_y - apple_radius - 2, 2, 4)
        pygame.draw.rect(surface, (0, 100, 0), stem)
        
        # Draw a leaf
        leaf_points = [
            (center_x + 2, center_y - apple_radius),
            (center_x + 5, center_y - apple_radius - 3),
            (center_x + 2, center_y - apple_radius - 3)
        ]
        pygame.draw.polygon(surface, (0, 150, 0), leaf_points)

def draw_grid(surface):
    # Draw a nicer grid with a subtle gradient
    for x in range(0, SCREEN_WIDTH, GRID_SIZE):
        alpha = 40 + (x // GRID_SIZE % 2) * 10  # Alternate slightly darker lines
        pygame.draw.line(surface, (*GRID_COLOR, alpha), (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
        alpha = 40 + (y // GRID_SIZE % 2) * 10
        pygame.draw.line(surface, (*GRID_COLOR, alpha), (0, y), (SCREEN_WIDTH, y))

def draw_hud(surface, snake, power_ups_active=None):
    # Draw a semi-transparent HUD at the top
    hud_height = 50
    hud_surface = pygame.Surface((SCREEN_WIDTH, hud_height), pygame.SRCALPHA)
    hud_surface.fill((0, 0, 0, 150))  # Semi-transparent black
    surface.blit(hud_surface, (0, 0))
    
    # Show score
    score_text = font.render(f'Score: {snake.score}', True, WHITE)
    surface.blit(score_text, (10, 10))
    
    # Show length
    length_text = font.render(f'Length: {snake.length}', True, WHITE)
    surface.blit(length_text, (150, 10))
    
    # Show active power-ups
    if power_ups_active:
        x_pos = 300
        for power_up_type, status in snake.power_ups.items():
            if status['active']:
                remaining = (status['end_time'] - pygame.time.get_ticks()) // 1000
                if remaining > 0:
                    power_up_text = font.render(f'{power_up_type.capitalize()}: {remaining}s', True, GOLD)
                    surface.blit(power_up_text, (x_pos, 10))
                    x_pos += 200

def game_over_screen(surface, snake):
    # Create a semi-transparent overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # Semi-transparent black
    surface.blit(overlay, (0, 0))
    
    # Game Over text with a shadow effect
    game_over_text = large_font.render('GAME OVER', True, RED)
    shadow_offset = 3
    shadow_text = large_font.render('GAME OVER', True, BLACK)
    
    text_x = SCREEN_WIDTH // 2 - game_over_text.get_width() // 2
    text_y = SCREEN_HEIGHT // 3
    
    # Draw shadow first, then text on top
    surface.blit(shadow_text, (text_x + shadow_offset, text_y + shadow_offset))
    surface.blit(game_over_text, (text_x, text_y))
    
    # Score text
    score_text = font.render(f'Final Score: {snake.score}', True, WHITE)
    surface.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2))
    
    # Length text
    length_text = font.render(f'Final Length: {snake.length}', True, WHITE)
    surface.blit(length_text, (SCREEN_WIDTH // 2 - length_text.get_width() // 2, SCREEN_HEIGHT // 2 + 30))
    
    # Restart instructions
    restart_text = font.render('Press R to restart or Q to quit', True, WHITE)
    surface.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 80))

def draw_menu(surface, high_scores):
    # Create a semi-transparent overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))
    
    # Title
    title = large_font.render('SNAKE GAME', True, GREEN)
    surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 4))
    
    # Menu options
    options = ['Play', 'Tutorial', 'High Scores', 'Quit']
    for i, option in enumerate(options):
        text = font.render(option, True, WHITE)
        surface.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 + i * 50))
    
    # Show high scores
    scores_text = font.render('High Scores:', True, GOLD)
    surface.blit(scores_text, (SCREEN_WIDTH // 2 - scores_text.get_width() // 2, SCREEN_HEIGHT * 3 // 4))
    
    for i, (difficulty, score) in enumerate(high_scores.items()):
        score_text = small_font.render(f'{difficulty}: {score}', True, WHITE)
        surface.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT * 3 // 4 + 30 + i * 25))

def draw_tutorial(surface):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))
    
    title = large_font.render('How to Play', True, GREEN)
    surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))
    
    instructions = [
        "Use arrow keys or WASD to move the snake",
        "Collect red food to grow and increase your score",
        "Watch out for power-ups:",
        "  - Blue: Speed boost",
        "  - Purple: Slow down",
        "  - Gold: Invincibility",
        "  - Pink: Double points",
        "Press SPACE to pause",
        "Press ESC to return to menu",
        "",
        "Press any key to continue"
    ]
    
    for i, text in enumerate(instructions):
        color = WHITE if i < 2 else GOLD if i == 2 else YELLOW if 3 <= i <= 6 else WHITE
        instruction = small_font.render(text, True, color)
        surface.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 150 + i * 25))

def draw_pause_menu(surface):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))
    
    title = large_font.render('PAUSED', True, WHITE)
    surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 3))
    
    options = ['Resume', 'Restart', 'Main Menu']
    for i, option in enumerate(options):
        text = font.render(option, True, WHITE)
        surface.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 + i * 50))

def main():
    # Load high scores
    high_scores = load_high_scores()
    
    # Game state variables
    game_state = MENU
    difficulty = "Normal"
    selected_option = 0
    
    # Initialize background stars
    stars = [(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), random.random() * 1.5 + 0.5) 
             for _ in range(100)]
    
    while True:
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if game_state == MENU:
                    if event.key == pygame.K_UP:
                        selected_option = (selected_option - 1) % 4
                    elif event.key == pygame.K_DOWN:
                        selected_option = (selected_option + 1) % 4
                    elif event.key == pygame.K_RETURN:
                        if selected_option == 0:
                            game_state = PLAYING
                            snake = Snake()
                            food = Food()
                            power_up = PowerUp()
                            particle_system = ParticleSystem()
                            base_game_speed = DIFFICULTIES[difficulty]["speed"]
                            game_speed = base_game_speed
                            last_move_time = 0
                            power_up_chance = DIFFICULTIES[difficulty]["power_up_chance"]
                        elif selected_option == 1:
                            game_state = TUTORIAL
                        elif selected_option == 2:
                            # Show high scores screen
                            pass
                        elif selected_option == 3:
                            pygame.quit()
                            sys.exit()
                
                elif game_state == TUTORIAL:
                    game_state = MENU
                
                elif game_state == PLAYING:
                    if event.key == pygame.K_ESCAPE:
                        game_state = PAUSED
                        selected_option = 0
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        snake.change_direction(UP)
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        snake.change_direction(DOWN)
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        snake.change_direction(LEFT)
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        snake.change_direction(RIGHT)
                
                elif game_state == PAUSED:
                    if event.key == pygame.K_UP:
                        selected_option = (selected_option - 1) % 3
                    elif event.key == pygame.K_DOWN:
                        selected_option = (selected_option + 1) % 3
                    elif event.key == pygame.K_RETURN:
                        if selected_option == 0:
                            game_state = PLAYING
                        elif selected_option == 1:
                            game_state = PLAYING
                            snake = Snake()
                            food = Food()
                            power_up = PowerUp()
                            base_game_speed = DIFFICULTIES[difficulty]["speed"]
                            game_speed = base_game_speed
                            last_move_time = 0
                            power_up_chance = DIFFICULTIES[difficulty]["power_up_chance"]
                        elif selected_option == 2:
                            game_state = MENU
                
                elif game_state == GAME_OVER:
                    if event.key == pygame.K_r:
                        game_state = PLAYING
                        snake = Snake()
                        food = Food()
                        power_up = PowerUp()
                        base_game_speed = DIFFICULTIES[difficulty]["speed"]
                        game_speed = base_game_speed
                        last_move_time = 0
                        power_up_chance = DIFFICULTIES[difficulty]["power_up_chance"]
                    elif event.key == pygame.K_q:
                        game_state = MENU
        
        # Clear screen
        screen.fill(BG_COLOR)
        
        # Draw background stars
        for i, (x, y, size) in enumerate(stars):
            brightness = 128 + int(127 * math.sin(current_time / 1000 + i))
            color = (brightness, brightness, brightness)
            pygame.draw.circle(screen, color, (int(x), int(y)), int(size))
        
        # Draw grid
        draw_grid(screen)
        
        if game_state == MENU:
            draw_menu(screen, high_scores)
            # Highlight selected option
            options = ['Play', 'Tutorial', 'High Scores', 'Quit']
            text = font.render(options[selected_option], True, GREEN)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 + selected_option * 50))
        
        elif game_state == TUTORIAL:
            draw_tutorial(screen)
        
        elif game_state == PLAYING:
            # Update game logic
            snake.update_power_ups()
            game_speed = adjust_speed(base_game_speed, snake)
            
            if current_time - last_move_time > 1000 / game_speed:
                snake.move()
                last_move_time = current_time
                
                if not snake.is_alive:
                    game_state = GAME_OVER
                    # Update high score if applicable
                    if snake.score > high_scores[difficulty]:
                        high_scores[difficulty] = snake.score
                        save_high_scores(high_scores)
            
            # Update food and power-ups
            food.update()
            
            if snake.get_head_position() == food.position:
                snake.grow(points=10 * DIFFICULTIES[difficulty]["score_multiplier"])
                food.randomize_position()
                
                food_x = food.position[0] * GRID_SIZE + GRID_SIZE // 2
                food_y = food.position[1] * GRID_SIZE + GRID_SIZE // 2
                particle_system.add_particles(food_x, food_y, GREEN, 15)
                
                while food.position in snake.positions or (power_up.active and food.position == power_up.position):
                    food.randomize_position()
                
                if base_game_speed < 20:
                    base_game_speed += 0.2
            
            if power_up.active and snake.get_head_position() == power_up.position:
                snake.apply_power_up(power_up.type)
                power_up.active = False
                
                power_up_x = power_up.position[0] * GRID_SIZE + GRID_SIZE // 2
                power_up_y = power_up.position[1] * GRID_SIZE + GRID_SIZE // 2
                if power_up.type == 'speed':
                    particle_system.add_particles(power_up_x, power_up_y, BLUE, 20)
                elif power_up.type == 'slow':
                    particle_system.add_particles(power_up_x, power_up_y, PURPLE, 20)
                elif power_up.type == 'invincible':
                    particle_system.add_particles(power_up_x, power_up_y, GOLD, 20)
                elif power_up.type == 'double_points':
                    particle_system.add_particles(power_up_x, power_up_y, (255, 105, 180), 20)
            
            if power_up.active and power_up.is_expired():
                power_up.active = False
            
            if not power_up.active and random.random() < power_up_chance and snake.length > 5:
                power_up.activate()
                while power_up.position in snake.positions or power_up.position == food.position:
                    power_up.randomize_position()
            
            particle_system.update()
            
            # Draw game elements
            food.draw(screen)
            if power_up.active:
                power_up.draw(screen)
            snake.draw(screen)
            particle_system.draw(screen)
            draw_hud(screen, snake, True)
        
        elif game_state == PAUSED:
            # Draw game elements in background
            food.draw(screen)
            if power_up.active:
                power_up.draw(screen)
            snake.draw(screen)
            particle_system.draw(screen)
            draw_hud(screen, snake, True)
            draw_pause_menu(screen)
            # Highlight selected option
            options = ['Resume', 'Restart', 'Main Menu']
            text = font.render(options[selected_option], True, GREEN)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 + selected_option * 50))
        
        elif game_state == GAME_OVER:
            food.draw(screen)
            snake.draw(screen)
            particle_system.draw(screen)
            particle_system.update()
            particle_system.draw(screen)
            game_over_screen(screen, snake)
        
        pygame.display.update()
        clock.tick(60)

def adjust_speed(base_speed, snake):
    # Adjust the game speed based on active power-ups
    if snake.power_ups['speed']['active']:
        return base_speed * 1.5
    elif snake.power_ups['slow']['active']:
        return base_speed * 0.5
    else:
        return base_speed

if __name__ == "__main__":
    main()
