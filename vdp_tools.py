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
import argparse
from os import SEEK_SET, SEEK_CUR

#Constants
FILE_NAME_REGEX = "(\\w|\\d|\\s)*"
FILEPATH_REGEX = "((\\.|(\\w|\\d|-| )*)(\\/|\\\\)+)"
        
def write_pallete(file_path):
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
                write_file.write(f"{label}End\n")
                write_file.write(f"{label}Size\tequ\t(({label}_end-{label})>>1)\n")

#TODO: .bmp instead of .data
def write_tile(file_path : str):
    with open(file_path, "rb") as file:
        label = re.split(FILEPATH_REGEX, file_path)[-1].split('.')[0]
        if (file.read(2) != b"BM"): raise Exception("File not BMP")
        size = int.from_bytes(file.read(4), 'little')
        file.seek(10, SEEK_SET)
        offset = int.from_bytes(file.read(4), 'little')
        size_dibs = int.from_bytes(file.read(4), 'little')
        width = int.from_bytes(file.read(4), 'little')
        height = int.from_bytes(file.read(4), 'little')
        if not (width % 16) and (height % 16): raise Exception("Not divisible by 16")
        file.seek()

        with open(f"{label}.68k", "w") as write_file:
            end_label = f"{label}End"
            vram_label = f"{label}Vram"
            write_file.write(f"{end_label}\n")
            write_file.write(f"{label}SizeByte\tequ\t({end_label}-{label})\n")
            write_file.write(f"{label}SizeWord\tequ\t({label}_size_byte>>1)\n")
            write_file.write(f"{label}SizeLong\tequ\t({label}_size_byte>>2)\n")
            write_file.write(f"{label}SizeTile\tequ\t({label}_size_byte>>5)\n")
            write_file.write(f"{vram_label}\tequ\t0\n")
            write_file.write(f"{label}_id\tequ\t({vram_label}>>5)\n")
    

def write_sprite(file_path : str, w : int, h : int):
    pass

if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="vdp_tools", description="Tool used to convert palletes or .raw file to pallete values, tiles and sprites")
    parser.add_argument("filename", help="path to the image", required=True)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-p", action="store_true", help="Convert file to pallete")
    group.add_argument("-s", nargs=2, type=int, metavar=('width', 'height'), help="Convert file to sprite")
    group.add_argument("-t", action="store_true", help="Convert file to tile")

    namespace = vars(parser.parse_args())
    if namespace["p"]:
        write_pallete(namespace["filename"])
    if namespace["t"]:
        write_tile(namespace["filename"])
    if namespace["s"]:
        pass
    