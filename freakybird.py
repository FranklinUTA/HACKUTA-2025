import pygame
from pygame.locals import *
import random
import requests
import subprocess
import time
import sys
import os

# --- Start backend automatically ---
backend_process = None
try:
    # Assumes freakybackend.py is in the same directory
    backend_process = subprocess.Popen([sys.executable, "freakybackend.py"])
    # Give backend time to start
    time.sleep(1)
except Exception as e:
    print("Could not start backend:", e)

pygame.init()

clock = pygame.time.Clock()
fps = 60

screen_width = 864
screen_height = 936

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Freaky Bird')

# --- Font & colors ---
font = pygame.font.SysFont('Comic Sans', 60)
white = (255, 255, 255)

# --- Game variables ---
ground_scroll = 0
scroll_speed = 4
flying = False
game_over = False
pipe_gap = 200
pipe_frequency = 1500
last_pipe = pygame.time.get_ticks() - pipe_frequency
score = 0
pass_pipe = False

# --- Load images ---
bg = pygame.image.load('img/bg.png')
ground_img = pygame.image.load('img/ground.png')
button_img = pygame.image.load('img/restart.png')

# --- Backend highscore functions ---
def get_highscore():
    try:
        response = requests.get('http://127.0.0.1:5000/get_highscore')
        return response.json()['highscore']
    except:
        return 0

def set_highscore(score):
    try:
        requests.post('http://127.0.0.1:5000/set_highscore', json={'score': score})
    except:
        pass

highscore = get_highscore()

# --- Helper functions ---
def draw_text(text, font, text_color, x, y):
    img = font.render(text, True, text_color)
    screen.blit(img, (x, y))

def reset_game():
    global pass_pipe, score
    pipe_group.empty()
    freaky.rect.x = 100
    freaky.rect.y = int(screen_height / 2)
    score = 0
    pass_pipe = False

# --- Classes (Bird, Pipe, Button) ---
class Bird(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        self.index = 0
        self.counter = 0
        for num in range(1, 4):
            img = pygame.image.load(f'img/bird{num}.png')
            self.images.append(img)
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.vel = 0
        self.clicked = False

    def update(self):
        global flying, game_over
        if flying:
            self.vel += 0.5
            if self.vel > 8:
                self.vel = 8
            if self.rect.bottom < 768:
                self.rect.y += int(self.vel)

        if not game_over:
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                self.clicked = True
                self.vel = -10
            if pygame.mouse.get_pressed()[0] == 0:
                self.clicked = False

            self.counter += 1
            if self.counter > 10:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images):
                    self.index = 0
            self.image = pygame.transform.rotate(self.images[self.index], self.vel * -2)
        else:
            self.image = pygame.transform.rotate(self.images[self.index], -90)

class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, position):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('img/pipe.png')
        self.rect = self.image.get_rect()
        if position == 1:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect.bottomleft = [x, y - int(pipe_gap / 2)]
        if position == -1:
            self.rect.topleft = [x, y + int(pipe_gap / 2)]

    def update(self):
        self.rect.x -= scroll_speed
        if self.rect.right < 0:
            self.kill()

class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def draw(self):
        action = False
        pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1:
                action = True
        screen.blit(self.image, (self.rect.x, self.rect.y))
        return action

# --- Groups ---
bird_group = pygame.sprite.Group()
pipe_group = pygame.sprite.Group()

freaky = Bird(100, int(screen_height / 2))
bird_group.add(freaky)

button = Button(screen_width // 2 - 50, screen_height // 2 - 100, button_img)

# --- Game loop ---
run = True
while run:
    clock.tick(fps)
    screen.blit(bg, (0, 0))

    bird_group.draw(screen)
    bird_group.update()
    pipe_group.draw(screen)
    screen.blit(ground_img, (ground_scroll, 768))

    # --- Collision ---
    if pygame.sprite.groupcollide(bird_group, pipe_group, False, False) or freaky.rect.top < 0:
        game_over = True

    # --- Scoring ---
    if len(pipe_group) > 0:
        if freaky.rect.left > pipe_group.sprites()[0].rect.left and freaky.rect.right < pipe_group.sprites()[0].rect.right and not pass_pipe:
            pass_pipe = True
        if pass_pipe:
            if freaky.rect.left > pipe_group.sprites()[0].rect.right:
                score += 1
                pass_pipe = False

    draw_text(f'Score: {score}', font, white, 10, 80)
    draw_text(f'Highscore: {highscore}', font, white, 10, 20)

    # --- Ground collision ---
    if freaky.rect.bottom >= 768:
        game_over = True
        flying = False

    # --- Pipe generation & ground scrolling ---
    if flying and not game_over:
        time_now = pygame.time.get_ticks()
        if time_now - last_pipe > pipe_frequency:
            pipe_height = random.randint(-125, 125)
            btm_pipe = Pipe(screen_width, int(screen_height / 2) + pipe_height, -1)
            top_pipe = Pipe(screen_width, int(screen_height / 2) + pipe_height, 1)
            pipe_group.add(btm_pipe)
            pipe_group.add(top_pipe)
            last_pipe = time_now

        ground_scroll -= scroll_speed
        if abs(ground_scroll) > 35:
            ground_scroll = 0

        pipe_group.update()

    # --- Game over handling ---
    if game_over:
        if score > highscore:
            highscore = score
            set_highscore(highscore)
        if button.draw():
            game_over = False
            reset_game()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.MOUSEBUTTONDOWN and not flying and not game_over:
            flying = True

    pygame.display.update()

# --- Clean up backend when game closes ---
if backend_process:
    backend_process.terminate()

pygame.quit()
