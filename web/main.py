import pygame
import random
import math
import asyncio
from enum import Enum

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
OCEAN_BLUE = (64, 164, 223)  # Light blue for ocean
YELLOW = (255, 255, 0)

class BoatType(Enum):
    FAST = 1  # Red boat, goes to red port
    SLOW = 2  # Blue boat, goes to blue port

class Boat:
    def __init__(self, x, y, boat_type, initial_direction):
        self.x = x
        self.y = y
        self.boat_type = boat_type
        self.base_speed = 3 if boat_type == BoatType.FAST else 2
        self.speed = 1  # Start with slow speed for initial path
        self.path = []
        self.current_path_index = 0
        self.color = RED if boat_type == BoatType.FAST else BLUE
        self.radius = 20
        self.out_of_bounds = False
        self.is_selected = False
        self.alpha = 255
        self.fading = False
        self.fade_speed = 8
        self.scale = 1.0
        self.scale_speed = 0.03
        
        # Add initial straight-line path
        if initial_direction == 'left':
            target_x = x + SCREEN_WIDTH//2
            target_y = y
        elif initial_direction == 'right':
            target_x = x - SCREEN_WIDTH//2
            target_y = y
        elif initial_direction == 'top':
            target_x = x
            target_y = y + SCREEN_HEIGHT//2
        else:  # bottom
            target_x = x
            target_y = y - SCREEN_HEIGHT//2
            
        self.path = [(target_x, target_y)]

    def update(self):
        if self.fading:
            self.alpha -= self.fade_speed
            self.scale -= self.scale_speed
            if self.alpha <= 0 or self.scale <= 0:
                return True
            return False

        if self.is_selected:
            return False

        if self.path and self.current_path_index < len(self.path):
            target = self.path[self.current_path_index]
            dx = target[0] - self.x
            dy = target[1] - self.y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < self.speed:
                self.current_path_index += 1
                if self.current_path_index >= len(self.path):
                    self.speed = self.base_speed
            else:
                self.x += (dx/distance) * self.speed
                self.y += (dy/distance) * self.speed

        if (self.x < 0 or self.x > SCREEN_WIDTH or 
            self.y < 0 or self.y > SCREEN_HEIGHT):
            self.out_of_bounds = True

    def draw(self, screen, fast_boat_img, slow_boat_img):
        if self.fading:
            boat_img = fast_boat_img if self.boat_type == BoatType.FAST else slow_boat_img
            current_size = int(40 * self.scale)
            if current_size <= 0:
                return
            
            scaled_img = pygame.transform.scale(boat_img, (current_size, current_size))
            scaled_img.set_alpha(self.alpha)
            
            if self.path and self.current_path_index < len(self.path):
                target = self.path[self.current_path_index]
                angle = math.degrees(math.atan2(target[1] - self.y, target[0] - self.x))
                rotated_img = pygame.transform.rotate(scaled_img, -angle)
                screen.blit(rotated_img, (self.x - rotated_img.get_width()//2, 
                                        self.y - rotated_img.get_height()//2))
            else:
                screen.blit(scaled_img, (self.x - scaled_img.get_width()//2, 
                                       self.y - scaled_img.get_height()//2))
        else:
            boat_img = fast_boat_img if self.boat_type == BoatType.FAST else slow_boat_img
            if self.path and self.current_path_index < len(self.path):
                target = self.path[self.current_path_index]
                angle = math.degrees(math.atan2(target[1] - self.y, target[0] - self.x))
                rotated_img = pygame.transform.rotate(boat_img, -angle)
                screen.blit(rotated_img, (self.x - rotated_img.get_width()//2, 
                                        self.y - rotated_img.get_height()//2))
            else:
                screen.blit(boat_img, (self.x - boat_img.get_width()//2, 
                                     self.y - boat_img.get_height()//2))

    def collides_with(self, other_boat):
        distance = math.sqrt((self.x - other_boat.x)**2 + (self.y - other_boat.y)**2)
        return distance < (self.radius + other_boat.radius)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Boat Navigation Game")
        self.clock = pygame.time.Clock()
        self.reset_game()

    def reset_game(self):
        self.boats = []
        self.current_path = []
        self.drawing = False
        self.score = 0
        self.game_over = False
        self.fading_boats = []
        self.selected_boat = None
        self.last_point = None
        
        self.port1 = (SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT//2)
        self.port2 = (SCREEN_WIDTH//2 + 50, SCREEN_HEIGHT//2)
        
        self.fast_boat_img = pygame.image.load('fast_boat.png')
        self.slow_boat_img = pygame.image.load('slow_boat.png')
        self.island_img = pygame.image.load('island.png')
        
        self.fast_boat_img = pygame.transform.scale(self.fast_boat_img, (40, 40))
        self.slow_boat_img = pygame.transform.scale(self.slow_boat_img, (40, 40))
        self.island_img = pygame.transform.scale(self.island_img, (200, 200))

    def find_nearest_boat(self, mouse_pos):
        """Find the nearest boat to the mouse position"""
        nearest_boat = None
        nearest_dist = float('inf')
        for boat in self.boats:
            dist = math.dist((boat.x, boat.y), mouse_pos)
            if dist < nearest_dist and dist < 50:  # Only select if within 50 pixels
                nearest_dist = dist
                nearest_boat = boat
        return nearest_boat

    def spawn_boat(self):
        side = random.choice(['left', 'right', 'top', 'bottom'])
        boat_type = random.choice([BoatType.FAST, BoatType.SLOW])
        
        if side == 'left':
            x, y = 0, random.randint(0, SCREEN_HEIGHT)
        elif side == 'right':
            x, y = SCREEN_WIDTH, random.randint(0, SCREEN_HEIGHT)
        elif side == 'top':
            x, y = random.randint(0, SCREEN_WIDTH), 0
        else:
            x, y = random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT
            
        self.boats.append(Boat(x, y, boat_type, side))

    def check_collisions(self):
        for i, boat1 in enumerate(self.boats):
            for boat2 in self.boats[i+1:]:
                if boat1.collides_with(boat2):
                    print("Collision detected! Game Over!")
                    self.game_over = True
                    return True
        return False

    def check_port_collision(self, boat):
        port_radius = 35
        if boat.boat_type == BoatType.FAST:
            distance = math.dist((boat.x, boat.y), self.port1)
            if distance < port_radius:
                print(f"Red boat reached port at distance {distance}")
                return True
        elif boat.boat_type == BoatType.SLOW:
            distance = math.dist((boat.x, boat.y), self.port2)
            if distance < port_radius:
                print(f"Blue boat reached port at distance {distance}")
                return True
        return False

    def smooth_mouse_path(self, new_point):
        if not self.last_point:
            self.last_point = new_point
            return new_point
        
        smoothed_x = (self.last_point[0] + new_point[0]) // 2
        smoothed_y = (self.last_point[1] + new_point[1]) // 2
        self.last_point = (smoothed_x, smoothed_y)
        return self.last_point

    def draw_dotted_line(self, points, color=BLACK):
        if len(points) < 2:
            return
            
        for i in range(len(points) - 1):
            start = points[i]
            end = points[i + 1]
            
            distance = math.dist(start, end)
            num_dots = int(distance / 5)
            
            for j in range(num_dots):
                t = j / num_dots
                x = start[0] + t * (end[0] - start[0])
                y = start[1] + t * (end[1] - start[1])
                
                if j % 2 == 0:
                    pygame.draw.circle(self.screen, color, (int(x), int(y)), 3)

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0,0))
        
        font = pygame.font.Font(None, 74)
        text = font.render('Game Over!', True, WHITE)
        score_text = font.render(f'Final Score: {self.score}', True, WHITE)
        restart_text = font.render('Press R to Restart', True, WHITE)
        
        self.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2 - 100))
        self.screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, SCREEN_HEIGHT//2))
        self.screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 100))

    async def run(self):
        running = True
        spawn_timer = 0
        spawn_interval = 3000

        while running:
            current_time = pygame.time.get_ticks()
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.game_over:
                        print("Restarting game")
                        self.reset_game()
                        spawn_timer = current_time
                
                # Handle mouse events if game is not over
                if not self.game_over:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        # Try to select a boat
                        self.selected_boat = self.find_nearest_boat(mouse_pos)
                        if self.selected_boat:
                            print("Boat selected")
                            self.selected_boat.is_selected = True
                            self.drawing = True
                            self.current_path = [mouse_pos]
                    
                    elif event.type == pygame.MOUSEBUTTONUP:
                        if self.drawing and self.selected_boat and len(self.current_path) > 1:
                            print("Path completed")
                            self.selected_boat.path = self.current_path.copy()
                            self.selected_boat.current_path_index = 0
                            self.selected_boat.speed = self.selected_boat.base_speed
                            self.selected_boat.is_selected = False
                        elif self.selected_boat:
                            self.selected_boat.is_selected = False
                        self.drawing = False
                        self.selected_boat = None
                        self.current_path = []
                        self.last_point = None
                    
                    elif event.type == pygame.MOUSEMOTION and self.drawing:
                        smoothed_point = self.smooth_mouse_path(mouse_pos)
                        if not self.current_path or \
                           math.dist(smoothed_point, self.current_path[-1]) > 10:
                            self.current_path.append(smoothed_point)

            # Game logic updates
            if not self.game_over:
                # Spawn new boats
                if current_time - spawn_timer > spawn_interval:
                    self.spawn_boat()
                    spawn_timer = current_time
                    spawn_interval = max(1000, spawn_interval - 100)

                # Check for collisions
                if self.check_collisions():
                    print("Game Over!")
                    continue
                
                # Update boats
                for boat in self.boats[:]:
                    boat.update()
                    
                    if boat.out_of_bounds:
                        boat.fading = True
                        self.fading_boats.append(boat)
                        self.boats.remove(boat)
                        continue
                    
                    # Check for port collisions
                    if self.check_port_collision(boat):
                        boat.fading = True
                        self.fading_boats.append(boat)
                        self.boats.remove(boat)
                        self.score += 1

            # Always update fading boats
            for boat in self.fading_boats[:]:
                if boat.update():
                    self.fading_boats.remove(boat)

            # Draw everything
            self.screen.fill(OCEAN_BLUE)
            
            # Draw the island and ports
            island_pos = (SCREEN_WIDTH//2 - self.island_img.get_width()//2, 
                         SCREEN_HEIGHT//2 - self.island_img.get_height()//2)
            self.screen.blit(self.island_img, island_pos)
            pygame.draw.circle(self.screen, RED, self.port1, 35)
            pygame.draw.circle(self.screen, BLUE, self.port2, 35)

            # Draw current path being drawn
            if self.drawing and len(self.current_path) > 1:
                self.draw_dotted_line(self.current_path, WHITE)

            # Draw all boats and their paths
            for boat in self.boats + self.fading_boats:
                if boat.path and not boat.fading:
                    self.draw_dotted_line(boat.path, boat.color)
                if boat.is_selected:
                    pygame.draw.circle(self.screen, WHITE, 
                                    (int(boat.x), int(boat.y)), 
                                    boat.radius + 8, 2)
                boat.draw(self.screen, self.fast_boat_img, self.slow_boat_img)

            # Draw score
            font = pygame.font.Font(None, 36)
            score_text = font.render(f'Score: {self.score}', True, BLACK)
            self.screen.blit(score_text, (10, 10))

            # Draw game over screen if game is over
            if self.game_over:
                self.draw_game_over()

            pygame.display.flip()
            self.clock.tick(FPS)
            
            # Required for web
            await asyncio.sleep(0)

async def main():
    game = Game()
    await game.run()

if __name__ == '__main__':
    asyncio.run(main())
