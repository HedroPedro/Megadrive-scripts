###############################################################################
# Vdp tools, script to convert raw files into labeled data for ASM68k assembler
# Copyright (C) 2025  Pedro Henrqiue de Oliveira
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################

import re
from sys import argv
import os

#Constants
ASSEMBLY_EXTENSION_REGEX = "(\\.(asm|68k|s))"
RAW_FILE_EXTENSION_REGEX = "(\\.(raw|data))"
TEXT_FILE_EXTENSION_REGEX = "(\\.txt)"
FILE_NAME_REGEX = "(\\w|\\d|\\s)*"
FILEPATH_REGEX = "((\\.|(\\w|\\d|-| )*)(\\/|\\\\)+)"
ASSEMBLY_FILE_REGEX = FILE_NAME_REGEX+ASSEMBLY_EXTENSION_REGEX
TEXT_FILE_REGEX = FILE_NAME_REGEX+TEXT_FILE_EXTENSION_REGEX
RAW_FILE_REGEX = FILE_NAME_REGEX+RAW_FILE_EXTENSION_REGEX

def write_pallete(file_path : str):
    with open(file_path, "r") as file:
        label = re.split(FILEPATH_REGEX, file_path)[-1].split(".")[0]
        with open(f"{label}.68k", "w") as write_file:
            write_file.write(f"{label}:\n")
            lines = file.readlines()
            i = 0
            for line in lines:
                rgb = [int(c) for c in line.split()]
                r = int(14*rgb[0]/255) & 0xE
                g = int(14*rgb[1]/255) & 0xE
                b = int(14*rgb[2]/255) & 0xE
                color = (f"${hex(b)[2:]}{hex(g)[2:]}{hex(r)[2:]}").upper()
                write_file.write(f"\tdc.w\t{color}\t; ({hex(i)[2:].upper()})\n")
                i += 1
            write_file.write(f"{label}_end\n")
            write_file.write(f"{label}_size\tequ\t(({label}_end-{label})/2)\n")
    return

#TODO: .bmp instead of .data
def write_tile(file_path : str, w : int, h : int, is_sprite : bool):
    if(is_sprite and (w > 4 or h > 4)):
        raise Exception("Invalid sprite width or height")

    with open(file_path, "rb") as file:
        label = re.split(FILEPATH_REGEX, file_path)[-1].split('.')[0]
        with open(f"{label}.68k", "w") as write_file:
            file.seek(os.SEEK_SET, os.SEEK_END)
            size = file.tell()
            tile_amount = w * h
            if size >> 6 != tile_amount: #Assumes the user wants the whole content to become tiles or sprite
                raise Exception(f"SIZE NOT FIT FOR {w}X{h}")
            file.seek(os.SEEK_SET, os.SEEK_SET)
            write_file.write(f"{label}:\n")
            data_list = [[[] for _ in range(0, w)] for _ in range(0, h)]
            index_h = 0
            index_w = 0

            for _ in range(0, size, 8):
                data_list[index_h][index_w % w].append(file.read(8))
                index_w += 1    
                if index_w == w * 8:
                    index_h += 1
                    index_w = 0

            #TODO: Make better functions!!!
            def save_tiles():
                for height_list in data_list:
                    for width_list in height_list:
                        tmp_list = list()
                        empty_lines = 0
                        for byte_data in width_list:
                            format_string = "\tdc.l\t$"
                            for byte in byte_data:
                                format_string = format_string + hex(byte)[-1]
                            if format_string == "\tdc.l\t$00000000":
                                empty_lines += 1
                            tmp_list.append(f"{format_string}\n")
                        if empty_lines != 8:
                            tmp_list.append('\n')
                            write_file.writelines(tmp_list)

            def save_sprites():
                sprite_tmp_lst = []
                for height_list in data_list:
                    for width_list in height_list:
                        tmp_list = []
                        for byte_data in width_list:
                            format_str = "\tdc.l\t$"
                            for byte in byte_data:
                                format_str += hex(byte)[-1]
                            tmp_list.append(f"{format_str}\n")
                        sprite_tmp_lst.append(tmp_list)

                sprite_lst = []
                for i in range(0, h):
                    sprite_lst.append(sprite_tmp_lst[i::h])
                
                for sprites in sprite_lst:
                    for sprite in sprites:
                        i = 0
                        for data in sprite:
                            write_file.write(data)
                            i += 1
                            if i & 7 == 0:
                                write_file.write("\n")
            
            save_in_file = save_sprites if is_sprite else save_tiles
            save_in_file()

            end_label = f"{label}_end"
            vram_label = f"{label}_vram"
            write_file.write(f"{end_label}\n")
            write_file.write(f"{label}_size_byte\tequ\t({end_label}-{label})\n")
            write_file.write(f"{label}_size_word\tequ\t({label}_size_byte/2)\n")
            write_file.write(f"{label}_size_long\tequ\t({label}_size_byte/4)\n")
            write_file.write(f"{label}_size_tile\tequ\t({label}_size_byte/32)\n")
            write_file.write(f"{vram_label}\tequ\t0\n")
            write_file.write(f"{label}_id\tequ\t({vram_label}/32)\n")
    return

if __name__ == "__main__":
    if len(argv) == 1:
        raise Exception(f"Try python3 {__file__} -h")
    
    match argv[1]:
        case "-h":
            print("-p file - convert a .txt into a palette")
            print("-t file (tiles per row) (tiles per line) - convert raw file into tiles")
            print("-s file (tiles per row) (tiles per line) - convert raw file into sprite mode with appropriate formatting")
            print("-h - print this information to the screen")
            exit()
        case "-p":
            argv = argv[2:]
            if len(re.findall(TEXT_FILE_REGEX, argv[0])) == 1:
                file = argv[0]
                write_pallete(file)
                exit()
            raise Exception("NOT A TEXT FILE")
        case "-t":
            argv = argv[2:]
            if len(re.findall(RAW_FILE_REGEX, argv[0])) == 1:
                write_tile(argv[0], abs(int(argv[1])), abs(int(argv[2])), False)
                exit()
        case "-s":
            argv = argv[2:]
            if len(re.findall(RAW_FILE_REGEX, argv[0])) == 1:
                write_tile(argv[0], abs(int(argv[1])), abs(int(argv[2])), True)
                exit()
        case _:
            raise Exception(f"Option not recognized. Try python3 {__file__} -h")