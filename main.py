import pygame
import random
import math


"""
Excessive comment lines were used for CTRL + F to find important functions/classes more easily while coding
Every function/class is commented with a space right after #
For easier debugging or testing, edit values that are commented using: " # Edit for cheats and debug "

"""


# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Blood and Blooms")

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

# Font
font = pygame.font.Font(None, 36)

# Game clock
clock = pygame.time.Clock()
FPS = 60


# Inicialization of values for player and zombie 
player_health = 100
zombie_wave = 1
zombie_health = 50
player_money = 0 


# Weapon class
class Weapon:
    def __init__(self, name, image_path, damage, fire_rate, ammo, reload_time, cost, spread=0, projectile_speed=15, is_automatic=False, max_range=500):
        self.name = name
        self.image = pygame.image.load(image_path).convert_alpha()
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
    "Pistol": Weapon("Pistol", "gun.png", 25, 200, 10, 2000, 0, max_range=500),
    "Shotgun": Weapon("Shotgun", "shotgun.png", 100, 500, 6, 3000, 50, spread=30, max_range=200),  
    "Rifle": Weapon("Rifle", "rifle.png", 35, 100, 20, 2500, 100, is_automatic=True, projectile_speed=15,  max_range=600),
    "Sniper": Weapon("Sniper", "sniper.png", 1000, 200, 5, 4000, 200, projectile_speed=30, max_range=2000)  
}
weapons["Pistol"].purchased = True  # Starting weapon is already purchased


