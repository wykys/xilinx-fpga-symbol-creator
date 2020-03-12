#!/usr/bin/env python3
# Creates a schematic FPGA symbol for Eeschema from the Xilinx text file pin description.
# wykys 2020

import re
from pathlib import Path


class PinType(object):
    INPUT = 'I'
    OUTPUT = 'O'
    BIDI = 'B'
    TRISTATE = 'T'
    PASSIVE = 'P'
    UNSPECIFIED = 'U'
    POWER_IN = 'W'
    POWER_OUT = 'w'
    OPEN_COLLECTOR = 'C'
    OPEN_EMITTER = 'E'
    NOT_CONNECTED = 'N'


class VerticalJustify(object):
    CENTER = 'C'
    BOTTOM = 'B'
    TOP = 'T'


class HorizontalJustify(object):
    CENTER = 'C'
    LEFT = 'L'
    RIGHT = 'R'


class Direction(object):
    HORIZONTAL = 0
    VERTICAL = 900


class PinOrientation(object):
    UP = 'U'
    DOWN = 'D'
    LEFT = 'L'
    RIGHT = 'R'


class Pin(object):
    def __init__(self, data: str):
        self.pin = ''
        self.name = ''
        self.type = ''
        self.bank = ''
        self.parse(data)

    def parse(self, data: str):
        # Pin, Pin Name, Memory Byte Group, Bank, VCCAUX Group,
        # Super Logic Region, I/O Type, No-Connect
        pattern = r'^([A-Z]\d+)\W+(\S+)\W+(\S+)\W+(\S+)\W+(\S+)\W+(\S+)\W+(\S+)\W+(\S+)$'
        m = re.match(pattern, data)
        if m:
            self.pin, self.name, _, self.bank, _, _, self.type, _ = m.groups()
            if 'VCC' in self.name or 'GND' in self.name:
                self.type = PinType.POWER_IN
            elif self.name == 'NC':
                self.type = PinType.NOT_CONNECTED
                self.type += ' N'  # invisible pin
            else:
                self.type = PinType.BIDI

    def is_empty(self):
        if self.pin == '' and self.name == '' and self.type == '' and self.bank == '':
            return True
        else:
            return False

    def __str__(self):
        return f'{"="*30}\nPin: {self.pin} Bank: {self.bank}\n{self.name} {self.type} {self.bank}'

    def __repr__(self):
        return self.__str__


def load(path: str) -> list:

    if not Path(path).is_file():
        return []

    with open(path, 'r') as fr:
        tmp = fr.readlines()

    data = []
    for line in tmp:
        line = line.strip()
        pin = Pin(line)
        if not pin.is_empty():
            data.append(pin)

    def pin_sort(pin: Pin) -> float:
        if pin.bank.isdigit():
            score = int(pin.bank)
        else:
            score = -1

        pattern = r'IO_L(\d+)([P|N])'
        m = re.match(pattern, pin.name)
        if m:
            tmp = m.groups()
            score += int(tmp[0]) / 1000
            score += 1e-4 if tmp[1] == 'N' else 0

        else:
            pattern = r'IO_(\d+)_'
            m = re.match(pattern, pin.name)
            if m:
                tmp = m.groups()
                score += int(tmp[0]) / 1000
            else:
                if pin.type == PinType.NOT_CONNECTED:
                    score += 10e6
                elif 'VCC' in pin.name:
                    score -= 10e6
                elif 'GND' in pin.name:
                    score -= 10e5

        return score

    for i in data:
        pin_sort(i)

    data = sorted(data, key=lambda pin: pin.name, reverse=False)
    return sorted(data, key=pin_sort, reverse=False)


def split_bank(data: list) -> dict:
    bank = {}
    for pin in pins:
        if pin.bank not in bank:
            bank[pin.bank] = []
        bank[pin.bank].append(pin)
    return bank


def draw_box(x1, y1, x2, y2, unit=0, convert=0):
    return f'S {int(x1)} {int(y1)} {int(x2)} {int(y2)} {unit} {convert} 10 f\n'


def draw_pin(
        pin,
        x,
        y,
        size,
        orientation=PinOrientation.RIGHT,
        unit=0,
        convert=0
):
    return f'X {pin.name} {pin.pin} {int(x)} {int(y)} {int(size)} {orientation} 50 50 {unit} {convert} {pin.type}\n'


def draw_text(
    text,
    x,
    y,
    size,
    italic=False,
    bold=False,
    hjustify=HorizontalJustify.CENTER,
    vjustify=VerticalJustify.CENTER,
    direction=Direction.HORIZONTAL,
    unit=0,
    convert=0
):
    italic = 'Italic' if italic else 'Normal'
    bold = 1 if bold else 0
    return f'T {direction} {int(x)} {int(y)} {int(size)} 0 {unit} {convert} "{text}" {italic} {bold} {hjustify} {vjustify}\n'


