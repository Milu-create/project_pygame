from abc import abstractmethod
import pygame
import sqlite3

HEIGHT, WIDTH = 800, 1200
CON = sqlite3.connect("players.db")
CUR = CON.cursor()


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

            dt = self._clock.tick()
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
                self.get_app().set_state(GameState())
            elif self._record_but.pressed(pygame.mouse.get_pos()):
                self.get_app().set_state(RecState('recbackground'))

    def loop(self, dt):
        screen = self.get_app().get_screen()
        screen.fill((0, 0, 0))
        screen.blit(self._bg_img, (0, 0))
        self._name.draw(screen)
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

    def __init__(self):
        super().__init__()

    def setup(self):
        pass

    def process_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.get_app().set_state(MenuState('background'))

    def loop(self, dt):
        self.get_app().get_screen().fill((255, 128, 0))

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
    def __init__(self, x, y, length, height, color_act, color_pass):
        self._font = pygame.font.SysFont("Calibri", 30)
        self._color_act = pygame.Color(color_act)
        self._color_pass = pygame.Color(color_pass)
        self._rect = pygame.Rect(x, y, length, height)
        self._color_now = self._color_pass
        self._text = ''
        self._txt_surface = self._font.render('', True, self._color_now)
        self._is_active = False

    def press(self, event):
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
