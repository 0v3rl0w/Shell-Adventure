#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import pygame

from typing import (
    Tuple,
    Dict
)
from string import ascii_lowercase

from game.mechanics.term.executor import execute_and_out
from game.mechanics.term.History import History


class Term:
    def __init__(self, username: str, host: str, size: Tuple[int, int], font: pygame.font.Font):
        self.surface = pygame.Surface(size)
        self.mono = font
        self.visualLine = []
        self.lineRect = None
        self.blinkRect = None
        self.fontSurface = None
        self.inInput = False
        self.promptVisual = True
        self.bash = True
        self.currentTyping = ""
        self.blinkX = 0
        self.custom = ""
        self.mouseCollide = False

        if not os.path.isdir(os.path.join(os.environ["HOME"], ".shelladv")):
            os.mkdir(os.path.join(os.environ["HOME"], ".shelladv"))

        if not os.path.isdir(
            os.path.join(
                os.path.join(os.environ["HOME"], ".shelladv"),
                username)
        ):

            os.mkdir(
                os.path.join(
                    os.path.join(os.environ["HOME"], ".shelladv"),
                    username)
            )

        self.history = History(
            os.path.join(
                os.path.join(os.environ["HOME"], ".shelladv"),
                username)
        )

        self.env = {
            "HOME": os.path.join(os.path.join(os.environ["HOME"], ".shelladv"), username),
            "PWD": os.path.join(os.path.join(os.environ["HOME"], ".shelladv"), username),
            "USER": username,
            "HOST": host,
            "LASTINPUT": ""
        }

        # os.chdir(self.env["HOME"])
        self.tick = time.time()
        self.updatePrompt()

    def resize(self, size: Tuple[int, int]):
        self.surface = pygame.Surface(size)

    def disable_prompt(self):
        self.promptVisual = False

    def enable_prompt(self):
        self.promptVisual = True

    def isprompt_enabled(self) -> bool:
        return self.promptVisual

    def disable_bash(self):
        self.bash = False

    def enable_bash(self):
        self.bash = True

    def set_mouse_collide(self, isCollide: bool):
        self.mouseCollide = isCollide

    def did_mouse_collide(self) -> bool:
        return self.mouseCollide

    def getInput(self):
        self.inInput = True

    def removeLine(self):
        self.visualLine = self.visualLine[:-1]

    def set_custom_prompt(self, string: str):
        self.custom = string

    def updatePrompt(self):
        if self.env["PWD"][:len(self.env["HOME"])] == self.env["HOME"]:
            path = f"~{self.env['PWD'].split(self.env['HOME'])[1]}"
        else:
            path = self.env["PWD"]

        self.prompt = f"{self.env['USER']}@{self.env['HOST']} {path}: $"

    def add_to_display(self, output: str):
        self.visualLine.append((self.prompt, f">{output}"))
        self.fontSurface = None
        self.blinkX = 0

    def clear(self):
        self.visualLine = []

    def get_env(self, key: str) -> str:
        return self.env[key]

    def set_env(self, var, value):
        self.env[var] = value
        self.blinkX = 0

    def draw(self):
        if len(self.visualLine) * 22 >= self.surface.get_size()[1] - 75:
            self.visualLine = self.visualLine[1:]

        for lineIndex, line in enumerate(self.visualLine):
            toshow = line[1][1:] if len(line[1]) > 1 and line[1][0] == '>' else f"{line[0]} {line[1]}"
            self.fontSurface = self.mono.render(
                    toshow,
                    True,
                    (255, 255, 255)
                )

            self.surface.blit(
                self.fontSurface,
                (0, lineIndex * 22)
            )

        self.lineRect = self.surface.blit(
            self.mono.render(
                f"{self.prompt if not self.custom else self.custom} {self.currentTyping}"
                if self.promptVisual else self.currentTyping,
                False,
                (255, 255, 255)
            ),
            (0, len(self.visualLine) * 22)

        )

    def keydown(self, keycode: int):
        if self.mouseCollide:
            keyName = pygame.key.name(keycode)
        else:
            keyName = ''

        if keyName[1:-1].isdigit():
            self.currentTyping += keyName[1:-1]

        if keyName == "[*]":
            print(self.blinkX)
        if keyName == "up":
            self.currentTyping = self.history.get_previous()
            self.blinkX = 0

        if keyName == "down":
            self.currentTyping = self.history.get_next()
            self.blinkX = 0

        if keyName == "<" and pygame.key.get_mods() & pygame.KMOD_SHIFT:
            self.currentTyping += '>'

        elif keyName == "&" and pygame.key.get_mods() & pygame.KMOD_MODE:
            self.currentTyping += '|'

        elif keyName == "[.]" or keyName == ';' and pygame.key.get_mods() & pygame.KMOD_SHIFT:
            self.currentTyping += '.'

        elif keyName == "[/]" or keyName == ':' and pygame.key.get_mods() & pygame.KMOD_SHIFT:
            self.currentTyping += '/'

        elif keyName == "-" and pygame.key.get_mods() & pygame.KMOD_SHIFT:
            self.currentTyping += '_'

        elif keyName == "[-]":
            self.currentTyping += '-'

        elif keyName == "backspace":
            self.currentTyping = self.currentTyping[:-1]
            self.blinkX = 0

        elif keyName == "return" or keyName == "enter":
            self.blinkX = 0
            if self.bash and not self.inInput:
                self.visualLine.append((self.prompt, self.currentTyping))
                self.history.append(self.currentTyping)
                execute_and_out(self.currentTyping, self)
            elif self.inInput:
                self.inInput = False
                self.env["LASTINPUT"] = self.currentTyping
            if self.custom:
                self.custom = ""
            self.currentTyping = ""

        elif keyName == "space":
            self.currentTyping += ' '

        elif keyName == "c" and pygame.key.get_mods() & pygame.KMOD_CTRL and self.bash:
            self.visualLine.append((self.prompt, self.currentTyping+"^C"))
            self.currentTyping = ""
            self.blinkX = 0

        elif keyName in ascii_lowercase and pygame.key.get_mods() & pygame.KMOD_SHIFT:
            self.currentTyping += keyName.upper()

        elif keyName in ascii_lowercase or keyName in ['&', '-', '=', '$', ';', '<', '\'', '\"', '(', ')', '!']:
            self.currentTyping += keyName

    def drawBlink(self):
        pygame.draw.rect(
            self.surface,
            (255, 255, 255),
            self.blinkRect
        )

    def update(self):
        self.blinkRect = pygame.Rect(0, 2 + len(self.visualLine) * 22, 12, 20)
        self.lineRect = None
        self.blinkX = 0
        self.surface.fill((0, 0, 0))
        self.draw()
        self.updatePrompt()
        if 0.3 < time.time() - self.tick < 0.8 and self.mouseCollide:
            while self.blinkRect is None or self.lineRect.colliderect(self.blinkRect):
                self.blinkRect = self.blinkRect.move(1, 0)

            self.drawBlink()
        if time.time() - self.tick > 0.8:
            self.tick = time.time()

    def get_surface(self) -> pygame.Surface:
        self.update()
        return self.surface
