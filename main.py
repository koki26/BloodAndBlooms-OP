import pygame
import random
import math
import heapq


"""
Excessive comment lines were used for CTRL + F to find important functions/classes more easily while coding
Every function/class is commented with a space right after #
For easier debugging or testing, edit values that are commented using: " # Edit for cheats and debug " or by pressing
F2 = Toggle debug mode
F3 = Grid
F4 = Paths
F5 = Obstacles

"""

# Initialize pygame
pygame.init()

# Load sounds
gunshot_sound = pygame.mixer.Sound("sounds/gunshot.mp3")
reload_sound = pygame.mixer.Sound("sounds/reload.mp3")
zombie_death_sound = pygame.mixer.Sound("sounds/zombie_death.mp3")
player_hurt_sound = pygame.mixer.Sound("sounds/player_hurt.mp3")
shop_open_sound = pygame.mixer.Sound("sounds/shop_open.mp3")
shop_buy_sound = pygame.mixer.Sound("sounds/shop_buy.mp3")
sound_track = pygame.mixer.Sound("sounds/sound_track.mp3")
start_sound = pygame.mixer.Sound("sounds/start.mp3")
gameover_sound = pygame.mixer.Sound("sounds/gameover.mp3")
background_music = pygame.mixer.Sound("sounds/background.mp3")
crop_planted_sound = pygame.mixer.Sound("sounds/crop_planted.mp3")
crop_harvested_sound = pygame.mixer.Sound("sounds/crop_harvested.mp3")
spitter_attack_sound = pygame.mixer.Sound("sounds/spit.mp3")

# Volumes and set number of chanels
pygame.mixer.set_num_channels(32)
gunshot_sound.set_volume(0.15)
zombie_death_sound.set_volume(0.1)
shop_buy_sound.set_volume(0.2)
shop_open_sound.set_volume(0.1)
sound_track.set_volume(0.3)
start_sound.set_volume(0.3)
gameover_sound.set_volume(0.3)
background_music.set_volume(0.1)
player_hurt_sound.set_volume(0.3)
spitter_attack_sound.set_volume(0.3)

# Screen dimensions
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Blood And Blooms")
icon = pygame.image.load("Images/zombie.png")
pygame.display.set_icon(icon)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BROWN = (139, 69, 19)
LIGHT_GRAY = (200, 200, 200)
YELLOW = (255, 200, 50)  
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
GRAY = (100, 100, 100)

# Fonts
font = pygame.font.Font("04B_30__.TTF", 26)
gameover_font = pygame.font.Font("04B_30__.TTF", 50)
shop_font = pygame.font.Font("04B_30__.TTF", 32)

# Game clock
clock = pygame.time.Clock()
FPS = 60

# DEBUG
DEBUG_MODE = False
DEBUG_SHOW_GRID = False
DEBUG_SHOW_PATHS = False
DEBUG_SHOW_OBSTACLES = False

# Variables
WAVE_TIMEOUT = 60000
WAVE_WARNING_DURATION = 10000 
shop_open_time = 0
time_spent_in_shop = 0
is_shop_open = False 
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
TEXT_BOBBING_INTERVAL = 300
TEXT_BOBBING_STEP = 0.5
TEXT_BOBBING_RANGE = 2
NEXT_WAVE_EVENT = pygame.USEREVENT + 2

COLLISION_RECTS = [ 
    # Graves
    # Left top
    pygame.Rect(74, 122, 76, 16),
    pygame.Rect(69, 138, 66, 18),  
    pygame.Rect(93, 108, 55, 14),

    # 2. Left bot
    pygame.Rect(217, 502, 80, 26),
    pygame.Rect(255, 486, 42, 16),
    pygame.Rect(220, 528, 48, 13),

    # 2. Right top
    pygame.Rect(304, 166, 77, 22),
    pygame.Rect(326, 151, 56, 15),
    pygame.Rect(299, 188, 43, 18),

    # Right top
    pygame.Rect(378, 199, 83, 35),

    # Left Bot
    pygame.Rect(121, 433, 84, 38),

    # 2. Left top
    pygame.Rect(202, 91, 78, 29),
    pygame.Rect(231, 120, 57, 21),

    # 2.Right bot
    pygame.Rect(334, 497, 84, 36),

    # Right bot
    pygame.Rect(544, 456, 77, 34),
    pygame.Rect(554, 442, 32, 14),
    pygame.Rect(574, 490, 43, 16),  

    # Monument walls
    pygame.Rect(880, 459, 274, 27),
    pygame.Rect(1123, 491, 27, 134),
    pygame.Rect(879, 623, 274, 25),
]

MONUMENT_WALLS = [ # Used just for bullet collisions
    pygame.Rect(880, 459, 274, 27),
    pygame.Rect(1123, 491, 27, 134),
    pygame.Rect(879, 623, 274, 25),
]

