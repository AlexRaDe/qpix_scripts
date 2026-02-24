### CALIBRATION SCRIPT ########################################
# Authors: PURM Students Summer 2024, NCD, ACG
# Usage: python3 run_calibration.py
# Notes: can run for a range of DAC settings OR one DAC setting
###############################################################

import sys
import os
import time
from commands.sampling_functions import *
from commands.helper_functions import *
from commands.serial_interface import send_serial_command # No more os.system!

### USER INPUTS ###
DAC_settings = range(12, 32, 1)
trials_num = 1
interface = 1
delta_t = 0
win_width = 100e-6
win_wait = 5e-6
reset_width = 5e-6
rst_cal_gap = 100e-9
config_file = 'configs/calibration.cfg'
external_clock = True

# --- PRE-LOOP OPTIMIZATIONS ---
# 1. Cache the config file once. No more reading inside the loop.
default_config_bin = read_config_file(config_file)
# 2. Cache channels in use once.
working_channels = get_channels_in_use()

def make_hex_command_fast(DAC_val, base_config):
    """Replaces make_five and string slicing with efficient formatting."""
    # Get 5-bit binary representation
    dac_bits = f"{DAC_val & 0x1F:05b}"
    replCur0 = dac_bits[0]          # MSB of the 5 bits
    replCur1_4 = dac_bits[1:][::-1] # Next 4 bits reversed

    # Slice the cached string
    final_bin = replCur1_4 + base_config[4:24] + replCur0 + base_config[25:]
    return int(final_bin, 2) # Return as integer for send_serial_command

# Clean up output files once at the start
for c in range(7):
    fname = f'outputs/ch{c}_calib.txt'
    if os.path.exists(fname):
        os.remove(fname)

# Open all output files once and keep them in a dictionary
out_files = {c: open(f'outputs/ch{c}_calib.txt', 'a') for c in range(7)}

try:
    set_ext_clock(1 if external_clock else 0)
    set_sample_select(1)
    set_delta_t(delta_t)

    print("Running Calibration...")
    with open('deltaT_log.txt', 'a') as delta_log:
        for i, DAC_setting in enumerate(DAC_settings, 1):

            # Use the fast bitwise/cached function
            cmd_int = make_hex_command_fast(DAC_setting, default_config_bin)

            print(f'*** DAC setting: {DAC_setting}, ({i} out of {len(DAC_settings)}) ***')

            # CALL DIRECTLY: No new Python process spawned here
            send_serial_command(interface, cmd_int)

            delta_log.write(f"\n-- DAC setting: {DAC_setting} ---\n")

            # Sampling logic
            all_counts, all_timestamps = sample_n_trials(
                trials_num, win_width=win_width, win_wait=win_wait,
                reset_width=reset_width, rst_cal_gap=rst_cal_gap,
                external_clock=external_clock, sampling=True,
                cal_pulse=False, file_writer=delta_log
            )

            # Fast writing to open file handles
            for c in range(7):
                counts = [trial[c] for trial in all_counts]
                mean_val = sum(counts)/len(counts)

                f = out_files[c]
                f.write(f'DAC setting: {DAC_setting}\nCounts: {counts}\nMean: {mean_val:.2f}\n')

                if c in working_channels:
                    print(f'Channel {c} counts: {counts}, Mean: {mean_val:.2f}')
            print("#"*10 + "\n")

finally:
    # Ensure all files close if the script is interrupted
    for f in out_files.values():
        f.close()
    print("Calibration complete. Files closed.")
