from abc import abstractmethod
import pygame

HEIGHT, WIDTH = 800, 1200


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
            font = pygame.font.Font(None, 30)
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
        self._bg_img = imgs[background_image]

    def setup(self):
        pygame.display.set_caption('Arkanoid')
        self._bg_img = pygame.transform.scale(self._bg_img, (WIDTH, HEIGHT))

    def process_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._but_new_game.pressed(pygame.mouse.get_pos()):
                self.get_app().set_state(GameState())
            elif self._record_but.pressed(pygame.mouse.get_pos()):
                self.get_app().set_state(RecState('recbackground'))

    def loop(self, dt):
        screen = self.get_app().get_screen()
        screen.fill((0, 0, 0))
        screen.blit(self._bg_img, (0, 0))
        self._but_new_game.do(screen, (66, 170, 255), 500, 350, 200, 50, 0, "PLAY", (35, 52, 110))
        self._record_but.do(screen, (66, 170, 255), 500, 650, 200, 50, 0, "RECORDS", (35, 52, 110))
        font = pygame.font.Font(None, 30)

    def destroy(self):
        pass


class RecState(AppState):
    def __init__(self, background_image):
        super().__init__()
        self._bg_img = imgs[background_image]

    def setup(self):
        pass

    def process_event(self, event):
        pass

    def loop(self, dt):
        screen = self.get_app().get_screen()
        screen.fill((0, 0, 0))
        screen.blit(self._bg_img, (0, 0))

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