class PathfindingGrid:
    def __init__(self):
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.zombie_positions = set()  # Track zombie positions
        self.update_obstacles()
    
    def update_obstacles(self):
        # Clear grid
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        
        # Mark graves as obstacles
        for grave in COLLISION_RECTS:
            x1 = grave.left // GRID_SIZE
            y1 = grave.top // GRID_SIZE
            x2 = grave.right // GRID_SIZE
            y2 = grave.bottom // GRID_SIZE
            
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                        self.grid[y][x] = 1  # 1 means obstacle
        
        # Mark zombie positions as temporary obstacles
        for (zx, zy) in self.zombie_positions:
            gx, gy = zx // GRID_SIZE, zy // GRID_SIZE
            if 0 <= gx < GRID_WIDTH and 0 <= gy < GRID_HEIGHT:
                self.grid[gy][gx] = 2  # 2 means temporary zombie obstacle

    def update_zombie_positions(self, zombies):
        self.zombie_positions = set()
        for zombie in zombies:
            # Store center position of each zombie
            self.zombie_positions.add((zombie.rect.centerx, zombie.rect.centery))
        self.update_obstacles()

    def is_walkable(self, x, y):
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
            return self.grid[y][x] != 1  # Walkable if not a permanent obstacle
        return False

    def find_path(self, start_pos, end_pos):
        # Convert to grid coordinates
        start_node = (start_pos[0] // GRID_SIZE, start_pos[1] // GRID_SIZE)
        end_node = (end_pos[0] // GRID_SIZE, end_pos[1] // GRID_SIZE)
        
        # If start or end is in obstacle, find nearest walkable
        if not self.is_walkable(*start_node):
            start_node = self.find_nearest_walkable(*start_node)
        if not self.is_walkable(*end_node):
            end_node = self.find_nearest_walkable(*end_node)
            
        # Use A* algorithm with priority queue for better performance
        open_set = []
        heapq.heappush(open_set, (0, start_node))
        came_from = {}
        
        g_score = {start_node: 0}
        f_score = {start_node: self.heuristic(start_node, end_node)}
        
        open_set_hash = {start_node}  # For quick lookup
        
        while open_set:
            current = heapq.heappop(open_set)[1]
            open_set_hash.remove(current)
            
            if current == end_node:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return [(x * GRID_SIZE + GRID_SIZE//2, y * GRID_SIZE + GRID_SIZE//2) 
                       for (x, y) in path]
                
            for dx, dy in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                if not self.is_walkable(*neighbor):
                    continue
                    
                tentative_g = g_score[current] + (1.4 if dx and dy else 1)  # Diagonal cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, end_node)
                    if neighbor not in open_set_hash:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                        open_set_hash.add(neighbor)
        
        return []  # No path found

    def heuristic(self, a, b):
        # Euclidean distance
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return dx + dy + (math.sqrt(2) - 2) * min(dx, dy)

    def find_nearest_walkable(self, x, y):
        # Find nearest walkable cell using Breadth First Search
        queue = [(x, y)]
        visited = set()
        
        while queue:
            cx, cy = queue.pop(0)
            if self.is_walkable(cx, cy):
                return (cx, cy)
                
            visited.add((cx, cy))
            
            for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
                nx, ny = cx + dx, cy + dy
                if (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and 
                    (nx, ny) not in visited):
                    queue.append((nx, ny))
                    
        return (x, y)  # Fallback

# Player health class system with 3 hearts and invincibility frames
class PlayerHealth:
    def __init__(self):
        self.max_hearts = 3
        self.hearts = 3
        self.pixel_size = 6  
        self.heart_width = 7 * self.pixel_size 
        self.heart_height = 6 * self.pixel_size  
        self.iframes_duration = 1500  
        self.last_hit_time = 0
        self.is_invincible = False
        self.blink_timer = 0
        self.blink_speed = 150  # ms between blinks

        # Pixel design (0=transparent, 1=fill, 2=fill [used to be outline])
        self.heart_pixels = [
            [0,1,1,0,1,1,0],
            [1,2,2,1,2,2,1],
            [1,2,2,2,2,2,1],
            [0,1,2,2,2,1,0],
            [0,0,1,2,1,0,0],
            [0,0,0,1,0,0,0]
        ]

        # Create heart images
        self.heart_images = {
            'full': self.create_heart_image((RED)), 
            'empty': self.create_heart_image((GRAY))
        }

    def create_heart_image(self, fill_color):
        img = pygame.Surface((self.heart_width, self.heart_height), pygame.SRCALPHA)
        
        # Draw fill pixels first (red or gray)
        for y in range(6):
            for x in range(7):
                if self.heart_pixels[y][x]:  # Fill area
                    pygame.draw.rect(img, fill_color, 
                                   (x * self.pixel_size, 
                                    y * self.pixel_size,
                                    self.pixel_size, 
                                    self.pixel_size))
        return img

    def take_damage(self, amount):
        current_time = pygame.time.get_ticks()
        if not self.is_invincible or current_time - self.last_hit_time > self.iframes_duration:
            player_hurt_sound.play()
            for _ in range(random.randint(8, 15)):
                        particle = BloodParticle(player.rect.centerx, player.rect.centery)
                        all_sprites.add(particle)
            self.hearts -= amount
            self.last_hit_time = current_time
            self.is_invincible = True
            self.blink_timer = current_time
            if self.hearts <= 0:
                self.hearts = 0
                return True
        return False

    def update(self):
        current_time = pygame.time.get_ticks()
        if self.is_invincible and current_time - self.last_hit_time > self.iframes_duration:
            self.is_invincible = False

    def draw(self, screen):
        current_time = pygame.time.get_ticks()
        blink_visible = (current_time - self.blink_timer) // self.blink_speed % 2 == 0

        for i in range(self.max_hearts):
            heart_pos = (10 + i * (self.heart_width + 4), 10)  # 4px spacing
            
            if self.is_invincible and not blink_visible:
                continue
                
            if i < self.hearts:
                screen.blit(self.heart_images['full'], heart_pos)
            else:
                screen.blit(self.heart_images['empty'], heart_pos)

# Initialize player health
player_health = PlayerHealth()

# Weapon class
class Weapon:
    def __init__(self, name, damage, fire_rate, ammo, reload_time, cost, 
                 spread=0, projectile_speed=15, is_automatic=False, max_range=500):
        self.name = name
        self.combined_image = pygame.image.load(f"Images/player_{name.lower()}.png").convert_alpha()
        
        self.damage = damage
        self.fire_rate = fire_rate
        self.ammo = ammo
        self.reload_time = reload_time
        self.cost = cost
        self.purchased = False
        self.spread = spread
        self.projectile_speed = projectile_speed
        self.is_automatic = is_automatic
        self.max_range = max_range

weapons = {
    "Pistol": Weapon("Pistol", 25, 200, 10, 2000, 0, 
                    max_range=500),
    "Shotgun": Weapon("Shotgun", 80, 500, 4, 3000, 50, 
                    spread=30, max_range=200),  
    "Rifle": Weapon("Rifle", 35, 100, 20, 2500, 100, 
                    is_automatic=True, projectile_speed=15, max_range=600),
    "Sniper": Weapon("Sniper", 1000, 200, 5, 4000, 200, 
                    projectile_speed=30, max_range=2000)  
}
weapons["Pistol"].purchased = True  # Starting weapon is already purchased

# Shop function
def show_shop():
    
    shop_open_sound.play()

    global shop_open_time, time_spent_in_shop, is_shop_open, player_money

    is_shop_open = True
    shop_open_time = pygame.time.get_ticks()  # Record when shop opens
    
    shop_running = True
    popup_message = None
    popup_start_time = 0
    POPUP_DURATION = 2000  # 2 seconds

    def handle_weapon_selection(weapon_name, weapon):
        nonlocal popup_message, popup_start_time
        global player_money 
        
        if weapon.purchased:
            player.equip_weapon(weapon_name)
        else:
            if player_money >= weapon.cost:
                player_money -= weapon.cost
                weapon.purchased = True
                player.purchased_weapons.append(weapon_name)
                player.equip_weapon(weapon_name)
                shop_buy_sound.play()
            else:
                popup_message = "Not enough money!"
                popup_start_time = pygame.time.get_ticks()

    while shop_running:
        screen.fill(BLACK)
        
        # Current balance
        balance_text = font.render(f"Balance: ${player_money}", True, GREEN)
        screen.blit(balance_text, (WIDTH//2 - balance_text.get_width()//2, 80))
        
        # Shop title
        title_text = shop_font.render("Shop", True, WHITE)
        screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 30))

        info_text = font.render("Press 1-3 to buy/equip or ESC to exit", True, WHITE)
        screen.blit(info_text, (WIDTH//2 - info_text.get_width()//2, 670))
        
        # Weapon listings
        y_offset = 150
        weapon_keys = ["Shotgun", "Rifle", "Sniper"]  # Only show purchasable weapons
        
        for i, weapon_name in enumerate(weapon_keys, 1):
            weapon = weapons[weapon_name]
            
            # Weapon entry
            text_color = WHITE
            status = ""
            
            if weapon_name == player.weapon.name:
                status = " (Equipped)"
                text_color = GREEN
            elif weapon.purchased:
                status = " (Purchased)"
                text_color = LIGHT_GRAY
            
            entry_text = f"{i}. {weapon_name}{status} - ${weapon.cost if not weapon.purchased else 'OWNED'}"
            text_surface = font.render(entry_text, True, text_color)
            screen.blit(text_surface, (WIDTH//2 - 350, y_offset))
            
            # Weapon stats
            stats_text = f"Dmg: {weapon.damage} | Fire Rate: {weapon.fire_rate/1000:.1f}s | Ammo: {weapon.ammo}"
            stats_surface = font.render(stats_text, True, LIGHT_GRAY)
            screen.blit(stats_surface, (WIDTH//2 - 350, y_offset + 30))
            
            y_offset += 80

        # Display popup message if active
        if popup_message and pygame.time.get_ticks() - popup_start_time < POPUP_DURATION:
            popup_surface = font.render(popup_message, True, RED)
            popup_rect = popup_surface.get_rect(center=(WIDTH//2, HEIGHT - 100))
            pygame.draw.rect(screen, BLACK, (popup_rect.x-10, popup_rect.y-5, 
                           popup_rect.width+20, popup_rect.height+10))
            screen.blit(popup_surface, popup_rect)
        
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    shop_running = False
                    is_shop_open = False
                    time_spent_in_shop += pygame.time.get_ticks() - shop_open_time
                    shop_open_sound.stop()
                    shop_buy_sound.stop()
                
                # Handle weapon selection
                if event.key == pygame.K_1:
                    handle_weapon_selection("Shotgun", weapons["Shotgun"])
                if event.key == pygame.K_2:
                    handle_weapon_selection("Rifle", weapons["Rifle"])
                if event.key == pygame.K_3:
                    handle_weapon_selection("Sniper", weapons["Sniper"])

class BloodParticle(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.size = random.randint(3, 7)
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        # Blood color variations
        blood_colors = [
            (200, 0, 0),    # Dark red
            (150, 0, 0),    # Deeper red
            (255, 50, 50),  # Bright red
            (180, 30, 30)  # Medium red
        ]
        pygame.draw.circle(self.image, random.choice(blood_colors), 
                          (self.size//2, self.size//2), self.size//2)
        
        self.rect = self.image.get_rect(center=(x, y))
        
        self.velocity = pygame.math.Vector2(
            random.uniform(-3, 3),
            random.uniform(-3, 0)
        )
            
        self.gravity = 0.2
        self.lifetime = random.randint(800, 1200)
        self.spawn_time = pygame.time.get_ticks()
        self.alpha = 255

    def update(self):
        # Apply gravity
        self.velocity.y += self.gravity
        
        # Update position
        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y
        
        # Fade out
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed > self.lifetime / 2:
            self.alpha = max(0, 255 - int(255 * (elapsed / self.lifetime)))
            self.image.set_alpha(self.alpha)
        
        if elapsed > self.lifetime:
            self.kill()

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.weapon = weapons["Pistol"]
        self.image = self.weapon.combined_image  
        self.original_image = self.image  
        self.mask = pygame.mask.from_surface(self.image)
        self.weapon = weapons["Pistol"]
        self.purchased_weapons = ["Pistol"]

        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.collision_radius = 20  
        self.collision_rect = pygame.Rect(0, 0, self.collision_radius*2, self.collision_radius*2)
        self.collision_rect.center = self.rect.center
        
        # Create a rect centered on screen
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        
        self.pivot_offset = pygame.math.Vector2(10, 0)  
        self.true_position = pygame.math.Vector2(self.rect.center)
        
        self.speed = 5
        self.angle = 0  
        self.ammo = self.weapon.ammo
        self.is_reloading = False
        self.last_shot_time = 0
        self.reload_start_time = 0
        self.last_sound_time = 0  
        self.sound_rate = 100
        
    def update(self):
        keys = pygame.key.get_pressed()

        self.collision_rect.center = self.rect.center
        
        # Store previous position
        prev_x, prev_y = self.true_position.x, self.true_position.y
        
        # Movement
        if keys[pygame.K_w]:
            self.true_position.y -= self.speed
            if self.true_position.y - self.rect.height/2 < 0:  
                self.true_position.y = prev_y
        if keys[pygame.K_s]:
            self.true_position.y += self.speed
            if self.true_position.y + self.rect.height/2 > HEIGHT:  
                self.true_position.y = prev_y
        if keys[pygame.K_a]:
            self.true_position.x -= self.speed
            if self.true_position.x - self.rect.width/2 < 0: 
                self.true_position.x = prev_x
        if keys[pygame.K_d]:
            self.true_position.x += self.speed
            if self.true_position.x + self.rect.width/2 > WIDTH:  
                self.true_position.x = prev_x
            
        # Check for collisions with objects
        player_rect = pygame.Rect(self.true_position.x - 20, self.true_position.y - 20, 40, 40)
            
        # Check collisions
        for object_rect in COLLISION_RECTS:
            if player_rect.colliderect(object_rect):
                self.true_position.x, self.true_position.y = prev_x, prev_y
                break

        # Update angle based on mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        rel_x, rel_y = mouse_x - self.true_position.x, mouse_y - self.true_position.y
        self.angle = math.degrees(-math.atan2(rel_y, rel_x))
        
        # Rotate the image
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        
        # Calculate the offset after rotation
        offset_rotated = self.pivot_offset.rotate(-self.angle)
        
        # Update the rect position
        self.rect = self.image.get_rect(center=self.true_position + offset_rotated)

        # Automatic firing for rifle
        mouse_buttons = pygame.mouse.get_pressed()
        if self.weapon.is_automatic and mouse_buttons[0]:  # 0 is left mouse button
            if self.can_shoot():
                self.shoot()


        
    def equip_weapon(self, weapon_name):
        if weapon_name in self.purchased_weapons:
            self.weapon = weapons[weapon_name]
            self.original_image = self.weapon.combined_image
            self.image = self.original_image
            self.rect = self.image.get_rect(center=self.rect.center)
            self.ammo = self.weapon.ammo
            self.is_reloading = False

    def can_shoot(self):
        current_time = pygame.time.get_ticks()
        return (self.ammo > 0 and 
                not self.is_reloading and
                current_time - self.last_shot_time >= self.weapon.fire_rate)
    
    def start_reload(self):
        if not self.is_reloading and self.ammo < self.weapon.ammo:
            self.is_reloading = True
            self.reload_start_time = pygame.time.get_ticks()
            reload_sound.play()
    
    def update_reload(self):
        if self.is_reloading:
            current_time = pygame.time.get_ticks()
            if current_time - self.reload_start_time >= self.weapon.reload_time:
                self.ammo = self.weapon.ammo
                self.is_reloading = False


    def draw_ammo(self, screen):
        # Draw ammo counter
        ammo_text = font.render(f"Ammo: {str(self.ammo) +"/"+ str(self.weapon.ammo)}", True, WHITE)
        screen.blit(ammo_text, (WIDTH - 250, 10))
        
        # Draw reload indicator
        if self.is_reloading:
            reload_text = font.render("Reloading...", True, RED)
            screen.blit(reload_text, (WIDTH - 250, 40))
            
            # Draw reload progress bar
            progress_width = 100
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.reload_start_time
            progress = min(elapsed / self.weapon.reload_time, 1.0)
            
            pygame.draw.rect(screen, LIGHT_GRAY, 
                           (WIDTH - 200, 70, progress_width, 10))
            pygame.draw.rect(screen, GREEN, 
                           (WIDTH - 200, 70, int(progress_width * progress), 10))

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)
    
    def shoot(self):
        if self.can_shoot():
            # Get mouse position
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            # Calculate direction vector from player to mouse
            dx = mouse_x - self.rect.centerx
            dy = mouse_y - self.rect.centery
            
            # Normalize the direction vector
            distance = max(1, math.sqrt(dx*dx + dy*dy))  
            direction = pygame.math.Vector2(dx/distance, dy/distance)
            
            gun_length = 20  
            muzzle_x = self.rect.centerx + gun_length * direction.x
            muzzle_y = self.rect.centery + gun_length * direction.y
            
            muzzle_flash = MuzzleFlash(muzzle_x, muzzle_y, 0)  
            all_sprites.add(muzzle_flash)

            # Create 3 bullets with different directions
            if self.weapon.name == "Shotgun":
                # Center bullet
                center_bullet = Bullet(
                    self.rect.centerx, 
                    self.rect.centery,
                    direction, 
                    self.weapon.projectile_speed,
                    self.weapon.max_range
                )
                all_sprites.add(center_bullet)
                bullets.add(center_bullet)
                
                # Left bullet
                left_direction = pygame.math.Vector2(-direction.y, direction.x) * 0.3 + direction
                left_direction = left_direction.normalize()
                
                left_bullet = Bullet(
                    self.rect.centerx, 
                    self.rect.centery,
                    left_direction, 
                    self.weapon.projectile_speed,
                    self.weapon.max_range
                )
                all_sprites.add(left_bullet)
                bullets.add(left_bullet)
                
                # Right bullet
                right_direction = pygame.math.Vector2(direction.y, -direction.x) * 0.3 + direction
                right_direction = right_direction.normalize()
                
                right_bullet = Bullet(
                    self.rect.centerx, 
                    self.rect.centery,
                    right_direction, 
                    self.weapon.projectile_speed,
                    self.weapon.max_range
                )
                all_sprites.add(right_bullet)
                bullets.add(right_bullet)
            else:
                # Regular single bullet for other weapons
                bullet = Bullet(
                    self.rect.centerx, 
                    self.rect.centery,
                    direction, 
                    self.weapon.projectile_speed,
                    self.weapon.max_range
                )
                all_sprites.add(bullet)
                bullets.add(bullet)

            # Update ammo and cooldown
            self.ammo -= 1
            self.last_shot_time = pygame.time.get_ticks()
            gunshot_sound.play()

            # Auto-reload when empty
            if self.ammo <= 0:
                self.start_reload()

# MuzzleFlasash class
class MuzzleFlash(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        self.alpha = 255
        self.layers = []
        
        # Generate random flash characteristics
        flash_size = random.randint(20, 30)
        spike_length = random.randint(8, 15)
        
        # Create main flash surface
        self.image = pygame.Surface((flash_size * 2, flash_size * 2), pygame.SRCALPHA)
        
        # Add bright core
        core_color = (255, 255, 150, self.alpha)
        pygame.draw.circle(self.image, core_color, 
                          (flash_size, flash_size), 
                          random.randint(3, 5))
        
        # Add glowing spikes
        unit_vectors = [
            (1, 0),
            (0.707, 0.707),
            (0, 1),
            (-0.707, 0.707),
            (-1, 0),
            (-0.707, -0.707),
            (0, -1),
            (0.707, -0.707),
        ]

        spike_color = (255, 180, 50, self.alpha)
        for i in range(len(unit_vectors)):
            dx, dy = unit_vectors[i]
            start_x = flash_size + dx * 5
            start_y = flash_size + dy * 5
            end_x = flash_size + dx * spike_length
            end_y = flash_size + dy * spike_length
            pygame.draw.line(
                self.image, spike_color,
                (start_x, start_y), (end_x, end_y),
                random.randint(2, 4)
            )
        # Add subtle smoke particles
        for _ in range(random.randint(3, 5)):
            smoke_color = (50, 50, 50, random.randint(50, 100))
            smoke_pos = (
                flash_size + random.randint(-10, 10),
                flash_size + random.randint(-10, 10)
            )
            pygame.draw.circle(self.image, smoke_color,
                             smoke_pos, random.randint(1, 2))

        # Apply transformations
        self.image = pygame.transform.rotate(self.image, -angle + random.randint(-15, 15))
        self.rect = self.image.get_rect(center=(x, y))
        
        # Animation properties
        self.spawn_time = pygame.time.get_ticks()
        self.duration = 120  # milliseconds

    def update(self):
        # Calculate fade progression
        elapsed = pygame.time.get_ticks() - self.spawn_time
        progress = elapsed / self.duration
        
        # Update alpha and scale
        self.alpha = max(0, 255 - int(255 * progress))
        self.image.set_alpha(self.alpha)
        
        # Add scaling effect
        current_scale = 1.0 + 0.5 * progress
        scaled_image = pygame.transform.scale(self.image,
            (int(self.rect.width * current_scale),
            int(self.rect.height * current_scale)))
        self.image = scaled_image
        
        if elapsed > self.duration:
            self.kill()

# Bullet class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, speed, max_range):
        super().__init__()
        self.speed = speed
        self.max_distance = max_range
        self.distance_traveled = 0
        self.width = 15
        self.height = 8

        # Create bullet image
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(self.image, YELLOW, (0, 0, self.width, self.height))
        pygame.draw.rect(self.image, BLACK, (0, 0, self.width, self.height), 2)
        
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction

    def update(self):
        # Move bullet in its direction
        self.rect.x += self.direction.x * self.speed
        self.rect.y += self.direction.y * self.speed
        self.distance_traveled += self.speed

        for wall in MONUMENT_WALLS:
                    if self.rect.colliderect(wall):
                        self.kill()
                        return
                    
        # Check if bullet exceeded max range or left screen
        if (self.max_distance is not None and self.distance_traveled > self.max_distance) or \
           not screen.get_rect().colliderect(self.rect):
            self.kill()

class SpitProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill(PURPLE)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 5
        self.direction = direction

    def update(self):
        self.rect.x += self.direction.x * self.speed
        self.rect.y += self.direction.y * self.speed
        if not screen.get_rect().colliderect(self.rect):
            self.kill()
            spit_projectiles.remove(self)  # Remove from the projectiles group

        for wall in MONUMENT_WALLS:
            if self.rect.colliderect(wall):
                self.kill()
                spit_projectiles.remove(self)
                return

# Zombie class
class Zombie(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path):
        super().__init__()
        self.original_image = pygame.image.load("Images/" + image_path).convert_alpha()
        self.image = self.original_image  # Default image without rotation
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        self.path_update_interval = random.randint(300, 500)  
        self.current_target_index = 0
        self.path = []
        self.next_waypoint = None
        self.path_update_timer = pygame.time.get_ticks()
        self.last_path_update_time = pygame.time.get_ticks()
        self.has_active_path = True
        self.stuck_timer = 0
        self.max_stuck_time = 5000
        
        # Add a circular collision radius for distance checks
        self.collision_radius = self.rect.width // 2
        self.collision_rect = pygame.Rect(0, 0, self.collision_radius*2, self.collision_radius*2)
        self.collision_rect.center = self.rect.center
        
        # Collision avoidance properties
        self.avoidance_radius = self.collision_radius * 2.5  # Area to check for other zombies
        self.avoidance_force = 0.7  # Strength of avoidance push
        self.push_decay = 0.9  # How quickly push forces decay
        
        # Movement vectors for smoother collision response
        self.velocity = pygame.math.Vector2(0, 0)
        self.push_vector = pygame.math.Vector2(0, 0)

        # Adjust speed based on wave
        self.base_speed = 1.5  # Base zombie speed
        self.speed = self.base_speed + (zombie_wave * 0.1)  # Slight speed increase per wave
        self.max_health = zombie_health
        self.health = zombie_health
        self.target_offset = pygame.math.Vector2(random.uniform(-30, 30), random.uniform(-30, 30))  # Spread out movement
        

    def update(self):
        current_time = pygame.time.get_ticks()
        
        # Update path periodically or if current path is empty
        if (current_time - self.path_update_timer > self.path_update_interval or 
            not self.path or self.current_target_index >= len(self.path)):
            old_has_path = bool(self.path)
            self.path_update_timer = current_time
            self.update_path()
            
            # Update stuck timer based on path status
            if self.path:
                self.has_active_path = True
                self.stuck_timer = 0
            else:
                self.has_active_path = False
                if old_has_path:  # Only start timer if we just lost our path
                    self.stuck_timer = current_time
        
        # Check if zombie is stuck without a path for too long
        if not self.has_active_path and self.stuck_timer > 0:
            if current_time - self.stuck_timer > self.max_stuck_time:
                self.kill()
                return
        
        # Update path periodically or if current path is empty
        if (current_time - self.path_update_timer > self.path_update_interval or 
            not self.path or self.current_target_index >= len(self.path)):
            self.path_update_timer = current_time
            self.update_path()
        
        # Follow path if we have one
        if self.path and self.current_target_index < len(self.path):
            target_pos = pygame.math.Vector2(self.path[self.current_target_index])
            
            # Calculate direction with smoothing
            direction = (target_pos - pygame.math.Vector2(self.rect.center))
            if direction.length() > 0:
                direction = direction.normalize()
            
            # Apply movement with smoothing
            self.rect.x += direction.x * self.speed
            self.rect.y += direction.y * self.speed
            
            # Check if reached current waypoint 
            if pygame.math.Vector2(self.rect.center).distance_to(target_pos) < 10:
                self.current_target_index += 1
        
        # Avoid other zombies
        self.avoid_collisions()
        
        # Rotate to face movement direction
        if self.path and self.current_target_index < len(self.path):
            target_pos = pygame.math.Vector2(self.path[self.current_target_index])
            rel_x, rel_y = target_pos.x - self.rect.centerx, target_pos.y - self.rect.centery
            self.angle = math.degrees(-math.atan2(rel_y, rel_x))
        
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)
        
    
        # Check collision with player
        if not DEBUG_MODE:
            player_dist = pygame.math.Vector2(player.rect.center).distance_to(self.rect.center)
            if player_dist < self.collision_radius + player.collision_radius:
                offset_x = player.rect.left - self.rect.left
                offset_y = player.rect.top - self.rect.top
                if player.mask.overlap(self.mask, (offset_x, offset_y)):
                    for _ in range(random.randint(8, 15)):
                        particle = BloodParticle(player.rect.centerx, player.rect.centery)
                        all_sprites.add(particle)
                    if player_health.take_damage(1):  
                        play_death_animation()
                    
                    # Push zombie back slightly when attacking player
                    push_dir = pygame.math.Vector2(self.rect.center) - pygame.math.Vector2(player.rect.center)
                    if push_dir.length() > 0:
                        push_dir = push_dir.normalize()
                    self.rect.center += push_dir * 10 

    def avoid_collisions(self):
        # Reset push vector each frame
        self.push_vector = pygame.math.Vector2(0, 0)
        neighbor_count = 0
        
        # Check against other zombies
        for other in zombies:
            if other != self:
                # Calculate distance between centers
                dist_vec = pygame.math.Vector2(other.rect.center) - pygame.math.Vector2(self.rect.center)
                distance = dist_vec.length()
                
                # Calculate combined collision radius
                min_distance = self.collision_radius + other.collision_radius
                
                if distance < self.avoidance_radius:
                    # Calculate separation force (stronger when closer)
                    if distance > 0:
                        force = (self.avoidance_radius - distance) / self.avoidance_radius
                        separation = -dist_vec.normalize() * force
                        self.push_vector += separation
                        neighbor_count += 1
                    
                    # Handle direct collisions
                    if distance < min_distance:
                        overlap = min_distance - distance
                        if overlap > 0:
                            # Calculate push direction and amount
                            if distance > 0:
                                push_dir = dist_vec.normalize()
                            else:
                                push_dir = pygame.math.Vector2(1, 0)  # Default if same position
                            
                            # Push away based on overlap
                            push_amount = overlap * 0.5
                            self.push_vector += -push_dir * push_amount
        
        # Apply averaged push force
        if neighbor_count > 0:
            self.push_vector /= neighbor_count
        
        # Apply push vector to position (with decay)
        if self.push_vector.length() > 0:
            self.rect.center += self.push_vector * self.avoidance_force
            self.push_vector *= self.push_decay

    def update_path(self):
        global pathfinding_grid
        
        # Update zombie positions in pathfinding grid
        pathfinding_grid.update_zombie_positions(zombies)
        
        # Get new path - use screen center if player is None (shouldn't happen but just in case)
        target_pos = player.rect.center if hasattr(player, 'rect') else (WIDTH//2, HEIGHT//2)
        
        # If zombie is outside screen, first path to screen edge
        if (self.rect.right < 0 or self.rect.left > WIDTH or
            self.rect.bottom < 0 or self.rect.top > HEIGHT):
            # Find closest screen edge point
            target_x = max(0, min(WIDTH, self.rect.centerx))
            target_y = max(0, min(HEIGHT, self.rect.centery))
            edge_target = (target_x, target_y)
            
            # Get path to screen edge first
            self.path = pathfinding_grid.find_path(self.rect.center, edge_target)
        else:
            # Normal path to player
            self.path = pathfinding_grid.find_path(self.rect.center, target_pos)
            
        self.current_target_index = 0
        
        # If no path found, try again with adjusted positions
        if not self.path:
            adjusted_start = pathfinding_grid.find_nearest_walkable(
                self.rect.centerx // GRID_SIZE,
                self.rect.centery // GRID_SIZE
            )
            adjusted_start = (adjusted_start[0] * GRID_SIZE + GRID_SIZE//2,
                            adjusted_start[1] * GRID_SIZE + GRID_SIZE//2)
            
            adjusted_target = pathfinding_grid.find_nearest_walkable(
                target_pos[0] // GRID_SIZE,
                target_pos[1] // GRID_SIZE
            )
            adjusted_target = (adjusted_target[0] * GRID_SIZE + GRID_SIZE//2,
                            adjusted_target[1] * GRID_SIZE + GRID_SIZE//2)
            
            self.path = pathfinding_grid.find_path(adjusted_start, adjusted_target)
            self.current_target_index = 0

class TankZombie(Zombie):
    def __init__(self, x, y, image_path):
        super().__init__(x, y, image_path)
        self.mask = pygame.mask.from_surface(self.image)
        self.base_speed = 0.8
        self.max_health = 150 + (zombie_wave * 15)
        self.health = self.max_health
        self.speed = self.base_speed + (zombie_wave * 0.05)
        self.collision_radius = 30  
        self.avoidance_radius = 80  
        self.avoidance_force = 0.5  
        self.push_decay = 0.8  
        self.collision_rect = pygame.Rect(0, 0, self.collision_radius*2, self.collision_radius*2)
        self.collision_rect.center = self.rect.center

class RunnerZombie(Zombie):
    def __init__(self, x, y, image_path):
        super().__init__(x, y, image_path)
        self.mask = pygame.mask.from_surface(self.image)
        self.base_speed = 3.20
        self.max_health = 30 + (zombie_wave * 5)
        self.health = self.max_health
        self.speed = self.base_speed + (zombie_wave * 0.15)
        self.collision_radius = 15  
        self.avoidance_radius = 50  
        self.avoidance_force = 0.3  
        self.push_decay = 0.95  
        self.collision_rect = pygame.Rect(0, 0, self.collision_radius*2, self.collision_radius*2)
        self.collision_rect.center = self.rect.center

class SpitterZombie(Zombie):
    def __init__(self, x, y, image_path):
        super().__init__(x, y, image_path)
        self.mask = pygame.mask.from_surface(self.image)
        self.base_speed = 1.0
        self.max_health = 80 + (zombie_wave * 8)
        self.health = self.max_health
        self.speed = self.base_speed + (zombie_wave * 0.1)
        self.attack_cooldown = 2000
        self.last_attack = 0
        self.collision_radius = 20  
        self.avoidance_radius = 70  
        self.avoidance_force = 0.4  
        self.push_decay = 0.9  
        self.collision_rect = pygame.Rect(0, 0, self.collision_radius*2, self.collision_radius*2)
        self.collision_rect.center = self.rect.center


    def update(self):
        super().update()
        if pygame.time.get_ticks() - self.last_attack > self.attack_cooldown:
            self.attack()
            self.last_attack = pygame.time.get_ticks()

    def attack(self):
        # Convert the centers to Vector2 objects
        player_center = pygame.math.Vector2(player.rect.center)
        zombie_center = pygame.math.Vector2(self.rect.center)
        
        # Calculate the direction vector
        direction = (player_center - zombie_center).normalize()
        
        # Create and add the spit projectile
        spit = SpitProjectile(self.rect.centerx, self.rect.centery, direction)
        spitter_attack_sound.play()
        all_sprites.add(spit)
        spit_projectiles.add(spit)
  
# Farm class
class Farm:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH // 2 - 50, HEIGHT // 2 - 50, 100, 100)
        self.seed_planted = None
        self.stalks = []  # Store positions and growth stages of individual wheat stalks

    def plant_seed(self):
        if self.seed_planted is None:
            self.seed_planted = pygame.time.get_ticks()
            # Initialize multiple wheat stalks with random positions within the farm area
            self.stalks = []
            crop_planted_sound.play()
            for _ in range(20):  # Number of wheat stalks
                x = random.randint(self.rect.left + 10, self.rect.right - 10)
                y = random.randint(self.rect.top + 10, self.rect.bottom - 10)
                self.stalks.append({"pos": (x, y), "growth": 0})

    def harvest_seed(self):
        global player_money
        if self.seed_planted:
            current_time = pygame.time.get_ticks()
            time_elapsed = (current_time - self.seed_planted) / 1000
            if time_elapsed >= 15:
                player_money += random.randint(10, 20)
                self.seed_planted = None
                self.stalks = []  # Clear the stalks after harvesting
                crop_harvested_sound.play()

    def draw(self, screen):
        pygame.draw.rect(screen, BROWN, self.rect)  # Draw the farm soil
        if self.seed_planted:
            current_time = pygame.time.get_ticks()
            time_elapsed = (current_time - self.seed_planted) / 1000
            growth_percentage = min(time_elapsed / 15, 1.0)  # Growth percentage (0 to 1)

            for stalk in self.stalks:
                x, y = stalk["pos"]
                stalk_height = int(40 * growth_percentage)  # Height of the stalk
                stalk_width = 2  # Width of the stalk
                stem_color = (34, 139, 34)  # Color for the stem

                # Draw the stem
                stem_top = y - stalk_height
                stem_bottom = y
                pygame.draw.line(screen, stem_color, (x, stem_bottom), (x, stem_top), stalk_width)

                # Draw the wheat grains at the top of the stalk
                if growth_percentage >= 1.0:  # Fully grown
                    grain_color = (PURPLE)
                    grain_radius = 3
                    num_grains = 5  # Number of grains per stalk
                    for i in range(num_grains):
                        grain_x = x + random.randint(-5, 5)
                        grain_y = stem_top + random.randint(-5, 5)
                        pygame.draw.circle(screen, grain_color, (grain_x, grain_y), grain_radius)

                # Draw the wheat head (a cluster of grains)
                if growth_percentage >= 0.8:  # Partially grown
                    head_color = (PURPLE)  # Wheat head color
                    head_width = 10
                    head_height = 5
                    pygame.draw.ellipse(screen, head_color, (x - head_width // 2, stem_top - head_height, head_width, head_height))
        
def show_start_menu():
    menu = [
        pygame.image.load("Images/menu.jpg").convert_alpha(),
        pygame.image.load("Images/menu1.jpg").convert_alpha()
    ]
    
    sound_track.play(loops=-1)

    value = 0
    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    sound_track.stop()
                    pygame.time.wait(150)
                    start_sound.play()
                    running = False

        screen.fill(BLACK)

        # Show current menu image
        menu_image = menu[value % len(menu)]
        screen.blit(menu_image, (0, 0))
        pygame.display.update()

        value += 1
        pygame.time.wait(500)  

        clock.tick(60) 

# Function to show the death screen
def show_death_screen():
    skull_surface = pygame.image.load("Images/death.png")
    
    skull_pos = (WIDTH//2 - 45, HEIGHT//2 - 150)
    
    # Blood drip
    blood_drops = []
    for i in range(20):
        blood_drops.append({
            'x': random.randint(skull_pos[0], skull_pos[0] + 64),
            'y': skull_pos[1] + 64,
            'speed': random.uniform(2, 5),
            'size': random.randint(2, 5)
        })
    
    # Animation timer
    start_time = pygame.time.get_ticks()
    animation_duration = 1500 
    
    while True:
        current_time = pygame.time.get_ticks()
        progress = min(1.0, (current_time - start_time) / animation_duration)
        
        screen.fill(BLACK)
        
        for drop in blood_drops:
            drop['y'] += drop['speed']
            pygame.draw.rect(screen, RED, 
                           (drop['x'], drop['y'], drop['size'], drop['size']))
            
            # Reset drops that fall off screen
            if drop['y'] > HEIGHT:
                drop['y'] = skull_pos[1] + 64
                drop['x'] = random.randint(skull_pos[0], skull_pos[0] + 64)
        
        skull_surface.set_alpha(int(255 * progress))
        screen.blit(skull_surface, skull_pos)
        
        # Draw text 
        game_over_text = gameover_font.render("GAME OVER", True, 
                                           (min(255, int(255 * progress * 2)), 0, 0))
        restart_text = font.render("Press R to Restart or Q to Quit", True, 
                                (min(255, int(255 * progress * 2)), 
                                 min(255, int(255 * progress * 2)), 
                                 min(255, int(255 * progress * 2))))
        
        screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, 
                                   HEIGHT//2 - 50))
        screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, 
                                 HEIGHT//2 + 50))
        
        pygame.display.flip()
        
        # Check for input after animation completes
        if progress >= 1.0:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        initialize_game()
                        return
                    if event.key == pygame.K_q:
                        pygame.quit()
                        exit()
        
        clock.tick(FPS)

class HeartExplosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.start_time = pygame.time.get_ticks()
        self.duration = 3000
        self.heart_img = self.create_heart_image()
        self.particles = []
        self.light_beams = []
        
    def create_heart_image(self):
        # Create a pixel art heart surface
        heart_size = 64
        heart = pygame.Surface((heart_size, heart_size), pygame.SRCALPHA)
        
        # Pixel pattern for the heart (1 = pixel, 0 = transparent)
        pattern = [
            [0,1,1,0,1,1,0],
            [1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1],
            [0,1,1,1,1,1,0],
            [0,0,1,1,1,0,0],
            [0,0,0,1,0,0,0]
        ]
        
        # Scale up the pixels
        pixel_size = heart_size // 7
        for py in range(7):
            for px in range(7):
                if pattern[py][px]:
                    pygame.draw.rect(heart, RED, 
                                    (px*pixel_size, py*pixel_size, 
                                     pixel_size, pixel_size))
        return heart
    
    def create_particles(self):
        # Create heart fragment particles
        heart_size = self.heart_img.get_size()
        for _ in range(20):  
            # Create a random rectangular section of the heart
            piece_w = random.randint(heart_size[0]//4, heart_size[0]//2)
            piece_h = random.randint(heart_size[1]//4, heart_size[1]//2)
            piece_x = random.randint(0, heart_size[0]-piece_w)
            piece_y = random.randint(0, heart_size[1]-piece_h)
            
            # Create the piece surface
            piece = pygame.Surface((piece_w, piece_h), pygame.SRCALPHA)
            piece.blit(self.heart_img, (0,0), (piece_x, piece_y, piece_w, piece_h))
            
            # Particle properties
            self.particles.append({
                'image': piece,
                'x': self.x + piece_x - heart_size[0]//2,
                'y': self.y + piece_y - heart_size[1]//2,
                'vel_x': random.uniform(-2, 2),
                'vel_y': random.uniform(-5, -2),
                'angle': 0,
                'angle_vel': random.uniform(-3, 3),
                'alpha': 255,
                'fade_speed': random.uniform(0.5, 2.0)
            })
    
    def update(self):
        current_time = pygame.time.get_ticks()
        progress = min(1.0, (current_time - self.start_time) / self.duration)
        
        # Create particles at 20% progress
        if progress >= 0.2 and not self.particles:
            self.create_particles()
        
        
        # Update particles
        for particle in self.particles:
            particle['x'] += particle['vel_x']
            particle['y'] += particle['vel_y']
            particle['vel_y'] += 0.1  # Gravity
            particle['angle'] += particle['angle_vel']
            particle['alpha'] = max(0, particle['alpha'] - particle['fade_speed'])
            particle['image'].set_alpha(particle['alpha'])
        
        return progress >= 1.0
    
    def draw(self, screen):
        current_time = pygame.time.get_ticks()
        progress = min(1.0, (current_time - self.start_time) / self.duration)
        
        # Draw the whole heart before it breaks (first 20% of animation)
        if progress < 0.2:
            scaled_heart = pygame.transform.scale(
                self.heart_img,
                (int(self.heart_img.get_width()),
                 int(self.heart_img.get_height()))
            )
            heart_rect = scaled_heart.get_rect(center=(self.x, self.y))
            screen.blit(scaled_heart, heart_rect)
        
        # Draw particles
        for particle in self.particles:
            if particle['alpha'] > 0:
                rotated_piece = pygame.transform.rotate(particle['image'], particle['angle'])
                piece_rect = rotated_piece.get_rect(center=(particle['x'], particle['y']))
                screen.blit(rotated_piece, piece_rect.topleft)

def play_death_animation():
    global background

    for spits in spit_projectiles:
        spit_projectiles.remove(spits)

    background_music.stop()

    gameover_sound.play()
    
    # Create the heart explosion effect at player's position
    heart_explosion = HeartExplosion(player.rect.centerx, player.rect.centery)
    
    # Create a darkening overlay
    darken_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    darken_surface.fill((0, 0, 0, 0))
    
    # Animation loop
    running = True
    start_time = pygame.time.get_ticks()
    
    while running:
        current_time = pygame.time.get_ticks()
        progress = min(1.0, (current_time - start_time) / heart_explosion.duration)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
        
        # Update effects
        done = heart_explosion.update()
        
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BLACK)
        
        # Draw game objects (fading out)
        for sprite in all_sprites:
            temp_img = sprite.image.copy()
            temp_img.set_alpha(255 - int(255 * progress))
            screen.blit(temp_img, sprite.rect.topleft)
        
        # Draw heart explosion effect
        heart_explosion.draw(screen)
        
        # Darken screen progressively
        darken_alpha = int(200 * progress)
        darken_surface.fill((0, 0, 0, darken_alpha))
        screen.blit(darken_surface, (0, 0))
        
        pygame.display.flip()
        clock.tick(FPS)
        
        if done:
            running = False

    show_death_screen()

# Sprite groups
all_sprites = pygame.sprite.Group()
player = Player()
all_sprites.add(player)
spit_projectiles = pygame.sprite.Group()
bullets = pygame.sprite.Group()
zombies = pygame.sprite.Group()
farm = Farm()

def spawn_zombie():
    global zombie_wave
    for _ in range(zombie_wave + 2):  # Slightly more zombies per wave
        x = random.choice([0, WIDTH])
        y = random.randint(0, HEIGHT)
        rand = random.random()

        # Define image paths for different zombie types ( maybe move to the top later on )
        zombie_image_path = "zombie.png"
        tank_zombie_image_path = "tank_zombie.png"
        runner_zombie_image_path = "runner_zombie.png"
        spitter_zombie_image_path = "spitter_zombie.png"

        if zombie_wave >= 10:
            if rand < 0.15: zombie = TankZombie(x, y, tank_zombie_image_path)
            elif rand < 0.35: zombie = RunnerZombie(x, y, runner_zombie_image_path)
            elif rand < 0.5: zombie = SpitterZombie(x, y, spitter_zombie_image_path)
            else: zombie = Zombie(x, y, zombie_image_path)
        elif zombie_wave >= 7:
            if rand < 0.1: zombie = TankZombie(x, y, tank_zombie_image_path)
            elif rand < 0.25: zombie = RunnerZombie(x, y, runner_zombie_image_path)
            elif rand < 0.35: zombie = SpitterZombie(x, y, spitter_zombie_image_path)
            else: zombie = Zombie(x, y, zombie_image_path)
        elif zombie_wave >= 5:
            if rand < 0.1: zombie = TankZombie(x, y, tank_zombie_image_path)
            elif rand < 0.2: zombie = RunnerZombie(x, y, runner_zombie_image_path)
            else: zombie = Zombie(x, y, zombie_image_path)
        elif zombie_wave >= 3:
            if rand < 0.1: zombie = TankZombie(x, y, tank_zombie_image_path)
            else: zombie = Zombie(x, y, zombie_image_path)
        else:
            zombie = Zombie(x, y, zombie_image_path)
            
        all_sprites.add(zombie)
        zombies.add(zombie)

def start_next_wave():
    global zombie_wave, wave_ready, wave_start_time, showing_wave_warning, time_spent_in_shop
    
    wave_ready = False
    wave_start_time = pygame.time.get_ticks()
    showing_wave_warning = False
    time_spent_in_shop = 0  
    spawn_zombie()

def handle_stuck_entities():

    # Threshold ratio of overlapping pixels to total pixels (20%)
    OVERLAP_THRESHOLD = 0.2
    
    # Check player collision
    player_mask = pygame.mask.from_surface(player.image)
    player_area = player_mask.count()
    
    for obj_rect in COLLISION_RECTS:
        # Create a mask for the collision object
        obj_mask = pygame.mask.Mask(obj_rect.size, True)
        
        # Calculate offset between player and object
        offset_x = obj_rect.left - player.rect.left
        offset_y = obj_rect.top - player.rect.top
        
        # Get overlapping area
        overlap_area = player_mask.overlap_area(obj_mask, (offset_x, offset_y))
        
        # Only push if OVERLAP_THRESHOLD is overlaped
        if overlap_area > player_area * OVERLAP_THRESHOLD:
            # Calculate push direction from center
            push_dir = pygame.math.Vector2(player.rect.center) - pygame.math.Vector2(obj_rect.center)
            if push_dir.length() > 0:
                push_dir = push_dir.normalize()
            
            # Push player away with force proportional to overlap
            push_force = 5 * (overlap_area / player_area)
            player.true_position += push_dir * push_force
            player.rect.center = player.true_position
    
    # Check zombie collisions
    for zombie in zombies:
        zombie_mask = pygame.mask.from_surface(zombie.image)
        zombie_area = zombie_mask.count()
        
        for obj_rect in COLLISION_RECTS:
            # Create a mask for the collision object
            obj_mask = pygame.mask.Mask(obj_rect.size, True)
            
            # Calculate offset between zombie and object
            offset_x = obj_rect.left - zombie.rect.left
            offset_y = obj_rect.top - zombie.rect.top
            
            # Get overlapping area
            overlap_area = zombie_mask.overlap_area(obj_mask, (offset_x, offset_y))
            
            # Only push if OVERLAP_THRESHOLD overlaped
            if overlap_area > zombie_area * OVERLAP_THRESHOLD:
                # Calculate push direction from center
                push_dir = pygame.math.Vector2(zombie.rect.center) - pygame.math.Vector2(obj_rect.center)
                if push_dir.length() > 0:
                    push_dir = push_dir.normalize()
                
                # Push zombie away with force proportional to overlap
                push_force = 5 * (overlap_area / zombie_area)
                zombie.rect.center += push_dir * push_force
                zombie.collision_rect.center = zombie.rect.center

def contain_zombies():
    for zombie in zombies:
        # Calculate push vector to keep zombie inside screen
        push_x, push_y = 0, 0
        
        if zombie.rect.right < 0:
            push_x = 5  # Push right
        elif zombie.rect.left > WIDTH:
            push_x = -5  # Push left
            
        if zombie.rect.bottom < 0:
            push_y = 5  # Push down
        elif zombie.rect.top > HEIGHT:
            push_y = -5  # Push up
            
        # Apply push if needed
        if push_x or push_y:
            zombie.rect.x += push_x
            zombie.rect.y += push_y
            zombie.collision_rect.center = zombie.rect.center
            
            zombie.path_update_timer = 0  # Will cause path to update next frame
        
def initialize_game():
    global zombie_wave, wave_ready, zombie_health, player_money, all_sprites, zombies, bullets, spit_projectiles, player, player_health, farm, wave_start_time, showing_wave_warning, warning_start_time, pathfinding_grid
    
    # Reset game state variables
    zombie_wave = 0 # Edit for cheats and debug
    player_money = 0 # Edit for cheats and debug
    wave_ready = False
    zombie_health = 100 # Edit for cheats and debug

    background_music.play(loops=-1)

    # Initialize pathfinding grid
    pathfinding_grid = PathfindingGrid()

    # Wave timeout variables
    wave_start_time = 0
    showing_wave_warning = False
    warning_start_time = 0
    
    # Clear all sprite groups
    all_sprites = pygame.sprite.Group()
    zombies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    spit_projectiles = pygame.sprite.Group()
    
    # Reset player
    player = Player()
    player_health = PlayerHealth()
    all_sprites.add(player)
    
    # Reset farm
    farm = Farm()
    
    # Reset weapon purchases (only keep Pistol)
    for weapon in weapons.values():
        if weapon.name != "Pistol":
            weapon.purchased = False
    player.purchased_weapons = ["Pistol"]
    player.equip_weapon("Pistol")
    
    # Start first wave
    start_next_wave()

def check_wave_timeout():
    global showing_wave_warning, warning_start_time, wave_ready, wave_start_time, zombie_wave, zombie_health, time_spent_in_shop
    
    current_time = pygame.time.get_ticks()
    
    # Subtract time spent in the shop from the wave timer
    adjusted_wave_start = wave_start_time + time_spent_in_shop
    time_in_wave = current_time - adjusted_wave_start
    
    # If player has been in wave for 1 minute and hasn't seen warning yet
    if time_in_wave > WAVE_TIMEOUT and not showing_wave_warning and len(zombies) > 0:
        showing_wave_warning = True
        warning_start_time = current_time
    
    # If warning is active and 10 seconds have passed
    if showing_wave_warning and current_time - warning_start_time > WAVE_WARNING_DURATION:
        for _ in range(random.randint(8, 15)):
            particle = BloodParticle(player.rect.centerx, player.rect.centery)
            all_sprites.add(particle)
        if player_health.take_damage(1):  
            play_death_animation()
            return
        zombie_wave += 1
        zombie_health += 10
        start_next_wave()
    
    # Cancel warning if all zombies are killed before timeout
    if showing_wave_warning and len(zombies) == 0:
        showing_wave_warning = False

def draw_wave_warning(screen):
    global showing_wave_warning, warning_start_time
    
    if showing_wave_warning:
        current_time = pygame.time.get_ticks()
        time_left = max(0, WAVE_WARNING_DURATION - (current_time - warning_start_time))
        seconds_left = math.ceil(time_left / 1000)
        
        # Draw warning at top center of screen
        warning_text = font.render(f"Next wave forced in: {seconds_left}", True, RED)
        screen.blit(warning_text, (WIDTH // 2 - warning_text.get_width() // 2, 10))

def draw_debug_info(screen):
    if not DEBUG_MODE:
        return
    
    # Create a temporary surface for transparent debug elements
    debug_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    # Draw grid if enabled
    if DEBUG_SHOW_GRID:
        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(debug_surface, (50, 50, 50, 100), (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(debug_surface, (50, 50, 50, 100), (0, y), (WIDTH, y), 1)
    
    # Draw obstacles if enabled
    if DEBUG_SHOW_OBSTACLES:
        # Draw collision boxes
        for object in COLLISION_RECTS:
            pygame.draw.rect(debug_surface, (255, 0, 0, 100), object, 2)
        
        # Draw grid obstacles
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if not pathfinding_grid.is_walkable(x, y):
                    rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    pygame.draw.rect(debug_surface, (255, 0, 0, 50), rect)
    
    # Draw zombie paths if enabled
    if DEBUG_SHOW_PATHS:
        for zombie in zombies:
            if hasattr(zombie, 'path') and zombie.path:
                # Draw path lines
                if len(zombie.path) > 1:
                    points = [pygame.math.Vector2(point) for point in zombie.path]
                    pygame.draw.lines(debug_surface, (0, 255, 0, 200), False, points, 2)
                
                # Draw current target
                if zombie.current_target_index < len(zombie.path):
                    target = zombie.path[zombie.current_target_index]
                    pygame.draw.circle(debug_surface, (255, 255, 0, 200), (int(target[0]), int(target[1])), 5)
                
                # Draw all waypoints
                for point in zombie.path:
                    pygame.draw.circle(debug_surface, (0, 200, 200, 200), (int(point[0]), int(point[1])), 3)
    
    # Blit the debug surface onto the screen
    screen.blit(debug_surface, (0, 0))
    
    # Draw debug HUD 
    debug_text = [
        f"Debug Mode (F2 to toggle)",
        f"Grid: {'ON (F3)' if DEBUG_SHOW_GRID else 'OFF (F3)'}",
        f"Paths: {'ON (F4)' if DEBUG_SHOW_PATHS else 'OFF (F4)'}",
        f"Obstacles: {'ON (F5)' if DEBUG_SHOW_OBSTACLES else 'OFF (F5)'}",
        f"Zombies: {len(zombies)}",
        f"Active Paths: {sum(1 for z in zombies if hasattr(z, 'path') and z.path)}"
    ]
    
    for i, text in enumerate(debug_text):
        text_surface = font.render(text, True, WHITE)
        screen.blit(text_surface, (10, HEIGHT - 150 + i * 25))

def main():
    global zombie_wave, wave_ready, zombie_health, player_money, all_sprites, zombies, bullets, spit_projectiles, player, player_health, farm, DEBUG_MODE, DEBUG_SHOW_GRID, DEBUG_SHOW_OBSTACLES, DEBUG_SHOW_PATHS, background, TEXT_BOBBING_INTERVAL, TEXT_BOBBING_RANGE, TEXT_BOBBING_STEP

    initialize_game() 

    running = True
    try:
        background = pygame.image.load("Images/background.png").convert()
        background = pygame.transform.scale(background, (WIDTH, HEIGHT)) 
    except:
        print("Background image not found! Using fallback color.")
        background = None

    while running:
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BLACK)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F2:  # Toggle debug mode
                    DEBUG_MODE = not DEBUG_MODE
                if DEBUG_MODE:  # Only allow these if in debug mode
                    if event.key == pygame.K_F3:  # Toggle grid
                        DEBUG_SHOW_GRID = not DEBUG_SHOW_GRID
                    if event.key == pygame.K_F4:  # Toggle paths
                        DEBUG_SHOW_PATHS = not DEBUG_SHOW_PATHS
                    if event.key == pygame.K_F5:  # Toggle obstacles
                        DEBUG_SHOW_OBSTACLES = not DEBUG_SHOW_OBSTACLES

                keys = pygame.key.get_pressed()
                if keys[pygame.K_r]:
                    player.start_reload()
                if keys[pygame.K_b]:
                    show_shop()
                if event.key == pygame.K_e:
                    # Check if player is close to farm
                    player_to_farm_dist = math.sqrt((player.rect.centerx - farm.rect.centerx)**2 + 
                                                (player.rect.centery - farm.rect.centery)**2)
                    if player_to_farm_dist < 150:  # Close range check
                        if farm.seed_planted is None:
                            farm.plant_seed()
                        else:
                            farm.harvest_seed()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if player.can_shoot():
                        player.shoot()

                        if player.ammo <= 0:
                            player.start_reload()

            # Trigger next wave after a delay
            if event.type == NEXT_WAVE_EVENT:
                start_next_wave()
                pygame.time.set_timer(NEXT_WAVE_EVENT, 0)  # Stop the event until it's needed again

        # Update all game objects
        all_sprites.update()

        pathfinding_grid.update_zombie_positions(zombies)

        handle_stuck_entities()

        contain_zombies()

        # Update player health (for invincibility frames)
        player_health.update()

        # Check bullet collisions with zombies
        for bullet in bullets:
            hit_zombies = pygame.sprite.spritecollide(bullet, zombies, False)
            for zombie in hit_zombies:
                for _ in range(random.randint(5, 10)):
                    particle = BloodParticle(zombie.rect.centerx, zombie.rect.centery)
                    all_sprites.add(particle)
                zombie.health -= player.weapon.damage 
                bullet.kill()
                if zombie.health <= 0:
                    zombie_death_sound.play()
                    zombie.kill()
        
        # Check spit collisions with player
        if not DEBUG_MODE:
            for spit in pygame.sprite.spritecollide(player, spit_projectiles, True):
                for _ in range(random.randint(3, 6)):
                    particle = BloodParticle(player.rect.centerx, player.rect.centery)
                    all_sprites.add(particle)
                if player_health.take_damage(1):  # 1 heart of damage per spit
                    play_death_animation()
        

        # In the wave progression section (after zombie kill check)
        if len(zombies) == 0 and not wave_ready:
            zombie_wave += 1
            zombie_health += 10  # Regular zombies get stronger each wave ( 10 health per wave seems about the best )
            wave_ready = True
            pygame.time.set_timer(NEXT_WAVE_EVENT, 5000)
            

        # Draw farm
        farm.draw(screen)
        for sprite in all_sprites:
            if isinstance(sprite, Player):
                sprite.draw(screen)
            else:
                screen.blit(sprite.image, sprite.rect.topleft)

        for zombie in zombies:
            if hasattr(zombie, 'stuck_timer') and zombie.stuck_timer > 0:
                current_time = pygame.time.get_ticks()
                if current_time - zombie.stuck_timer > zombie.max_stuck_time:
                    zombie.kill()

        # Draw howering text for farm
        player_to_farm_dist = math.sqrt((player.rect.centerx - farm.rect.centerx)**2 + (player.rect.centery - farm.rect.centery)**2)
        if player_to_farm_dist < 150:
            # Calculate bobbing effect
            current_time = pygame.time.get_ticks()
            bobbing_phase = (current_time // TEXT_BOBBING_INTERVAL) % 4
            
            # Simple state machine for bobbing direction
            if not hasattr(farm, 'bob_offset'):
                farm.bob_offset = 0
                farm.bob_direction = TEXT_BOBBING_STEP
            
            if bobbing_phase == 0:
                farm.bob_direction = TEXT_BOBBING_STEP
            elif bobbing_phase == 2:
                farm.bob_direction = -TEXT_BOBBING_STEP
            
            farm.bob_offset += farm.bob_direction
            farm.bob_offset = max(-TEXT_BOBBING_RANGE, min(TEXT_BOBBING_RANGE, farm.bob_offset))
            
            if farm.seed_planted is None:
                text = font.render("Press E to plant", True, WHITE)
            else:
                if (pygame.time.get_ticks() - farm.seed_planted) / 1000 >= 15:
                    text = font.render("Press E to harvest", True, WHITE)
                else:
                    text = font.render("Growing...", True, WHITE)
            
            # Apply the offset
            text_rect = text.get_rect(center=(farm.rect.centerx, farm.rect.top - 20 + farm.bob_offset))

            screen.blit(text, text_rect)

        # Draw Zombie HB
        for zombie in zombies:
            health_width = 40
            health_height = 5
            bar_x = zombie.rect.centerx - health_width//2
            bar_y = zombie.rect.top - 15
            
            # Draw background ( total health )
            pygame.draw.rect(screen, RED, (bar_x, bar_y, health_width, health_height))

            # Draw current health
            current_width = (zombie.health / zombie.max_health) * health_width
            pygame.draw.rect(screen, GREEN, (bar_x, bar_y, current_width, health_height))

        # Check if wave timeout should happen
        check_wave_timeout()

        # Draw wave warning if active
        if showing_wave_warning:
            draw_wave_warning(screen)

        # Draw HUD
        player_health.draw(screen)
        wave_text = font.render(f"Wave: {zombie_wave}", True, WHITE)
        money_text = font.render(f"Money: {player_money}", True, WHITE)
        screen.blit(wave_text, (10, 10 + player_health.heart_height + 10))
        screen.blit(money_text, (10, 10 + player_health.heart_height + 40))
        player.update_reload()
        player.draw_ammo(screen)

        draw_debug_info(screen)   

        pygame.display.flip()
        clock.tick(FPS)

show_start_menu()
main()

pygame.quit()