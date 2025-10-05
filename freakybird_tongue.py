

# --- Imports ---
import threading
import random
import cv2
import mediapipe as mp
import numpy as np
import time
import pygame
import os

# --- Tongue detection globals ---
tongue_out = False
camera_frame = None

# --- Tongue detector thread ---
def tongue_detector_thread():
    global tongue_out, camera_frame
    camera_frame = None
    mp_face_mesh = mp.solutions.face_mesh
    cap = cv2.VideoCapture(0)
    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    ) as face_mesh:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)
            detected = False
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    top_lip_idx = [13]
                    bottom_lip_idx = [14]
                    top_lip_pt = np.array([int(frame.shape[1]*face_landmarks.landmark[top_lip_idx[0]].x), int(frame.shape[0]*face_landmarks.landmark[top_lip_idx[0]].y)])
                    bottom_lip_pt = np.array([int(frame.shape[1]*face_landmarks.landmark[bottom_lip_idx[0]].x), int(frame.shape[0]*face_landmarks.landmark[bottom_lip_idx[0]].y)])
                    mouth_open = np.linalg.norm(top_lip_pt - bottom_lip_pt)
                    if mouth_open > 18:
                        mouth_box_idx = [78, 308, 13, 14]
                        mouth_box = np.array([[int(frame.shape[1]*face_landmarks.landmark[i].x), int(frame.shape[0]*face_landmarks.landmark[i].y)] for i in mouth_box_idx])
                        x, y, w, h = cv2.boundingRect(mouth_box)
                        mouth_roi = frame[y:y+h, x:x+w]
                        if mouth_roi.size > 0:
                            mouth_roi_yuv = cv2.cvtColor(mouth_roi, cv2.COLOR_BGR2YUV)
                            mouth_roi_yuv[:,:,0] = cv2.equalizeHist(mouth_roi_yuv[:,:,0])
                            mouth_roi_eq = cv2.cvtColor(mouth_roi_yuv, cv2.COLOR_YUV2BGR)
                            hsv = cv2.cvtColor(mouth_roi_eq, cv2.COLOR_BGR2HSV)
                            lower = np.array([160, 80, 80])
                            upper = np.array([179, 255, 255])
                            mask = cv2.inRange(hsv, lower, upper)
                            kernel = np.ones((3,3), np.uint8)
                            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
                            mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel, iterations=1)
                            ratio = cv2.countNonZero(mask) / (w * h)
                            if ratio > 0.12:
                                detected = True
            tongue_out = detected
            camera_frame = frame.copy()
            time.sleep(0.05)

# --- Start tongue detector in a background thread ---
detector_thread = threading.Thread(target=tongue_detector_thread, daemon=True)
detector_thread.start()

# --- Pygame/game setup ---
pygame.init()
clock = pygame.time.Clock()
fps = 60
screen_width = 864
screen_height = 936
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Freaky Bird')
ground_scroll = 0
scroll_speed = 4
bg = pygame.image.load('img/bg.png')
ground_img = pygame.image.load('img/ground.png')
font = pygame.font.SysFont('Comic Sans', 60)
white = (255, 255, 255)
flying = False
game_over = False
pipe_gap = 200
pipe_frequency = 1500
last_pipe = pygame.time.get_ticks() - pipe_frequency
score = 0
pass_pipe = False
button_img = pygame.image.load('img/restart.png')

# --- Highscore file functions ---
HIGHSCORE_FILE = 'highscore.txt'
def load_highscore():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            return 0
    return 0

def save_highscore(val):
    try:
        with open(HIGHSCORE_FILE, 'w') as f:
            f.write(str(val))
    except:
        pass

highscore = load_highscore()

# --- Helper functions ---
def draw_text(text, font, text_color, x, y):
    img = font.render(text, True, text_color)
    screen.blit(img, (x, y))

def reset_game():
    global pass_pipe, score, last_pipe
    pipe_group.empty()
    freaky.rect.x = 100
    freaky.rect.y = int(screen_height / 4)
    freaky.vel = 0
    score = 0
    pass_pipe = False
    last_pipe = pygame.time.get_ticks() - pipe_frequency

# --- Classes ---
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
        global flying, game_over, tongue_out
        # Gravity
        if flying:
            self.vel += 0.3
            if self.vel > 5:
                self.vel = 5
            if self.rect.bottom < 768:
                self.rect.y += int(self.vel)

        # Flap only on tongue out
        if tongue_out and not self.clicked and not game_over:
            self.clicked = True
            self.vel = -6
        if not tongue_out:
            self.clicked = False

        # Animation
        self.counter += 1
        flap_cooldown = 10
        if self.counter > flap_cooldown:
            self.counter = 0
            self.index += 1
            if self.index >= len(self.images):
                self.index = 0
        self.image = self.images[self.index]
        # Rotate
        self.image = pygame.transform.rotate(self.images[self.index], self.vel * -2)

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
freaky = Bird(100, int(screen_height / 4))
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
            save_highscore(highscore)
        if button.draw():
            game_over = False
            reset_game()


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    # Only start flying when tongue is first stuck out (not already flying or game over)
    if tongue_out and not flying and not game_over:
        flying = True

    # --- Webcam preview ---
    if camera_frame is not None:
        cam_rgb = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
        cam_rgb = cv2.resize(cam_rgb, (200, 150))
        cam_surface = pygame.surfarray.make_surface(np.rot90(cam_rgb))
        screen.blit(cam_surface, (screen_width - 210, 10))

    pygame.display.update()

pygame.quit()