import sys
import os
import time
import argparse
from commands.sampling_functions import *
from commands.helper_functions import *
from commands.serial_interface import send_serial_command

def parse_args():
    parser = argparse.ArgumentParser(description="QPix FPGA Calibration Script (mmap optimized)")
    
    # DAC Settings: allows a range (start stop step)
    parser.add_argument('--dac_range', type=int, nargs=3, default=[12, 32, 1],
                        help="DAC settings as: start stop step (default: 12 32 1)")
    
    # Integer/Float Inputs
    parser.add_argument('--trials_num', type=int, default=1, help="Number of trials")
    parser.add_argument('--interface', type=int, default=1, help="Serial interface ID")
    parser.add_argument('--delta_t', type=int, default=0, help="Delta T select")
    parser.add_argument('--win_width', type=float, default=100e-6, help="Window width in seconds")
    parser.add_argument('--win_wait', type=float, default=5e-6, help="Window wait in seconds")
    parser.add_argument('--reset_width', type=float, default=5e-6, help="Reset width in seconds")
    parser.add_argument('--rst_cal_gap', type=float, default=100e-9, help="RST/Cal gap in seconds")
    
    # Files and Flags
    parser.add_argument('--config_file', type=str, default='configs/calibration.cfg', help="Path to config file")
    parser.add_argument('--no_ext_clock', action='store_false', dest='external_clock', help="Disable external clock")
    parser.set_defaults(external_clock=True)
    
    # Sample Select Toggle (The one we missed!)
    parser.add_argument('--sample_select', type=int, choices=[0, 1], default=1, 
                        help="Set sample select bit (default: 1)")

    # Sampling/Pulse Logic
    parser.add_argument('--sampling', action='store_false', dest='sampling', help="Disable sampling")
    parser.set_defaults(sampling=True)
    parser.add_argument('--cal_pulse', action='store_true', dest='cal_pulse', help="Enable calibration pulse")
    parser.set_defaults(cal_pulse=False)

    return parser.parse_args()

def make_hex_command_fast(DAC_val, base_config):
    """Replaces make_five and string slicing with efficient formatting."""
    dac_bits = f"{DAC_val & 0x1F:05b}"
    replCur0 = dac_bits[0]
    replCur1_4 = dac_bits[1:][::-1]
    final_bin = replCur1_4 + base_config[4:24] + replCur0 + base_config[25:]
    return int(final_bin, 2)

def main():
    args = parse_args()
    
    # Generate the range object from arguments
    DAC_settings = range(args.dac_range[0], args.dac_range[1], args.dac_range[2])

    # --- PRE-LOOP OPTIMIZATIONS ---
    default_config_bin = read_config_file(args.config_file)
    working_channels = get_channels_in_use()

    # Clean and open output files
    out_files = {}
    for c in range(7):
        fname = f'outputs/ch{c}_calib.txt'
        if os.path.exists(fname):
            os.remove(fname)
        out_files[c] = open(fname, 'a')

    try:
        set_ext_clock(1 if args.external_clock else 0)
        set_sample_select(1)
        set_delta_t(args.delta_t)

        print(f"Running Calibration on interface {args.interface}...")
        
        with open('deltaT_log.txt', 'a') as delta_log:
            for i, DAC_setting in enumerate(DAC_settings, 1):
                
                cmd_int = make_hex_command_fast(DAC_setting, default_config_bin)
                print(f'*** DAC setting: {DAC_setting}, ({i} out of {len(DAC_settings)}) ***')

                # CALL DIRECTLY: No new Python process spawned
                send_serial_command(args.interface, cmd_int)

                delta_log.write(f"\n-- DAC setting: {DAC_setting} ---\n")

                # Sampling logic using arguments
                all_counts, all_timestamps = sample_n_trials(
                    args.trials_num, 
                    win_width=args.win_width, 
                    win_wait=args.win_wait,
                    reset_width=args.reset_width, 
                    rst_cal_gap=args.rst_cal_gap,
                    external_clock=args.external_clock, 
                    sampling=args.sampling,
                    cal_pulse=args.cal_pulse, 
                    file_writer=delta_log
                )

                # Output Processing
                for c in range(7):
                    counts = [trial[c] for trial in all_counts]
                    mean_val = sum(counts)/len(counts) if counts else 0

                    f = out_files[c]
                    f.write(f'DAC setting: {DAC_setting}\nCounts: {counts}\nMean: {mean_val:.2f}\n')

                    if c in working_channels:
                        print(f'Channel {c} counts: {counts}, Mean: {mean_val:.2f}')
                print("#"*10 + "\n")

    finally:
        for f in out_files.values():
            f.close()
        print("Calibration complete. Files closed.")

if __name__ == "__main__":
    main()
