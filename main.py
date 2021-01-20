from abc import abstractmethod
from random import randrange
import pygame
import sqlite3

HEIGHT, WIDTH = 800, 1200
CON = sqlite3.connect("players.db")
CUR = CON.cursor()
FPS = 60


class App:
    def __init__(self):
        self._state = None
        pygame.init()
        self._screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self._running = True
        self._clock = pygame.time.Clock()

    def set_state(self, state):
        self._state = state
        self._state.set_app(self)
        self._state.setup()

    def get_screen(self):
        return self._screen

    def run(self):
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                self._state.process_event(event)
            dt = self._clock.tick(FPS)
            self._state.loop(dt)
            pygame.display.flip()
        self._state.destroy()


class AppState:
    def __init__(self):
        self._app = None

    def set_app(self, app):
        self._app = app

    def get_app(self):
        return self._app

    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def process_event(self, event):
        pass

    @abstractmethod
    def loop(self, dt):
        pass

    @abstractmethod
    def destroy(self):
        pass


class MenuState(AppState):
    def __init__(self, background_image):
        super().__init__()
        self._but_new_game = Button()
        self._record_but = Button()
        self._find = Button()
        self._open = Button()
        self._name = InputBox(500, 150, 200, 50, (66, 170, 255), (35, 52, 110))
        self._bg_img = imgs[background_image]

    def setup(self):
        pygame.display.set_caption('Arkanoid')
        self._bg_img = pygame.transform.scale(self._bg_img, (WIDTH, HEIGHT))

    def process_event(self, event):
        self._name.press(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._but_new_game.pressed(pygame.mouse.get_pos()):
                self._total = self._name.ret_total()
                CUR.execute("""INSERT INTO players(name, score) VALUES(?, ?);""", self._total)
                CON.commit()
                self.get_app().set_state(GameState(randrange(0, 2)))
            elif self._record_but.pressed(pygame.mouse.get_pos()):
                self.get_app().set_state(RecState('recbackground'))
            elif self._open.pressed(pygame.mouse.get_pos()):
                self.get_app().set_state(GameState(0))
            elif self._find.pressed(pygame.mouse.get_pos()):
                self.get_app().set_state(GameState(1))

    def loop(self, dt):
        screen = self.get_app().get_screen()
        screen.fill((0, 0, 0))
        screen.blit(self._bg_img, (0, 0))
        self._name.draw(screen)
        self._open.do(screen, (66, 170, 255), 100, 475, 400, 75, 0, "OPEN MODE", (35, 52, 110))
        self._find.do(screen, (66, 170, 255), 700, 475, 400, 75, 0, "HIDE AND SEEK MODE", (35, 52, 110))
        self._but_new_game.do(screen, (66, 170, 255), 500, 350, 200, 50, 0, "PLAY", (35, 52, 110))
        self._record_but.do(screen, (66, 170, 255), 500, 650, 200, 50, 0, "RECORDS", (35, 52, 110))

    def destroy(self):
        pass


class RecState(AppState):
    def __init__(self, background_image):
        super().__init__()
        self._play_but = Button()
        self._name = InputBox(300, 725, 200, 50, (66, 170, 255), (35, 52, 110))
        self._bg_img = imgs[background_image]

    def setup(self):
        self._bg_img = pygame.transform.scale(self._bg_img, (WIDTH, HEIGHT))

    def process_event(self, event):
        self._name.press(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._play_but.pressed(pygame.mouse.get_pos()):
                self._total = self._name.ret_total()
                CUR.execute("""INSERT INTO players(name, score) VALUES(?, ?);""", self._total)
                CON.commit()
                self.get_app().set_state(GameState())

    def loop(self, dt):
        screen = self.get_app().get_screen()
        screen.fill((0, 0, 0))
        screen.blit(self._bg_img, (0, 0))
        result = CUR.execute("""SELECT score FROM players WHERE score!=0;""").fetchall()
        result.sort(reverse=True)
        with open('text_for_top.txt', mode='w') as out_file:
            if len(result) > 10:
                for i in range(1, 11):
                    total = CUR.execute("SELECT name FROM players WHERE score=?;", result[i]).fetchone()
                    print('', i + 1, total[0], result[i][0], file=out_file, sep='      ', end=';')
            else:
                for i in range(len(result)):
                    total = CUR.execute("SELECT name FROM players WHERE score=?;", result[i]).fetchone()
                    print('', i + 1, total[0], result[i][0], file=out_file, sep='      ', end=';')
        with open('text_for_top.txt', mode='r') as file:
            self._rect = pygame.Rect(200, 100, 800, 600)
            pygame.draw.rect(screen, (255, 255, 255), self._rect, 0)
            self._font = pygame.font.SysFont("Calibri", 30)
            self._text = file.readline().split(';')
            kol = 1
            for i in self._text:
                kol += 1
                self._txt_surface = self._font.render(i, True, (0, 0, 0))
                screen.blit(self._txt_surface, (self._rect.x + 150, self._rect.y + 40 * kol))
        CON.commit()
        self._name.draw(screen)
        self._play_but.do(screen, (66, 170, 255), 600, 725, 200, 50, 0, "PLAY", (35, 52, 110))

    def destroy(self):
        pass


class GameState(AppState):
    def __init__(self, is_find):
        super().__init__()
        self._is_mode = is_find
        self._board_speed = 60
        self._board = pygame.Rect(450, 650, 300, 20)
        self._ball_radius = 20
        self._ball_speed = 3
        self._ball_rect = int(self._ball_radius * 2 ** 0.5)
        self._ball = pygame.Rect(randrange(self._ball_rect, WIDTH - self._ball_rect),
                                 400, self._ball_rect, self._ball_rect)
        self._dx, self._dy = 1, -1
        self._block_list = [pygame.Rect(10 + 120 * i, 10 + 70 * j, 100, 50) for i in range(10) for j in range(4)]
        self._is_draw_list = [randrange(0, 2) for _ in self._block_list]

    def detect_collision(self, dx, dy, ball, rect):
        if dx > 0:
            delta_x = ball.right - rect.left
        else:
            delta_x = rect.right - ball.left
        if dy > 0:
            delta_y = ball.bottom - rect.top
        else:
            delta_y = rect.bottom - ball.top
        if abs(delta_x - delta_y) < 10:
            dx, dy = -dx, -dy
        elif delta_x > delta_y:
            dy = -dy
        elif delta_y > delta_x:
            dx = -dx
        return dx, dy

    def setup(self):
        pass

    def process_event(self, event):
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT] and self._board.left > 0:
            self._board.left -= self._board_speed
        if key[pygame.K_RIGHT] and self._board.right < WIDTH:
            self._board.right += self._board_speed
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.get_app().set_state(MenuState('background'))

    def loop(self, dt):
        self.get_app().get_screen().fill((35, 52, 110))
        screen = self.get_app().get_screen()
        if self._is_mode:
            for i in range(len(self._block_list)):
                if self._is_draw_list[i]:
                    pygame.draw.rect(screen, (66, 170, 255), self._block_list[i])
        else:
            for i in range(len(self._block_list)):
                pygame.draw.rect(screen, (66, 170, 255), self._block_list[i])
        pygame.draw.rect(screen, pygame.Color((255, 255, 255)), self._board)
        pygame.draw.circle(screen, pygame.Color((255, 255, 255)), self._ball.center, self._ball_radius)
        self._ball.x += self._ball_speed * self._dx
        self._ball.y += self._ball_speed * self._dy
        if self._ball.centerx < self._ball_radius or self._ball.centerx > WIDTH - self._ball_radius:
            self._dx = -self._dx
        if self._ball.centery < self._ball_radius:
            self._dy = -self._dy
        if self._ball.colliderect(self._board) and self._dy > 0:
            self._dx, self._dy = self.detect_collision(self._dx, self._dy, self._ball, self._board)
        hit_index = self._ball.collidelist(self._block_list)
        if hit_index != -1:
            hit_rect = self._block_list.pop(hit_index)
            self._dx, self._dy = self.detect_collision(self._dx, self._dy, self._ball, hit_rect)
            hit_rect.inflate_ip(self._ball.width * 3, self._ball.height * 3)
            pygame.draw.rect(screen, (255, 0, 5), hit_rect)
        if self._ball.bottom > HEIGHT:
            pass
        elif not len(self._block_list):
            pass

    def destroy(self):
        pass


def _return_znach(key=('name',)):
    result = CUR.execute(f"""SELECT {key[0]} FROM players
                            WHERE number_of_play=(SELECT MAX(number_of_play) 
                            FROM players)""").fetchone()
    return result


class Button:
    def do(self, surface, color, x, y, length, height, width, text, text_color):
        self.draw_button(surface, color, length, height, x, y, width)
        self.write_text(surface, text, text_color, length, height, x, y)
        self._rect = pygame.Rect(x, y, length, height)

    def write_text(self, surface, text, text_color, length, height, x, y):
        font_size = int((length - 100) // len(text))
        myFont = pygame.font.SysFont("Calibri", font_size)
        myText = myFont.render(text, True, text_color)
        surface.blit(myText, ((x + length / 2) - myText.get_width() / 2, (y + height / 2) - myText.get_height() / 2))

    def draw_button(self, surface, color, length, height, x, y, width):
        for i in range(1, 10):
            s = pygame.Surface((length + (i * 2), height + (i * 2)))
            s.fill(color)
            surface.blit(s, (x - i, y - i))
        pygame.draw.rect(surface, color, (x, y, length, height), width)

    def pressed(self, mouse):
        if mouse[0] > self._rect.topleft[0]:
            if mouse[1] > self._rect.topleft[1]:
                if mouse[0] < self._rect.bottomright[0]:
                    if mouse[1] < self._rect.bottomright[1]:
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:
            return False


class InputBox:
    def __init__(self, x, y, length, height, color_act, color_pass, text='', is_click=True):
        self._font = pygame.font.SysFont("Calibri", 30)
        self._color_act = pygame.Color(color_act)
        self._color_pass = pygame.Color(color_pass)
        self._rect = pygame.Rect(x, y, length, height)
        self._color_now = self._color_pass
        self._text = text
        self._txt_surface = self._font.render(text, True, self._color_now)
        self._is_active = False
        self._is_click = is_click
        self._worki = AppState()

    def press(self, event):
        if self._is_click:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self._rect.collidepoint(event.pos):
                    self._is_active = not self._is_active
                else:
                    self._is_active = False
                self._color_now = self._color_act if self._is_active else self._color_act
            if event.type == pygame.KEYDOWN:
                if self._is_active:
                    if event.key == pygame.K_RETURN:
                        self.ret_total()
                        CUR.execute("""INSERT INTO players(name, score) VALUES(?, ?);""", self._total)
                        CON.commit()
                        self._text = ''
                    elif event.key == pygame.K_BACKSPACE:
                        self._text = self._text[:-1]
                    else:
                        self._text += event.unicode
                        self.update()
                    self._txt_surface = self._font.render(self._text, True, self._color_now)
        else:
            self._txt_surface = self._font.render(self._text, True, self._color_now)

    def ret_total(self):
        if self._text:
            self._total = (self._text, 0)
        else:
            self._total = ('StarKiller', 0)
        return self._total

    def update(self):
        width = max(200, self._txt_surface.get_width() + 30)
        self._rect.w = width

    def draw(self, screen):
        screen.blit(self._txt_surface, (self._rect.x + 10, self._rect.y + 10))
        pygame.draw.rect(screen, self._color_now, self._rect, 7)


def load_image(image_path, colorkey=None):
    result = pygame.image.load(image_path)
    if colorkey is not None:
        if colorkey == -1:
            colorkey = result.get_at((0, 0))
        result.set_colorkey(colorkey)
    else:
        result.convert_alpha()
    return result


if __name__ == '__main__':
    app = App()

    imgs = {'background': load_image('background.png'),
            'recbackground': load_image('recback.png')}

    menu_state = MenuState('background')
    app.set_state(menu_state)
    app.run()