def make_symbol(pins: list, part: str, title: str) -> str:
    GRID_STEP = 100
    PIN_SIZE = GRID_STEP * 2
    WIDTH = GRID_STEP * 20

    banks = split_bank(pins)
    unit = 0
    tmp = []

    for bank, pin_list in banks.items():
        x = 0
        y = 0
        unit += 1

        # bank symbol
        if bank.isdigit():
            flag_bank_power = False
            vcc_count = len(list((p for p in banks[bank] if 'VCC' in p.name)))
            for pin in pin_list:
                if 'VCC' in pin.name:
                    orientation = PinOrientation.DOWN
                    if not flag_bank_power:
                        flag_bank_power = True
                        y += GRID_STEP * 3
                        x += WIDTH + PIN_SIZE - vcc_count * GRID_STEP
                    else:
                        x += GRID_STEP
                else:
                    if flag_bank_power:
                        flag_bank_power = False
                        x = 0
                        y = 0
                    orientation = PinOrientation.RIGHT

                tmp.append(
                    draw_pin(pin, x, y, PIN_SIZE, orientation, unit=unit)
                )

                if not flag_bank_power:
                    y -= GRID_STEP

            tmp.append(
                draw_box(
                    PIN_SIZE,
                    GRID_STEP,
                    x + WIDTH + PIN_SIZE,
                    y,
                    unit=unit
                )
            )

            tmp.append(
                draw_text(
                    title,
                    PIN_SIZE + WIDTH - GRID_STEP,
                    - GRID_STEP * 4,
                    GRID_STEP,
                    bold=True,
                    hjustify=HorizontalJustify.RIGHT,
                    unit=unit
                )
            )

            tmp.append(
                draw_text(
                    f'BANK {bank}',
                    PIN_SIZE + WIDTH - GRID_STEP,
                    -GRID_STEP * 6,
                    GRID_STEP / 2,
                    bold=True,
                    hjustify=HorizontalJustify.RIGHT,
                    unit=unit
                )
            )

        # power symbol
        else:
            vcc_database = set(
                list(p.name for p in pin_list if 'VCC' in p.name)
            )
            power_name = ''
            power_name_cnt = 0
            orientation = PinOrientation.RIGHT

            x = 0
            y += GRID_STEP

            flag_orientation = True
            for pin in pin_list:
                if pin.name in vcc_database:
                    if pin.name != power_name:
                        power_name = pin.name
                        power_name_cnt += 1
                        y -= GRID_STEP
                        if flag_orientation and power_name_cnt > (
                                len(vcc_database) / 2 + 1):
                            flag_orientation = False
                            orientation = PinOrientation.LEFT
                            y = 0
                            x += WIDTH + PIN_SIZE * 2

                    tmp.append(
                        draw_pin(pin, x, y, PIN_SIZE, orientation, unit=unit)
                    )
                    y -= GRID_STEP
                elif pin.name == 'GND':
                    if power_name in vcc_database:
                        power_name_cnt = 0
                        power_name = pin.name

                    if (power_name_cnt % 2) == 1:
                        orientation = PinOrientation.LEFT
                        x += WIDTH + PIN_SIZE * 2
                    else:
                        orientation = PinOrientation.RIGHT
                        x = 0
                        y -= GRID_STEP

                    power_name_cnt += 1

                    tmp.append(
                        draw_pin(pin, x, y, PIN_SIZE, orientation, unit=unit)
                    )

                    y_end = y

                else:
                    if power_name != pin.name:
                        power_name = pin.name
                        power_name_cnt = 0

                    if (power_name_cnt % 2) == 1:
                        orientation = PinOrientation.LEFT
                        x += WIDTH - PIN_SIZE * 6
                    else:
                        orientation = PinOrientation.RIGHT
                        x = PIN_SIZE * 4
                        y += GRID_STEP

                    power_name_cnt += 1

                    tmp.append(
                        draw_pin(pin, x, y, PIN_SIZE, orientation, unit=unit)
                    )

            tmp.append(
                draw_box(
                    PIN_SIZE,
                    GRID_STEP,
                    WIDTH + PIN_SIZE,
                    y_end - GRID_STEP,
                    unit=unit
                )
            )

            tmp.append(
                draw_text(
                    title,
                    (PIN_SIZE * 2 + WIDTH) / 2,
                    -GRID_STEP * 4,
                    GRID_STEP,
                    bold=True,
                    hjustify=HorizontalJustify.CENTER,
                    unit=unit
                )
            )

            tmp.append(
                draw_text(
                    f'POWER',
                    (PIN_SIZE * 2 + WIDTH) / 2,
                    -GRID_STEP * 6,
                    GRID_STEP / 2,
                    bold=True,
                    hjustify=HorizontalJustify.CENTER,
                    unit=unit
                )
            )

    CODE_START = (
        f'EESchema-LIBRARY Version 2.4\n'
        f'#encoding utf-8\n'
        f'#\n'
        f'# {part}\n'
        f'#\n'
        f'DEF {part} U 0 20 Y Y {unit} L N\n'
        f'F0 "U" 200 300 50 H V L CNN\n'
        f'F1 "{part}" 200 200 50 H V L CNN\n'
        f'F2 "" 0 0 50 H I C CNN\n'
        f'F3 "" 0 0 50 H I C CNN\n'
        f'DRAW\n'
    )

    CODE_END = (
        'ENDDRAW\n'
        'ENDDEF\n'
        '#\n'
        '#End Library'
    )

    code = ''.join(tmp)
    code = CODE_START + code + CODE_END
    return code


if __name__ == '__main__':
    pins = load('../data/xc7s15ftgb196pkg.txt')
    code = make_symbol(pins, 'XC7S15-FTGB196', 'Spartan 7')
    print(code)
