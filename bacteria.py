import pygame
import math
import random

# === CONFIGURATION ===
WIDTH, HEIGHT = 800, 600
DOT_COUNT = 150
DOT_RADIUS = 5
FOOD_RADIUS = 3
FOOD_COUNT = 100
FPS = 30

# === COLORS ===

WHITE = (255, 255, 255)
BLUE = (0, 0, 255)        # Healthy
RED = (255, 0, 0)    # Infected
GREEN = (0, 255, 0)       # Immune
OLIVE_GREEN = (186, 184, 108)

# === Pygame Initialization ===
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bacterial Simulation")
clock = pygame.time.Clock()
FOOD_GENERATION_INTERVAL = 50  # in milliseconds (0.05 second)
last_food_spawn_time = pygame.time.get_ticks()
INFECTION_INTERVAL = 50000  # 50 seconds
last_infection_time = pygame.time.get_ticks()

# === Dot Class ===
class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = random.uniform(1, 2)
        self.direction = random.uniform(0, 360)
        self.infected = False
        self.health = 85
        self.immune = False
        self.infected_time = None
        self.infection_duration = 10000  # Reduced for quicker testing
        self.recovery_checked = False
        self.division_pending = False
        self.division_time = None
        self.last_eaten_time = pygame.time.get_ticks()  # initialize at creation
        self.eat_count = 0  # counts how many food items this dot has eaten
        self.immune_time = None  # Track when dot became immune
        self.immunity_duration = 10000  # 10 seconds of immunity

    def change_direction(self):
        self.direction = random.uniform(0, 360)

    def move(self):
        angle = math.radians(self.direction)
        self.x += self.speed * math.cos(angle)
        self.y += self.speed * math.sin(angle)

        if self.x - DOT_RADIUS < 0 or self.x + DOT_RADIUS > WIDTH:
            self.direction = 180 - self.direction
        if self.y - DOT_RADIUS < 0 or self.y + DOT_RADIUS > HEIGHT:
            self.direction = -self.direction

        self.x = max(DOT_RADIUS, min(WIDTH - DOT_RADIUS, self.x))
        self.y = max(DOT_RADIUS, min(HEIGHT - DOT_RADIUS, self.y))

    def is_colliding(self, other):
        distance = math.hypot(self.x - other.x, self.y - other.y)
        return distance < 2 * DOT_RADIUS

    def eat_food(self, food_list):
        for food in food_list[:]:
            if math.hypot(self.x - food[0], self.y - food[1]) < DOT_RADIUS + FOOD_RADIUS:
                self.health = min(100, self.health + (3 if self.infected else 10))
                food_list.remove(food)
                self.eat_count += 1
                self.last_eaten_time = pygame.time.get_ticks()

                if not self.infected and self.eat_count >= 3 and not self.division_pending:
                    self.division_pending = True
                    self.division_time = pygame.time.get_ticks() + 1000  # 1 second delay
                    self.eat_count = 0  # reset counter after triggering division

    def update_health(self):
        current_time = pygame.time.get_ticks()

        # === Infected health deterioration ===
        if self.infected:
            self.health -= 0.3

            if not self.recovery_checked and self.infected_time is not None:
                if current_time - self.infected_time >= self.infection_duration:
                    self.recovery_checked = True
                    if random.random() < 0.7:
                        self.infected = False
                        self.immune = True
                        self.health = 100
                        self.infected_time = None
                        self.immune_time = current_time  # Start immunity timer
                        return "alive"
                    else:
                        return "dead"

            if self.health <= 0:
                return "dead"

        # === Immunity expiration check ===
        if self.immune and self.immune_time is not None:
            if current_time - self.immune_time >= self.immunity_duration:
                self.immune = False
                self.immune_time = None

        # === Starvation death ===
        if current_time - self.last_eaten_time >= 20000:  # 20 sec
            return "dead"

        return "alive"

    def ready_to_divide(self):
        if self.division_pending and pygame.time.get_ticks() >= self.division_time:
            self.division_pending = False
            self.division_time = None
            return True
        return False

    def update(self, food_list):
        self.move()
       # if random.randint(0, 100) < 5:
       #     self.change_direction()
        self.eat_food(food_list)
        return self.update_health()