# Shop function
def show_shop():
    shop_running = True
    popup_message = None
    popup_start_time = 0
    POPUP_DURATION = 2000  

    def handle_weapon_selection(weapon_name, key_number, weapon):
        global player_money, popup_message, popup_start_time
        
        if weapon.purchased:
            player.equip_weapon(weapon_name)
        else:
            if player_money >= weapon.cost:
                player_money -= weapon.cost
                weapon.purchased = True
                player.purchased_weapons.append(weapon_name)
                player.equip_weapon(weapon_name)
            else:
                popup_message = "Not enough money!"
                popup_start_time = pygame.time.get_ticks()

    while shop_running:
        screen.fill(BLACK)
        
        # Current balance
        balance_text = font.render(f"Balance: ${player_money}", True, WHITE)
        screen.blit(balance_text, (WIDTH//2 - balance_text.get_width()//2, 30))
        
        # Shop title
        title_text = font.render("Shop (Press 1-3 to buy/equip, ESC to exit)", True, WHITE)
        screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 80))
        
        # Weapon listings
        y_offset = 150
        for i, (weapon_name, weapon) in enumerate(weapons.items(), 1):
            if weapon_name == "Pistol":
                continue  # Skip default weapon
            
            # Weapon entry
            text_color = WHITE
            status = ""
            
            if weapon_name == player.weapon.name:
                status = " (Equipped)"
                text_color = GREEN
            elif weapon.purchased:
                status = " (Purchased)"
                text_color = LIGHT_GRAY
            
            entry_text = f"{i-1}. {weapon_name}{status} - ${weapon.cost if not weapon.purchased else 'OWNED'}"
            text_surface = font.render(entry_text, True, text_color)
            screen.blit(text_surface, (WIDTH//2 - 200, y_offset))
            
            # Weapon stats
            stats_text = f"Dmg: {weapon.damage} | Fire Rate: {weapon.fire_rate/1000} s | Ammo: {weapon.ammo}" # Note for my self: Consider showing fire rate in more understandible way
            stats_surface = font.render(stats_text, True, LIGHT_GRAY)
            screen.blit(stats_surface, (WIDTH//2 - 200, y_offset + 30))
            
            y_offset += 80

        # Display popup message if active
        if popup_message and pygame.time.get_ticks() - popup_start_time < POPUP_DURATION:
            popup_surface = font.render(popup_message, True, RED)
            screen.blit(popup_surface, (WIDTH//2 - popup_surface.get_width()//2, HEIGHT - 100))
        
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    shop_running = False
                
                # Handle weapon selection
                if event.key == pygame.K_1:
                    handle_weapon_selection("Shotgun", 1, weapons["Shotgun"])
                if event.key == pygame.K_2:
                    handle_weapon_selection("Rifle", 2, weapons["Rifle"])
                if event.key == pygame.K_3:
                    handle_weapon_selection("Sniper", 3, weapons["Sniper"])

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((50, 50), pygame.SRCALPHA)  # Transparent square for the player
        pygame.draw.circle(self.image, GREEN, (25, 25), 25)  # Draw a green circle for the player
        self.weapon = weapons["Pistol"]
        self.purchased_weapons = ["Pistol"]
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.gun_offset = 20  # Distance of gun from center
        self.speed = 5
        self.angle = 10
        self.ammo = self.weapon.ammo
        self.is_reloading = False
        self.last_shot_time = 0
        self.reload_start_time = 0
        
    def equip_weapon(self, weapon_name):
        if weapon_name in self.purchased_weapons:
            self.weapon = weapons[weapon_name]
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
            # Add a reload sound effect here
    
    def update_reload(self):
        if self.is_reloading:
            current_time = pygame.time.get_ticks()
            if current_time - self.reload_start_time >= self.weapon.reload_time:
                self.ammo = self.weapon.ammo
                self.is_reloading = False
                # Add a reload complete sound effect here

    def draw_ammo(self, screen):
        # Draw ammo counter
        ammo_text = font.render(f"Ammo: {str(self.ammo) +"/"+ str(self.weapon.ammo)}", True, BLACK)
        screen.blit(ammo_text, (WIDTH - 160, 10))
        
        # Draw reload indicator
        if self.is_reloading:
            reload_text = font.render("Reloading...", True, RED)
            screen.blit(reload_text, (WIDTH - 160, 40))
            
            # Draw reload progress bar
            progress_width = 100
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.reload_start_time
            progress = min(elapsed / self.weapon.reload_time, 1.0)
            
            pygame.draw.rect(screen, LIGHT_GRAY, 
                           (WIDTH - 140, 70, progress_width, 10))
            pygame.draw.rect(screen, GREEN, 
                           (WIDTH - 140, 70, int(progress_width * progress), 10))

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_s] and self.rect.bottom < HEIGHT:
            self.rect.y += self.speed
        if keys[pygame.K_a] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_d] and self.rect.right < WIDTH:
            self.rect.x += self.speed

        # Update angle based on mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        rel_x, rel_y = mouse_x - self.rect.centerx, mouse_y - self.rect.centery
        self.angle = math.degrees(-math.atan2(rel_y, rel_x))

        # Automatic firing for rifles
        if self.weapon.is_automatic and keys[pygame.K_SPACE]:
            self.shoot()

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)  # Draw player

        # Rotate gun properly and position it correctly
        rotated_gun = pygame.transform.rotate(self.weapon.image, self.angle)
        gun_rect = rotated_gun.get_rect(center=self.rect.center)  # Keep gun centered

        # Adjust gun position to move with the player
        gun_x = self.rect.centerx + self.gun_offset * math.cos(math.radians(self.angle))
        gun_y = self.rect.centery - self.gun_offset * math.sin(math.radians(self.angle))

        gun_rect.center = (gun_x, gun_y)
        screen.blit(rotated_gun, gun_rect.topleft)  # Draw rotated gun
    
    def shoot(self):
        if self.can_shoot():
            direction = pygame.math.Vector2(
                math.cos(math.radians(self.angle)),
                -math.sin(math.radians(self.angle))
            ).normalize()

            # Create muzzle flash
            gun_length = 40
            muzzle_x = self.rect.centerx + gun_length * direction.x
            muzzle_y = self.rect.centery + gun_length * direction.y
            muzzle_flash = MuzzleFlash(muzzle_x, muzzle_y, self.angle)
            all_sprites.add(muzzle_flash)

            # Handle weapon-specific shooting
            if self.weapon.name == "Shotgun":
                self.shotgun_shot(direction, gun_length)
            elif self.weapon.name == "Rifle":
                self.rifle_shot(direction, gun_length)
            elif self.weapon.name == "Sniper":
                self.sniper_shot(direction, gun_length)
            else:
                self.pistol_shot(direction, gun_length)

            # Update ammo and cooldown
            self.ammo -= 1
            self.last_shot_time = pygame.time.get_ticks()

            # Auto-reload when empty
            if self.ammo <= 0:
                self.start_reload()

    def shotgun_shot(self, direction, gun_length): # Does not work, fix later maybe
            
            # Pass projectile_speed and max_range from the weapon
            bullet = Bullet(
                self.rect.centerx, self.rect.centery, gun_length, 
                speed=self.weapon.projectile_speed,
                max_distance=self.weapon.max_range
            )
            all_sprites.add(bullet)
            bullets.add(bullet)

    def sniper_shot(self, direction, gun_length):
        print("Shot")
        # Pass projectile_speed and max_range directly
        bullet = Bullet(
            self.rect.centerx, self.rect.centery,
            direction, gun_length, self.angle,
            self.weapon.projectile_speed,
            self.weapon.max_range
        )
        all_sprites.add(bullet)
        bullets.add(bullet)


    def rifle_shot(self, direction, gun_length):
        bullet = Bullet(
            self.rect.centerx, self.rect.centery,
            direction, gun_length, self.angle,
            self.weapon.projectile_speed,
            self.weapon.max_range
        )
        all_sprites.add(bullet)
        bullets.add(bullet)

    def pistol_shot(self, direction, gun_length):
        bullet = Bullet(
            self.rect.centerx, self.rect.centery,
            direction, gun_length, self.angle,
            self.weapon.projectile_speed,
            self.weapon.max_range
        )
        all_sprites.add(bullet)
        bullets.add(bullet)



# MuzzleFlasash class
class MuzzleFlash(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        self.alpha = 255
        self.layers = []
        
        # Generate random flash characteristics
        flash_size = random.randint(20, 30)
        num_spikes = random.randint(4, 8)
        spike_length = random.randint(8, 15)
        
        # Create main flash surface
        self.image = pygame.Surface((flash_size * 2, flash_size * 2), pygame.SRCALPHA)
        
        # Add bright core
        core_color = (255, 255, 150, self.alpha)
        pygame.draw.circle(self.image, core_color, 
                          (flash_size, flash_size), 
                          random.randint(3, 5))
        
        # Add glowing spikes
        spike_color = (255, 180, 50, self.alpha)
        for i in range(num_spikes):
            angle_deg = (360 / num_spikes) * i
            rad = math.radians(angle_deg)
            start_x = flash_size + math.cos(rad) * 5
            start_y = flash_size + math.sin(rad) * 5
            end_x = flash_size + math.cos(rad) * spike_length
            end_y = flash_size + math.sin(rad) * spike_length
            pygame.draw.line(self.image, spike_color,
                            (start_x, start_y), (end_x, end_y),
                            random.randint(2, 4))

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
    def __init__(self, x, y, direction, gun_length, angle, projectile_speed, max_range):
        super().__init__()
        self.speed = projectile_speed
        self.max_distance = max_range
        self.distance_traveled = 0  # Track how far the bullet has traveled
        self.width = 15
        self.height = 8

        # Create the original bullet image with a black outline
        self.original_image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(self.original_image, YELLOW, (0, 0, self.width, self.height))  # Yellow bullet
        pygame.draw.rect(self.original_image, BLACK, (0, 0, self.width, self.height), 2)  # Black outline

        # Rotate the bullet to face the correct direction
        self.image = pygame.transform.rotate(self.original_image, -angle)
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction
        self.rect.centerx = x + gun_length * self.direction.x
        self.rect.centery = y + gun_length * self.direction.y

    def update(self):
        dx = self.speed * self.direction.x
        dy = self.speed * self.direction.y
        self.rect.x += dx
        self.rect.y += dy
        self.distance_traveled += math.sqrt(dx**2 + dy**2)  # Update distance traveled

        # Check if the bullet has exceeded its max distance
        if self.max_distance is not None and self.distance_traveled > self.max_distance:
            self.kill()
        else:
            if (self.rect.right < 0 or self.rect.left > WIDTH or
                self.rect.top > HEIGHT or self.rect.bottom < 0):
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

# Zombie class
class Zombie(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path):
        super().__init__()
        self.original_image = pygame.image.load(image_path).convert_alpha()
        self.image = self.original_image  # Default image without rotation
        self.rect = self.image.get_rect(center=(x, y))
        
        # Adjust speed based on wave
        self.base_speed = 1.5  # Base zombie speed
        self.speed = self.base_speed + (zombie_wave * 0.1)  # Slight speed increase per wave
        self.max_health = zombie_health
        self.health = zombie_health
        self.target_offset = pygame.math.Vector2(random.uniform(-30, 30), random.uniform(-30, 30))  # Spread out movement

    def update(self):
        # Find direction toward the player
        target_pos = pygame.math.Vector2(player.rect.center) + self.target_offset
        zombie_pos = pygame.math.Vector2(self.rect.center)
        
        # Calculate movement direction
        direction = (target_pos - zombie_pos).normalize() if target_pos != zombie_pos else pygame.math.Vector2(0, 0)
        
        # Move zombie
        self.rect.x += direction.x * self.speed
        self.rect.y += direction.y * self.speed

        # Rotate the zombie to face the player
        rel_x, rel_y = player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery
        angle = math.degrees(-math.atan2(rel_y, rel_x))
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

class TankZombie(Zombie): 
    def __init__(self, x, y, image_path):
        super().__init__(x, y, image_path)
        self.base_speed = 0.8
        self.max_health = 150 + (zombie_wave * 15)
        self.health = self.max_health
        self.speed = self.base_speed + (zombie_wave * 0.05)

class RunnerZombie(Zombie):
    def __init__(self, x, y, image_path):
        super().__init__(x, y, image_path)
        self.base_speed = 3.20
        self.max_health = 30 + (zombie_wave * 5)
        self.health = self.max_health
        self.speed = self.base_speed + (zombie_wave * 0.15)

class SpitterZombie(Zombie):
    def __init__(self, x, y, image_path):
        super().__init__(x, y, image_path)
        self.base_speed = 1.0
        self.max_health = 80 + (zombie_wave * 8)
        self.health = self.max_health
        self.speed = self.base_speed + (zombie_wave * 0.1)
        self.attack_cooldown = 2000
        self.last_attack = 0

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
                player_money += 10
                self.seed_planted = None
                self.stalks = []  # Clear the stalks after harvesting

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

            # Display "Mature!" text above the farm when fully grown
            if growth_percentage >= 1.0:
                text = font.render("Mature!", True, WHITE)
                text_rect = text.get_rect(center=(self.rect.centerx, self.rect.top - 20))
                screen.blit(text, text_rect)

        
# Function to show the starting menu
def show_start_menu():
    while True:
        screen.fill(BLACK)
        menu = pygame.image.load("menu.jpg").convert_alpha()
        screen.blit(menu, (0, 0))
        
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return

# Function to show the death screen
def show_death_screen():
    while True:
        screen.fill(BLACK)
        game_over_text = font.render("Game Over", True, WHITE)
        restart_text = font.render("Press R to Restart or Q to Quit", True, WHITE)
        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 10))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    main()  # Restart the game
                if event.key == pygame.K_q:
                    pygame.quit()
                    exit()



def handle_zombie_collisions():
        zombies_list = zombies.sprites()
        for i in range(len(zombies_list)):
            for j in range(i + 1, len(zombies_list)):
                zombie1 = zombies_list[i]
                zombie2 = zombies_list[j]
                if pygame.sprite.collide_rect(zombie1, zombie2):
                    # Calculate vector between centers
                    dx = zombie1.rect.centerx - zombie2.rect.centerx
                    dy = zombie1.rect.centery - zombie2.rect.centery
                    distance = math.hypot(dx, dy)
                    
                    if distance == 0:
                        dx = 1
                        dy = 0
                        distance = 5
                    
                    # Calculate minimum distance to prevent overlap (sum of radii)
                    min_distance = (zombie1.rect.width + zombie2.rect.width) / 2  # Both are 40px wide
                    overlap = min_distance - distance
                    
                    if overlap > 0:
                        # Move each zombie away by half the overlap
                        move_x = (dx / distance) * overlap / 2
                        move_y = (dy / distance) * overlap / 2
                        zombie1.rect.x += move_x
                        zombie1.rect.y += move_y
                        zombie2.rect.x -= move_x
                        zombie2.rect.y -= move_y

# Sprite groups
all_sprites = pygame.sprite.Group()
player = Player()
all_sprites.add(player)
spit_projectiles = pygame.sprite.Group()
bullets = pygame.sprite.Group()
zombies = pygame.sprite.Group()

farm = Farm()


# Define a new event for wave progression
NEXT_WAVE_EVENT = pygame.USEREVENT + 2

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
    global wave_ready
    wave_ready = False
    spawn_zombie()




def main():
    global player_health, zombie_wave, wave_ready, zombie_health, player_money
    player_health = 100 # Edit for cheats and debug
    zombie_wave = 0 # Edit for cheats and debug
    player_money = 0 # Edit for cheats and debug
    wave_ready = False

    # Clear all groups
    all_sprites.empty()
    zombies.empty()
    bullets.empty()
    spit_projectiles.empty()
    zombie_health = 100
    
    # Add player back
    all_sprites.add(player)
    
    # Start the first wave
    start_next_wave()

    running = True
    while running:
        screen.fill(LIGHT_GRAY)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE] and player.can_shoot():
                    
                    direction = pygame.math.Vector2(
                        math.cos(math.radians(player.angle)),
                        -math.sin(math.radians(player.angle))
                    )
                    
                    # Create muzzle flash and bullet
                    gun_length = 40  # Distance from the player's center to the muzzle
                    muzzle_x = player.rect.centerx + gun_length * direction.x
                    muzzle_y = player.rect.centery + gun_length * direction.y
                    
                    muzzle_flash = MuzzleFlash(muzzle_x, muzzle_y, player.angle)
                    all_sprites.add(muzzle_flash)
                    
                    # Create the bullet
                    bullet = Bullet(player.rect.centerx, player.rect.centery, 
                                    direction, gun_length, player.angle, player.weapon.projectile_speed, player.weapon.max_range)
                    all_sprites.add(bullet)
                    bullets.add(bullet)
                    
                    # Update ammo and cooldown
                    player.ammo -= 1
                    player.last_shot_time = pygame.time.get_ticks()
                    
                    # Auto-reload when empty
                    if player.ammo <= 0:
                        player.start_reload()
                
                if keys[pygame.K_r]:
                    player.start_reload()
                if keys[pygame.K_b]:
                    show_shop()




            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if farm.rect.collidepoint(event.pos):
                        if farm.seed_planted is None:
                            farm.plant_seed()
                        else:
                            farm.harvest_seed()

            # Trigger next wave after a delay
            if event.type == NEXT_WAVE_EVENT:
                start_next_wave()
                pygame.time.set_timer(NEXT_WAVE_EVENT, 0)  # Stop the event until it's needed again

        # Update all game objects
        all_sprites.update()

        handle_zombie_collisions()

        # Check bullet collisions with zombies
        for bullet in bullets:
            hit_zombies = pygame.sprite.spritecollide(bullet, zombies, False)
            for zombie in hit_zombies:
                zombie.health -= player.weapon.damage 
                bullet.kill()
                if zombie.health <= 0:
                    zombie.kill()
        
        # Check spit collisions with player
        for spit in pygame.sprite.spritecollide(player, spit_projectiles, True):
            player_health -= 10
            if player_health <= 0:
                show_death_screen()

        # Check if player is hit by zombies
        if pygame.sprite.spritecollide(player, zombies, False):
            player_health -= 1
            if player_health <= 0:
                show_death_screen()
                running = False

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

        # Draw HUD
        health_text = font.render(f"Player Health: {player_health}", True, BLACK)
        wave_text = font.render(f"Wave: {zombie_wave}", True, BLACK)
        money_text = font.render(f"Money: {player_money}", True, BLACK)
        screen.blit(health_text, (10, 10))
        screen.blit(wave_text, (10, 40))
        screen.blit(money_text, (10, 70))
        player.update_reload()
        player.draw_ammo(screen)

        pygame.display.flip()
        clock.tick(FPS)

show_start_menu()
main()

pygame.quit()
