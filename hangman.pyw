import itertools
import os
import random
import sqlite3
import string
from typing import (Callable,
                    Tuple,
                    Union,
                    Dict,
                    Optional,
                    Iterable,
                    NoReturn)

import CustomizeDatabase
import pandas
import pygame

__all__ = ["Word", "Player",
           "Window", "Button", "Text", "Image", "EntryBox", "HomePage",
           "InfoWindow", "InstructionsPage", "LoginPage",
           "LevelsPage", "GamePage", "ScoreBoardPage", "FinishLevelPage",
           "LeaderboardPage"]
__authors__ = ["Tom Ben-Dor <tombendor.school@gmail.com>",
               "Asif Solomon <asifsolomon@gmail.com>",
               "Amit Roth <roth.amit@gmail.com>"]
__version__ = "5.0.0"
__credits__ = ["Beit Ekstein", "Safari Ramat Gan"]

pygame.init()

colors = {"green": (183, 222, 210),
          "red": (246, 166, 178),
          "orange": (247, 194, 151),
          "yellow": (255, 236, 184),
          "blue": (144, 210, 216)}

number_of_clues = {1: 3, 2: 2, 3: 1, 4: 2}

con = sqlite3.connect("files/db/database.db")

words = {1: set(), 2: set(), 3: set(), 4: set()}


def login_required(window: type):
    if not issubclass(window, Window):
        raise TypeError(f"{window.__name__} must be subclass of Window.")

    class WrapperWindow(window):
        def open(self) -> NoReturn:
            if player.name == "<Anonymous>":
                LoginPage().open()

            super().open()

    return WrapperWindow


class Word:
    """
    Class representing a Word object.
    Every word has level, discover and file_name attributes.
    """

    def __init__(self, *,
                 word: str,
                 level: int,
                 discover: Union[bool, int],
                 file_name: Optional[str],
                 priority: int):
        """
        :param word: the word as string.
        :param level: level of the word (1 - 4).
        :param discover: boolean value representing
                         whether the word has discover image.
        :param file_name: if discover=True,
                          the file name in path: files/animals/.
        :param priority: rank the user results with this word in previous games
                         for future game.
        """
        self.word = word
        self.level = level
        self.discover = bool(discover)
        self.file_name = file_name
        self.priority = priority

    def __str__(self) -> str:
        return self.word

    def __repr__(self) -> str:
        return f"Word(word='{self.word}', level={self.level})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Word):
            return NotImplemented
        return other.word == self.word

    def __hash__(self) -> int:
        return hash(self.word)


class Player:
    def __init__(self, name):
        self.name = name
        self._score = 0

    @property
    def score(self) -> int:
        return self._score

    @score.setter
    def score(self, value: int) -> None:
        self._score = value
        self.save_score()

    def save_score(self) -> None:
        sql = f"SELECT Score FROM tblLeaders WHERE Name='{self.name}'"

        matching_players = pandas.read_sql_query(sql, con)
        if not matching_players.empty:
            score = max(matching_players["Score"][0], self.score)
            sql = f"UPDATE tblLeaders SET Score={score} WHERE Name='{self.name}'"
        else:
            score = self.score
            sql = f"INSERT INTO tblLeaders VALUES ('{self.name}', {score})"

        con.execute(sql)
        con.commit()


player = Player("<Anonymous>")