# === Helper Functions ===
def generate_dots(n):
    return [Dot(random.randint(DOT_RADIUS, WIDTH - DOT_RADIUS),
                random.randint(DOT_RADIUS, HEIGHT - DOT_RADIUS)) for _ in range(n)]

def generate_food(n):
    return [(random.randint(FOOD_RADIUS, WIDTH - FOOD_RADIUS),
             random.randint(FOOD_RADIUS, HEIGHT - FOOD_RADIUS)) for _ in range(n)]

def spread_infection(dot1, dot2):
    if dot1.infected and not dot2.infected and not dot2.immune:
        dot2.infected = True
        if dot2.infected_time is None:
            dot2.infected_time = pygame.time.get_ticks()
        dot2.recovery_checked = False
    elif dot2.infected and not dot1.infected and not dot1.immune:
        dot1.infected = True
        if dot1.infected_time is None:
            dot1.infected_time = pygame.time.get_ticks()
        dot1.recovery_checked = False

def handle_collisions(dots):
    for i, dot1 in enumerate(dots):
        for j in range(i + 1, len(dots)):
            dot2 = dots[j]
            if dot1.is_colliding(dot2):
                dot1.change_direction()
                dot2.change_direction()
                dot1.move()
                dot2.move()
                spread_infection(dot1, dot2)

def draw_dots(dots):
    for dot in dots:
        if dot.infected:
            color = RED
        elif dot.immune:
            color = GREEN
        else:
            color = BLUE

        radius = DOT_RADIUS + 2 if dot.division_pending else DOT_RADIUS
        pygame.draw.circle(screen, color, (int(dot.x), int(dot.y)), radius)

def draw_food(food_list):
    for food in food_list:
        pygame.draw.circle(screen, OLIVE_GREEN, (food[0], food[1]), FOOD_RADIUS)

# === Main Program ===
dots = generate_dots(DOT_COUNT)
food_items = generate_food(FOOD_COUNT)

if dots:
    patient_zero = random.choice(dots)
    patient_zero.infected = True
    patient_zero.infected_time = pygame.time.get_ticks()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # === Food Generation ===
    current_time = pygame.time.get_ticks()
    if current_time - last_food_spawn_time >= FOOD_GENERATION_INTERVAL:
        food_x = random.randint(FOOD_RADIUS, WIDTH - FOOD_RADIUS)
        food_y = random.randint(FOOD_RADIUS, HEIGHT - FOOD_RADIUS)
        food_items.append((food_x, food_y))
        last_food_spawn_time = current_time


    screen.fill(WHITE)
    new_dots = []
    division_lines = []

    alive_dots = []
    for dot in dots:
        if dot.update(food_items) == "alive":
            if dot.ready_to_divide():
                angle = math.radians(random.uniform(0, 360))
                offset = 12
                new_x = dot.x + offset * math.cos(angle)
                new_y = dot.y + offset * math.sin(angle)
                new_dot = Dot(new_x, new_y)

                if dot.immune:
                    new_dot.immune = True

                new_dot.health = 50
                dot.health = 50
                new_dots.append(new_dot)
                division_lines.append(((dot.x, dot.y), (new_dot.x, new_dot.y)))

            alive_dots.append(dot)

    dots = alive_dots + new_dots

    handle_collisions(dots)
    draw_dots(dots)
    draw_food(food_items)

    for line in division_lines:
        pygame.draw.line(screen, WHITE, line[0], line[1], 2)

    # === Infect random blue bacteria every 30 seconds ===
    if pygame.time.get_ticks() - last_infection_time >= INFECTION_INTERVAL:
        healthy_dots = [dot for dot in dots if not dot.infected and not dot.immune]
        if healthy_dots:
            new_patient = random.choice(healthy_dots)
            new_patient.infected = True
            new_patient.infected_time = pygame.time.get_ticks()
            new_patient.recovery_checked = False
            last_infection_time = pygame.time.get_ticks()


    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
