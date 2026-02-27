### ALL HELPER FUNCTIONS ########################
# Authors: ACG
# Usage: from commands.helper_functions import *
# Notes: contains all low-level helper functions
#################################################

import os
import sys
import mmap
import csv

# --- FPGA MEMORY CONFIGURATION ---
FPGA_BASE_ADDR = 0x43C00000
MAP_SIZE = 0x1000 # 4KB

# Initialize memory mapping
try:
    _f = open("/dev/mem", "r+b")
    # Mapping the memory block globally
    _mem = mmap.mmap(_f.fileno(), MAP_SIZE, offset=FPGA_BASE_ADDR)
except PermissionError:
    print("Error: Accessing /dev/mem requires sudo/root privileges.")
    sys.exit(1)

def poke(addr, value):
    """Internal helper to write 32-bit values to a physical address."""
    offset = addr - FPGA_BASE_ADDR
    _mem[offset:offset+4] = value.to_bytes(4, byteorder='little')

def peek(addr):
    """Internal helper to read 32-bit values from a physical address."""
    offset = addr - FPGA_BASE_ADDR
    return int.from_bytes(_mem[offset:offset+4], byteorder='little')

# -----------------------------------------------

def get_channels_in_use():
    paths = ['channels_in_use.csv', '../channels_in_use.csv']
    for path in paths:
        if os.path.exists(path):
            with open(path, newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    return [int(c) for c in row]
    return []

def get_channel_registers(c):
    # Converted hex strings to integers for faster math
    channel_registers = [
        [0, 0x43c001b4, 0x43c00108, 0x43c0010c], [1, 0x43c001b8, 0x43c00110, 0x43c00114],
        [2, 0x43c001bc, 0x43c00118, 0x43c0011c], [3, 0x43c001c0, 0x43c00120, 0x43c00124],
        [4, 0x43c001c4, 0x43c00128, 0x43c0012c], [5, 0x43c001c8, 0x43c00130, 0x43c00134],
        [6, 0x43c001cc, 0x43c00138, 0x43c0013c], [7, 0x43c001d0, 0x43c00140, 0x43c00144],
        [8, 0x43c001d4, 0x43c00148, 0x43c0014c], [9, 0x43c001d8, 0x43c00150, 0x43c00154],
        [10, 0x43c001dc, 0x43c00158, 0x43c0015c], [11, 0x43c001e0, 0x43c00160, 0x43c00164],
        [12, 0x43c001e4, 0x43c00168, 0x43c0016c], [13, 0x43c001e8, 0x43c00170, 0x43c00174],
        [14, 0x43c001ec, 0x43c00178, 0x43c0017c], [15, 0x43c001f0, 0x43c00180, 0x43c00184]
    ]
    return channel_registers[c][1:]

def calibration_pulse():
    # Bitwise approach: Set bit 4 (adjust index if your 'initial_setting_bin[27]' meant something else)
    val = peek(0x43c00000)
    new_val = val | (1 << 4) # Sets bit 4 to '1'
    poke(0x43c00000, new_val)
    print('Asserting calibration pulse sequence on cal_control1,2 and RST_EXT1,2.')

def sample_pulse():
    val = peek(0x43c00000)
    new_val = val | (1 << 15) # Example: bit 15
    poke(0x43c00000, new_val)
    print('Asserting sampling sequence on window_trig.')

def startup():
    poke(0x43c00000, 0x00000001)
    print('Asserting master logic reset...', end='')
    poke(0x43c00000, 0x00000000)
    print(" done.")

def set_ext_clock(on):
    val = peek(0x43c00000)
    if on == 1:
        # Set bits 16 and 17 to '11'
        new_val = (val & ~(0b11 << 16)) | (0b11 << 16)
        state = 'on'
    else:
        # Clear bits 16 and 17 to '00'
        new_val = val & ~(0b11 << 16)
        state = 'off'
    poke(0x43c00000, new_val)
    print(f'Replenishment clocks {state}.')

def set_win_width(t):
    width = int(t / 20e-9)
    poke(0x43c0001c, width)

def set_rst_cal_gap(t):
    ticks = int(t / 20e-9) & 0xFFFF
    val = peek(0x43c00020)
    # Keep 16 LSBs, replace 16 MSBs
    new_val = (val & 0x0000FFFF) | (ticks << 16)
    poke(0x43c00020, new_val)

def set_reset_width(t):
    ticks = int(t / 20e-9) & 0xFFFF
    val = peek(0x43c00020)
    # Keep 16 MSBs, replace 16 LSBs
    new_val = (val & 0xFFFF0000) | ticks
    poke(0x43c00020, new_val)

def set_win_wait(t):
    ticks = int(t / 20e-9) & 0x7FFFFFFF
    val = peek(0x43c00024)
    # Keep MSB (bit 31), replace everything else
    new_val = (val & 0x80000000) | ticks
    poke(0x43c00024, new_val)

def set_sample_select(on):
    val = peek(0x43c00024)
    if on:
        new_val = val | 0x80000000
    else:
        new_val = val & 0x7FFFFFFF
    poke(0x43c00024, new_val)

def set_delta_t(on):
    poke(0x43c00028, on)
    print(f'deltaT_select set to {on}')

def read_ch_status(c):
    fifo_status_reg, _, _ = get_channel_registers(c)
    ch_status = peek(fifo_status_reg)
    # Bit parsing
    return (
        (ch_status >> 10) & 0x3, # wr_rst_busy
        (ch_status >> 9) & 0x1,  # almost_full
        (ch_status >> 8) & 0x1,  # full
        (ch_status >> 2) & 0x1,  # rd_rst_busy
        (ch_status >> 1) & 0x1,  # almost_empty
        (ch_status & 0x1)        # empty
    )

def read_ch_fifo(c):
    _, ts_hi_reg, ts_lo_reg = get_channel_registers(c)
    poke(0x43c00018, (1 << c))
    poke(0x43c00018, 0x00000000)
    hi = peek(ts_hi_reg)
    lo = peek(ts_lo_reg)
    return (hi << 32) + lo

def read_config_file(filename):
    if not os.path.exists(filename):
        print(f'Error: Config file {filename} does not exist.')
        sys.exit()
    settings_string = ''
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0][-1] not in ('1', '0'):
                print(f'Error: Config file not formatted properly.')
                sys.exit()
            settings_string += row[0][-1]
    if len(settings_string) != 32:
        print(f'Error: Config file is wrong length.')
        sys.exit()
    return settings_string

def make_serial_command(settings_string): #takes input in binary
    hex_command = f'0x{int(settings_string, 2):08X}'
    return hex_command