class Window:
    """
    Parent for all Pages.
    """
    _clock = pygame.time.Clock()

    configuration = {"height": 700,
                     "width": 1000,
                     "font": "comicsansms",
                     "background color": colors['yellow'],
                     "title": "Safari - Hangman",
                     "mode": pygame.RESIZABLE}
    title = ""

    def __init__(self):
        self._buttons = []

    def __init_subclass__(cls, title=''):
        cls.title = title

    @property
    def buttons(self) -> Iterable:
        return self._buttons

    @buttons.setter
    def buttons(self, buttons: Iterable) -> None:
        if not all(isinstance(button, Button) for button in buttons):
            raise TypeError(f"All buttons must be instances of Button."
                            f"\n\t\t   Buttons:\n\t\t   {buttons}")

        self._buttons = buttons

    def _draw_buttons(self) -> None:
        for button in self.buttons:
            button.draw(self.screen)

    def config_button(self, *texts: str, **kwargs) -> None:
        """
        Update button's attributes.

        :param texts: options for the button's text.
        :param kwargs: attributes to change.
        :return: None.
        :raises: ValueError if button wasn't found.
        """
        for button in self.buttons:
            if button.text in texts:
                button.__dict__.update(**kwargs)
                break
        else:
            raise ValueError(f"Couldn't find any button to config"
                             f" from the list: {list(texts)}."
                             f"\n\t\t\tButtons available:"
                             f"\n\t\t\t{self.buttons}")

    def _create_window(self) -> None:
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT),
                                              self.configuration['mode'])
        self.screen.fill(self.configuration['background color'])
        pygame.display.set_caption(self.configuration['title'])
        Text(text=self.title,
             font=(self.configuration['font'], WIDTH // 18),
             rect=(0, 0, WIDTH, 200)).draw(self.screen)
        Image(path=f"files/logos/logo.png",
              pos=(15, 50),
              scale=HEIGHT).draw(self.screen)

    def _mainloop(self) -> NoReturn:
        """
        Update the surface and handle events.
        """
        while self.running:
            for event in pygame.event.get():
                self._handle_event(event)
            self._draw_buttons()
            pygame.display.update()
            self._clock.tick(30)

    def _handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.close(kill=True)
        elif event.type == pygame.VIDEORESIZE:
            global WIDTH, HEIGHT
            WIDTH, HEIGHT = event.size
            WIDTH, HEIGHT = max(WIDTH, 1000), max(HEIGHT, 700)
            self._create_window()

    def open(self) -> NoReturn:
        self.running = True
        self._create_window()
        self._mainloop()

    def close(self, *, kill=False) -> NoReturn:
        self.running = False
        if kill:
            con.close()  # Closing Sqlite connection.
            raise SystemExit

    def goto_window(self, window) -> NoReturn:
        if not isinstance(window, Window):
            raise TypeError(f"{window} is not instance of Window!")

        self.close()
        window.open()


WIDTH, HEIGHT = Window.configuration['width'], Window.configuration['height']


class Button:
    """
    Class for creating buttons in pygame.
    """

    configuration = {"normal": colors['orange'],
                     "disabled": colors['red'],
                     "active": colors['blue']}

    def __init__(self, *,
                 text: str,
                 font: Tuple[str, int],
                 size: Tuple[int, int],
                 color: Tuple[int, int, int],
                 active: Tuple[int, int, int],
                 pos: Tuple[int, int],
                 command: Callable[[], None]):
        """
        :param text: the label of the button.
        :param font: font & font size.
        :param size: the size of the rect object.
        :param color: color of the button.
        :param active: color when button is clicked.
        :param pos: position of the rect object.
        :param command: the command that will be executed
                        when button is clicked.
        """
        self.text = text
        self.font = font
        self.size = size
        self.color = color
        self.active = active
        self.pos = pos
        self.command = command

    def draw(self, screen: pygame.Surface) -> None:
        """
        :param screen: the parent of the button.
        :return: None
        """
        x, y = self.pos
        w, h = self.size
        r, g, b = self.color

        mouse = pygame.mouse.get_pos()
        if x < mouse[0] < x + w and y < mouse[1] < y + h:
            pygame.draw.rect(screen,
                             (min(r + 10, 255),
                              min(g + 10, 255),
                              min(b + 10, 255)),
                             (x, y, w, h))
            event = pygame.event.wait()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pygame.draw.rect(screen, self.active, (x, y, w, h))
                    self.command()
        else:
            pygame.draw.rect(screen, self.color, (x, y, w, h))

        Text(text=self.text, font=self.font, rect=(x, y, w, h)).draw(screen)

    @classmethod
    def from_menubutton(cls, text: str, loc: str, command: Callable[[], None]):
        """
        Create a button object with all given parameters.

        :rtype: Button.
        """
        locations = {"left": (WIDTH // 15, (HEIGHT * 5) // 6),
                     "middle-left": ((WIDTH * 3) // 10, (HEIGHT * 5) // 6),
                     "middle-right": ((WIDTH * 8) // 15, (HEIGHT * 5) // 6),
                     "right": ((WIDTH * 23) // 30, (HEIGHT * 5) // 6)}

        try:
            options = {"text": text,
                       "font": (Window.configuration['font'], WIDTH // 40),
                       "size": (WIDTH // 6, HEIGHT // 15),
                       "color": Button.configuration['normal'],
                       "active": Button.configuration['active'],
                       "pos": locations[loc],
                       "command": command}
        except KeyError as e:
            raise ValueError(f"Location must be 'left', 'middle-left',"
                             f" 'middle-right' or 'right'. Not '{loc}'.") \
                from e
        else:
            return cls(**options)

    def __repr__(self) -> str:
        return f"Button('{self.text}')"


class Text:
    """
    Class for creating text in pygame.
    The text will display at the center of the rect object.
    """

    def __init__(self, *,
                 text: str,
                 font: Tuple[str, int],
                 rect: Tuple[int, int, int, int],
                 color: Tuple[int, int, int] = (0, 0, 0),
                 bg: Tuple[int, int, int] = None):
        """
        :param text: text.
        :param font: font & font size.
        :param rect: the rectangle that the text will be centered into.
                     (xpos, ypos, width, height).
        :param color: color of the text.
        :param bg: background color.
        """
        self.text = text
        self.font = font
        self.rect = rect
        self.color = color
        self.bg = bg

    def draw(self, screen: pygame.Surface) -> None:
        """
        :param screen: the parent of the text.
        :return: None
        """
        font = pygame.font.SysFont(*self.font)
        text = font.render(self.text, True, self.color, self.bg)
        width, height = text.get_size()
        x, y, w, h = self.rect
        screen.blit(text, (x + (w - width) // 2, y + (h - height) // 2))

    def __repr__(self) -> str:
        return f"Text('{self.text}')"


class Image:
    """
    Class for creating image in pygame.
    The image's scale will be automatically changed.
    """

    def __init__(self, *,
                 path: str,
                 pos: Union[Tuple[int, int], str],
                 scale: int = 700):
        """
        :param path: path of the image.
        :param pos: the position of the image (can be "CENTER").
        :param scale: height of the window
                      that fits for the current image size.
        """
        self.path = path
        self.pos = pos
        self.scale = scale

    def draw(self, screen: pygame.Surface) -> None:
        """
        :param screen: the parent of the text.
        :return: None
        """
        img = pygame.image.load(self.path)
        w, h = img.get_size()
        width = int(HEIGHT / (self.scale / h) * w / h)
        height = int(HEIGHT / (self.scale / h))
        img = pygame.transform.scale(img, (width, height))
        if self.pos == "CENTER":
            self.pos = ((WIDTH - width) // 2, (HEIGHT - height) // 2)
        screen.blit(img, self.pos)

    def __repr__(self) -> str:
        return f"Image('{self.path}')"


class EntryBox:
    def __init__(self, *,
                 rect: Tuple[int, int, int, int],
                 font: Tuple[str, int],
                 color: Tuple[int, int, int],
                 chars_limit: int):
        self.rect = rect
        self.font = font
        self.color = color
        self.chars_limit = chars_limit

        self.text = ""

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, self.color, self.rect)
        Text(text=self.text + "|", font=self.font, rect=self.rect).draw(screen)

    def insert(self, letter: str) -> None:
        if letter == ' ':
            if self.text == "" or self.text[-1] == ' ':
                return
        if len(self.text) >= self.chars_limit:
            return

        self.text = (self.text + letter).title()

    def delete(self) -> None:
        self.text = self.text[:-1]


class HomePage(Window, title="Hangman"):
    """
    Home page window. Subclass of Window class.
    """

    def _create_window(self) -> None:
        super()._create_window()

        self.buttons = [
            Button.from_menubutton("Instructions", "middle-right",
                                   lambda: self.goto_window(InstructionsPage)),
            Button.from_menubutton("Play", "left",
                                   lambda: self.goto_window(LevelsPage())),
            Button.from_menubutton("Leaderboard", "middle-left",
                                   lambda: self.goto_window(
                                       LeaderboardPage())),
            Button(text="Exit",
                   font=(Window.configuration['font'], WIDTH // 50),
                   size=(WIDTH // 12, HEIGHT // 24),
                   color=Button.configuration['normal'],
                   active=Button.configuration['active'],
                   pos=((WIDTH * 11) // 12 - 25, (HEIGHT * 23) // 24 - 25),
                   command=lambda: self.close(kill=True)),
        ]

        Image(path=f"files/pics/animals.jpg",
              pos="CENTER",
              scale=2500).draw(self.screen)


class InfoWindow(Window):
    """
    Parent class for About & Instructions. Subclass of Window class.
    """
    langs = ['English', 'Hebrew']

    def __init__(self, *,
                 title: str,
                 mp3_files: Dict[str, str],
                 png_files: Dict[str, str]):
        """
        :param title: the title of the page.
        :param mp3_files: mp3 files.
        :param png_files: png files.
        """
        self.title = title
        self.mp3_files = mp3_files
        self.png_files = png_files

        self.lang = self.langs[0]
        self.langs_order = itertools.cycle(self.langs[1:] + self.langs[:1])
        self.next_lang = next(self.langs_order)

        self.playing_sound = False

        super().__init__()

    def _create_window(self) -> None:
        super()._create_window()

        self.buttons = [
            Button.from_menubutton("Back", "right",
                                   lambda: self.goto_window(HomePage())),
            Button.from_menubutton("Listen", "left",
                                   self.toggle_sound),
            Button.from_menubutton(self.next_lang, "middle-left",
                                   self.toggle_lang),
        ]

        self.translate()

    def toggle_lang(self) -> None:
        self.lang = self.next_lang
        self.next_lang = next(self.langs_order)
        self.translate()

    def translate(self) -> None:
        """
        Set page to current lang.
        """
        self.config_button("Listen", "Stop",
                           command=self.toggle_sound
                           if self.lang in self.mp3_files.keys()
                           else lambda: None,
                           color=Button.configuration['normal']
                           if self.lang in self.mp3_files.keys()
                           else Button.configuration['disabled'],
                           active=Button.configuration['active']
                           if self.lang in self.mp3_files.keys()
                           else Button.configuration['disabled'])
        self.config_button(*self.langs,
                           text=self.next_lang)
        Image(path=f"files/pics/{self.png_files[self.lang]}",
              pos="CENTER", scale=1200).draw(self.screen)

    def toggle_sound(self) -> None:
        """
        By clicking the "Listen" button, the text will be read.
        """
        if self.playing_sound:
            pygame.mixer.music.stop()
            self.config_button("Listen", "Stop",
                               text="Listen")
            self.config_button(*self.langs,
                               color=Button.configuration['normal'],
                               active=Button.configuration['active'],
                               command=self.toggle_lang)
        else:
            pygame.mixer.music.load(f"files/mp3/{self.mp3_files[self.lang]}")
            pygame.mixer.music.play()
            self.config_button("Listen", "Stop",
                               text="Stop")
            self.config_button(*self.langs,
                               color=Button.configuration['disabled'],
                               active=Button.configuration['disabled'],
                               command=lambda: None)

        self.playing_sound = not self.playing_sound

    def close(self, *, kill=False) -> NoReturn:
        if self.playing_sound:
            pygame.mixer.music.stop()

        super().close(kill=kill)

    @classmethod
    def from_title(cls, title: str):
        """
        :param title: title of the window.
        :return: new InfoWindow instance based on the title.
        :rtype: InfoWindow
        """
        return cls(title=title.title(),
                   mp3_files={"English": f"{title}.mp3"},
                   png_files={"English": f"english_{title}.png",
                              "Hebrew": f"hebrew_{title}.png"})


InstructionsPage = InfoWindow.from_title('instructions')


class LoginPage(Window, title="Insert name"):
    """
    Window for getting the user's name for the leaders board.
    """

    def __init__(self):
        super().__init__()

        self.entry_box = EntryBox(
            rect=(WIDTH // 4, HEIGHT // 2, WIDTH // 2, HEIGHT // 9),
            font=(Window.configuration['font'], WIDTH // 30),
            color=colors['blue'],
            chars_limit=20)

    def _create_window(self) -> None:
        super()._create_window()

        self.buttons = [
            Button.from_menubutton("Back", "right",
                                   lambda: self.goto_window(HomePage())),
            Button.from_menubutton("Submit", "left", self.submit)
        ]

        self.entry_box.rect = (WIDTH // 4,
                               HEIGHT // 2,
                               WIDTH // 2,
                               HEIGHT // 9)
        self.entry_box.font = (Window.configuration['font'], WIDTH // 30)
        self.entry_box.draw(self.screen)

        if len(self.entry_box.text.strip()) >= 3:
            self.config_button("Submit",
                               color=Button.configuration['normal'],
                               active=Button.configuration['active'],
                               command=self.submit)
        else:
            self.config_button("Submit",
                               color=Button.configuration['disabled'],
                               active=Button.configuration['disabled'],
                               command=lambda: None)

    def _handle_event(self, event: pygame.event.Event) -> None:
        super()._handle_event(event)

        if event.type == pygame.KEYDOWN:
            letter = chr(event.key)
            if letter in string.ascii_letters + ' ':
                self.entry_box.insert(letter)
            elif event.key == pygame.K_BACKSPACE:
                self.entry_box.delete()

            self._create_window()

    def submit(self) -> None:
        global player
        player = Player(self.entry_box.text.strip())
        self.close()


class LevelsPage(Window, title="Choose level"):
    """
    Window for choosing a level. Subclass of InfoWindow class.
    """

    def _create_window(self) -> None:
        super()._create_window()

        buttons = [
            Button.from_menubutton("Back", "right",
                                   lambda: self.goto_window(HomePage())),
            Button.from_menubutton("Customize", "left", self.customize),
        ]

        for level, text in enumerate(["1", "2", "3", "+"], start=1):
            def func(level_=level):
                # It's necessary to built a function.
                # See Python late binding.
                self.goto_window(GamePage(words[level_].pop()))

            size = HEIGHT // 6
            button = {"text": text,
                      "font": (Window.configuration['font'], WIDTH // 20),
                      "size": (size, size),
                      "color": Button.configuration[
                          'normal' if words[level] else 'disabled'],
                      "active": Button.configuration[
                          'active' if words[level] else 'disabled'],
                      "pos": ((WIDTH - size * 7) // 2 + size * 2 * (level - 1),
                              HEIGHT // 2 - size // 2),
                      "command": func if words[level] else lambda: None}
            buttons.append(Button(**button))

        self.buttons = buttons

    def customize(self) -> None:
        """
        Customize the words of level 4 within the customize window.
        """
        self.configuration['mode'] = 0
        self._create_window()

        try:
            CustomizeDatabase.customize()
        except SystemExit:
            global words
            words[4].clear()
            sql = "SELECT * FROM tblWords WHERE Level=4"
            update_words(sql)

        self.configuration['mode'] = pygame.RESIZABLE
        self._create_window()
        self._draw_buttons()


@login_required
class GamePage(Window):
    """
    Main game window. Subclass of Window class.
    """
    sound_mode = True

    def __init__(self, word: Word):
        """
        :param word: a Word() object.
        """
        self.word = word
        self.clues = min(number_of_clues.get(self.word.level, 0),
                         len(str(self.word)) // 4)
        self.guessed = []
        self.attempts = 0
        self.title = f"Level #{word.level}"

        super().__init__()

    def _create_window(self) -> None:
        super()._create_window()

        buttons = [
            Button.from_menubutton("Clue", "left", self.get_clue),
            Button.from_menubutton("Back", "right",
                                   lambda: self.goto_window(LevelsPage())),
            Button.from_menubutton("Skip", "middle-left",
                                   lambda: self.game_over("lost")),
            Button(text="",
                   font=(Window.configuration['font'], WIDTH // 50),
                   size=(
                       int(HEIGHT / (2000 / 130)), int(HEIGHT / (2000 / 130))),
                   color=Window.configuration['background color'],
                   active=Button.configuration['active'],
                   pos=((WIDTH * 11) // 12 + 25, (HEIGHT * 23) // 24 - 25),
                   command=lambda: self.toggle_sound_button()),
        ]

        for i, letter in enumerate(string.ascii_uppercase):
            keyboard_size = HEIGHT // 18
            y = int(HEIGHT // 2 + (i // 6) * (keyboard_size + 5))
            x = int(0.625 * WIDTH + (i % 6) * (keyboard_size + 5))

            def guess(letter_=letter):
                self.guess_letter(letter_)

            button = {"text": letter,
                      "font": (
                          Window.configuration['font'],
                          int(keyboard_size // 2.5)),
                      "size": (keyboard_size, keyboard_size),
                      "color": Button.configuration['normal'],
                      "active": colors['green' if letter in str(
                          self.word).upper() else 'red'],
                      "pos": (x, y),
                      "command": guess}

            buttons.append(Button(**button))

        self.buttons = buttons

        for letter in self.guessed:
            self.config_button(letter,
                               color=colors['green' if letter in str(
                                   self.word).upper() else 'red'],
                               command=lambda: None)

        if not self.clues:
            self.config_button("Clue",
                               color=Button.configuration['disabled'],
                               active=Button.configuration['disabled'],
                               command=lambda: None)

        Text(
            text=f"Guess the {'animal' if self.word.level != 4 else 'word'}" +
                 f" below:",
            font=(Window.configuration['font'], WIDTH // 30),
            rect=(0, 0, WIDTH, HEIGHT // 2)).draw(self.screen)

        self._draw_buttons()
        self.draw_underlines()
        self.draw_hangman()

    def _draw_buttons(self) -> None:
        super()._draw_buttons()

        if self.sound_mode:
            img_path = f"files/pics/unmuteButton.png"
        else:
            img_path = f"files/pics/muteButton.png"

        Image(path=img_path,
              pos=((WIDTH * 11) // 12 + 25, (HEIGHT * 23) // 24 - 25),
              scale=2000).draw(self.screen)

    def _handle_event(self, event) -> None:
        super()._handle_event(event)

        if event.type == pygame.KEYDOWN:
            letter = chr(event.key).upper()
            if letter not in self.guessed and letter in string.ascii_uppercase:
                self.guess_letter(letter)

    def draw_underlines(self) -> None:
        underlines = []
        for letter in str(self.word):
            if (letter.upper() in self.guessed or
                    letter not in string.ascii_letters):
                underlines.append(letter)
                continue
            underlines.append("_")
        Text(text=' '.join(underlines),
             font=(Window.configuration['font'], WIDTH // 20),
             rect=(0, 0, WIDTH, (HEIGHT * 2) // 3)).draw(self.screen)
        if "_" not in underlines:
            self.game_over("won")

    def draw_hangman(self) -> None:
        if self.attempts:
            Image(path=f"files/stages/{7 - self.attempts}.png",
                  pos=(WIDTH // 3 - 100, HEIGHT // 2 - 50)).draw(self.screen)

    def guess_letter(self, letter: str) -> None:
        self.guessed.append(letter)
        self._create_window()
        if letter not in str(self.word).upper():
            self.attempts += 1
            if self.attempts == 7:
                self.game_over("lost")
        self.draw_hangman()

    def get_clue(self) -> None:
        letters = set(str(self.word).upper()).difference(
            self.guessed).intersection(string.ascii_uppercase)
        letter = random.choice(list(letters))
        self.guess_letter(letter)
        self.clues -= 1
        self._create_window()

    def toggle_sound_button(self) -> None:
        GamePage.sound_mode = not self.sound_mode

    @property
    def learned(self) -> bool:
        """
        :return: Whether the user has learned the word properly.
        :rtype: bool
        """

        if self.word.level == 4:
            return True
        used_clues = min(number_of_clues.get(self.word.level, 0),
                         len(str(self.word)) // 4) - self.clues
        if self.attempts > 6:
            return False
        if (((used_clues == 3) and (self.attempts > 2)) or
                ((used_clues == 2) and (self.attempts > 3)) or
                ((used_clues == 1) and (self.attempts > 4) or
                 ((used_clues == 0) and (self.attempts > 5)))):
            return False
        return True

    def game_over(self, state: str) -> NoReturn:
        """
        This function counts the successes and fails.
        At the end of a game - the result will be added to the counter.
        It also changes the priority or the word.
        """
        self.word.state = state
        if state == "won":
            if self.sound_mode:
                pygame.mixer.music.load(f"files/mp3/win.mp3")
                pygame.mixer.music.play()

            if self.learned:
                self.word.priority -= 1
            player.score += self.word.level if self.word.level != 4 else 1
        if self.word.priority and self.word.level == 4:
            global words
            words[self.word.level].add(self.word)
        self.goto_window(ScoreBoardPage(self.word))


class ScoreBoardPage(Window, title="Score Board"):
    """
    Score board window. Subclass of Window class.
    """

    def __init__(self, word: Word):
        """
        :param word: a Word() object.
        """
        self.word = word

        super().__init__()

    def _create_window(self) -> None:
        super()._create_window()

        buttons = [
            Button.from_menubutton("Back", "right",
                                   lambda: self.goto_window(LevelsPage())),
            Button.from_menubutton("Next", "middle-left",
                                   lambda: self.goto_window(
                                       GamePage(
                                           words[self.word.level].pop()))),
        ]
        if self.word.discover:
            buttons.append(
                Button.from_menubutton("Discover", "left", self.discover))
        self.buttons = buttons

        if not len(words[self.word.level]):
            self.config_button("Next",
                               command=lambda: self.goto_window(
                                   FinishLevelPage(self.word.level)))

        Text(text=f"You {self.word.state}!",
             font=(Window.configuration['font'], WIDTH // 10),
             rect=(0, 0, WIDTH, (HEIGHT * 2) // 3)).draw(self.screen)
        Text(
            text=f"The {'animal' if self.word.level != 4 else 'word'}"
                 f" was: {self.word}",
            font=(Window.configuration['font'], WIDTH // 20),
            rect=(0, 0, WIDTH, HEIGHT)).draw(self.screen)
        Text(text=f"Your score is {player.score}",
             font=(Window.configuration['font'], WIDTH // 30),
             rect=(0, HEIGHT // 2, WIDTH, HEIGHT // 2)).draw(self.screen)

    def discover(self) -> None:
        img_path = os.path.abspath(
            f"files/animals/{self.word.file_name}")
        os.startfile(img_path)


class FinishLevelPage(Window, title="Level Completed"):
    """
    Finish level window. Subclass of Window class.
    """

    def __init__(self, level):
        self.level = level

        super().__init__()

    def _create_window(self) -> None:
        super()._create_window()

        self.buttons = [
            Button.from_menubutton("Back", "right",
                                   lambda: self.goto_window(LevelsPage())),
        ]

        Text(text=f"You finished level {self.level}!",
             font=(Window.configuration['font'], WIDTH // 10),
             rect=(0, 0, WIDTH, HEIGHT)).draw(self.screen)


class LeaderboardPage(Window, title="Leaderboard"):
    def __init__(self):
        super().__init__()

        sql = "SELECT * FROM tblLeaders ORDER BY Score DESC LIMIT 5"
        self.top_scores = pandas.read_sql_query(sql, con).to_dict("records")

    def _create_window(self) -> None:
        super()._create_window()

        self.buttons = [
            Button.from_menubutton("Back", "right",
                                   lambda: self.goto_window(HomePage())),
        ]

        if len(self.top_scores) > 0:
            for n in range(1, len(self.top_scores) + 1):
                pygame.draw.rect(self.screen,
                                 colors['blue' if n % 2 else 'orange'],
                                 (WIDTH // 4 - 20, n * HEIGHT // 10 + 140,
                                  WIDTH // 2 + 100, HEIGHT // 12))
                Text(text=f"#{n}",
                     font=(Window.configuration['font'], WIDTH // 30),
                     rect=(WIDTH // 4, n * HEIGHT // 10 + 150, 50, 50)).draw(
                    self.screen)
                Text(text=f"{self.top_scores[n - 1]['Name']}",
                     font=(Window.configuration['font'], WIDTH // 30),
                     rect=(WIDTH // 2, n * HEIGHT // 10 + 150, 100, 50)).draw(
                    self.screen)
                Text(text=f"{self.top_scores[n - 1]['Score']}",
                     font=(Window.configuration['font'], WIDTH // 30),
                     rect=(
                         (WIDTH * 3) // 4, n * HEIGHT // 10 + 150, 50,
                         50)).draw(
                    self.screen)
        else:
            Text(text="The leaderboard is empty!",
                 font=(Window.configuration['font'], WIDTH // 15),
                 rect=(0, 0, WIDTH, HEIGHT)).draw(self.screen)
            Text(text="Start playing now!",
                 font=(Window.configuration['font'], WIDTH // 20),
                 rect=(0, HEIGHT // 2, WIDTH, HEIGHT // 2)).draw(self.screen)


def update_words(sql: str) -> None:
    """
    Read the words' information from the database.
    """
    global words
    for word in pandas.read_sql_query(sql, con).to_dict('records'):
        word = Word(word=word['Word'].title(),
                    level=word['Level'],
                    discover=word['Discover'],
                    file_name=word['FileName'],
                    priority=word['Priority'])
        words[word.level].add(word)


update_words("SELECT * FROM tblWords")


def main():
    HomePage().open()


if __name__ == '__main__':
    main()
