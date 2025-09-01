import argparse
import re
from functools import reduce

DEFAULT_SPACE_RE = "[\\t ]+"

first_pass = True
current_address = 0
output_str = ""

registers = {
    "b": 0,
    "c": 1,
    "d": 2,
    "e": 3,
    "h": 4,
    "l": 5,
    "a": 7,
}

pair = {
    "bc": 0,
    "de": 1,
    "hl": 2,
    "sp": 3,
    "af": 3,
}

flags = {
    'nz': 0,
    'z': 1,
    'nc': 2,
    'c' : 3,
    'po': 4,
    'pe': 5,
    'p': 6,
    'm': 7
}

label_table = {}

EMPTY = 255
A_REG = 1
ANY_REG = 2
IMM = 3
PAIR_REG = 4
LABEL = 5

def get_type(string : str):
    if not string:
        return EMPTY
    
    if string.isdecimal():
        return IMM
    
    if string in registers.keys():
        if string == 'a':
            return A_REG
        return ANY_REG
    
    if string in pair.keys():
        return PAIR_REG
    
    return LABEL
    

def arg_check(op : str, condition : bool):
    if not condition:
        raise Exception(f"Not the args for {op}")

def parse(line : str):
    line = line.lstrip()
    comma_splt = line.split(';')

    split2 = comma_splt[0].split(',')

    second_arg = split2[-1].strip() if len(split2) == 2 else None

    split3 = re.split(DEFAULT_SPACE_RE, split2[0])
    
    (label, op) = (split3[0][0:-1], split3[1]) if ':' in split3[0] else (None, split3[0])

    first_arg = split3[-1]

    return label, op, first_arg, second_arg

def write_inst(inst_size : int, out_val : int, label : None | int):
    global output_str
    global current_address
    global first_pass

    if not first_pass:
        val_bytes= out_val.to_bytes(inst_size, byteorder='little')
        hex_val = val_bytes.hex(' ', bytes_per_sep=1).upper().split()
        result = str(reduce(lambda x,y : f"{x},{y}", map(lambda x : f"${x}", hex_val)))
        current_address += inst_size

        output_str += f"\ndc\t{result}"
        return

    if label:
        if label in label_table:
            raise Exception(f"Label: {label} already exists")
        label_table[label] = current_address
        current_address += inst_size

def nop(tokens):
    arg_check(tokens[1], tokens[2] == None and tokens[3] == None)
    write_inst(1, out_val=0, label=tokens[0])

def ld(tokens):
    first_type = get_type(tokens[2])
    second_type = get_type(tokens[3])
    
    arg_check(tokens[1], first_type < IMM and second_type <= IMM)
    
    if second_type == IMM:
        val = ((6|(registers[tokens[2]]<<3))<<8)|int(tokens[3])
        return write_inst(2, val, tokens[0])
    
    if second_type <= ANY_REG:
        val = 64|(registers[tokens[2]]<<3)|registers[tokens[3]]
        return write_inst(1, val, tokens[0])

def add(tokens):
    first_type = get_type(tokens[2])
    second_type = get_type(tokens[3])
    arg_check(tokens[1], first_type == A_REG and second_type <= IMM)

    if second_type <= ANY_REG:
        val = 128 | registers[tokens[3]]
        return write_inst(1, val, tokens[0])
    
    if second_type == IMM:
        val = 5088 | int(tokens[3])
        return write_inst(2, val, tokens[0])

def adc(tokens):
    first_type = get_type(tokens[2])
    second_type = get_type(tokens[3])

    arg_check(tokens[1], first_type == A_REG and second_type <= IMM)

    if second_type <= ANY_REG:
        val = 136 | registers[tokens[3]]
        return write_inst(1, val, tokens[0])
    
    if second_type == IMM:
        val = 52736 | int(tokens[3])
        return write_inst(2, val, tokens[0])

def sub(tokens):
    first_type = get_type(tokens[2])

    arg_check(tokens[0], first_type < PAIR_REG and tokens[3] == None)

    if first_type < PAIR_REG:
        return write_inst(1, 144 | registers[tokens[2]], tokens[0])

    if first_type == IMM:
        return write_inst(1, 54784 | int(tokens[2]), tokens[0])

def and_inst(tokens):
    first_type = get_type(tokens[2])

    arg_check(tokens[0], first_type < PAIR_REG and tokens[3] == None)

    if first_type < PAIR_REG:
        return write_inst(1, 160 | registers[tokens[2]], tokens[0])
    
    if first_type == IMM:
        return write_inst(2, 58880 | int(tokens[2]), tokens[0])

def process(tokens : tuple[4]):
    if (tokens[1] == None and tokens[2] == None and tokens[3] == None):
        return True
    
    opcode = str.lower(tokens[1])
    
    if opcode == 'nop':
        return nop(tokens)

    if opcode == 'ld':
        return ld(tokens)
    
    if opcode == 'add':
        return add(tokens)
    
    if opcode == 'adc':
        return adc(tokens)
    
    if opcode == 'and':
        return and_inst(tokens)
    
    if opcode == 'bit':
        pass

    if opcode == 'set':
        pass

    if opcode == 'res':
        pass
    
    if opcode == 'call':
        pass

    if opcode == 'ret':
        pass

    if opcode == 'rst':
        pass

    if opcode == 'cp':
        pass
    
    if opcode == 'xor':
        pass

    if opcode == 'inc':
        pass

    if opcode == 'dec':
        pass

    if opcode == 'or':
        pass

    if opcode == 'xor':
        pass
    
    if opcode == 'sub':
        return sub(tokens)

    if opcode == 'sbc':
        pass

    if opcode == 'push':
        pass

    if opcode == 'pop':
        pass

    if opcode == 'jp':
        pass

    if opcode == 'jr':
        pass

    if opcode == 'djnz':
        pass

def convert_asm_code_to_hex(input_path, output_path):
    global first_pass
    global current_address
    with open(input_path, 'r') as input_f:
        current_address = 0
        cant_output = False
        lines = input_f.readlines()
    
        for line_i, line in enumerate(lines, 1):
            try:
                result = parse(line)
                process(result)
            except Exception as e:
                cant_output = True
                print(f"Error on line {line_i}: {e}")

        if cant_output:
            return

        first_pass = False
        current_address = 0
        for lines in lines:
            parse(lines)
            process(result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert z80 asm mnemonics to hex values")
    parser.add_argument("filename", help="file to convert")
    namespace = parser.parse_args()
    filename = vars(namespace)["filename"]
    convert_asm_code_to_hex(filename, None)
    print(output_str)