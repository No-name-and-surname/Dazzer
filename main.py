import calibrator
import mutator
import config
import copy
from random import *
from blessings import Terminal
from termcolor import colored
import os
import time
import signal
import curses
from pyvis.network import Network
import networkx as nx
from screeninfo import get_monitors
import re
from simple_term_menu import TerminalMenu
import sys
from datetime import datetime

#globals initialization ---------------------------------------------------------------------------------------------------
DEBUG_PROB_OF_MUT = [25, 25, 25]
TIMEOUT = 1
width_1 = (str(list(get_monitors())[0])[8:].split(', '))[2].split('width=')[1] + 'px'
height_1 = (str(list(get_monitors())[0])[8:].split(', '))[3].split('height=')[1] + 'px'
nt = Network(height_1, width='100%',  bgcolor="#111111", font_color="white",  select_menu=True)
pos = 27
places = []
codes = []
countik = 0
MAX_C = 0
flag = 0
term = Terminal()
dictionary = open(config.dict_name, 'rb').read().decode().split('\r\n')
new_dict, new_dict2 = [], []
start_time = None
total_tests = 0
saved_tests = 0
last_update_time = 0
update_interval = 0.1  # Update every 100ms

# --------------------------------------------------------------------------------------------------------------------------

def get_best_mutator(stats):
    """Determine the most effective mutator based on found issues"""
    mutator_stats = {
        "interesting": 0,
        "ch_symb": 0,
        "length_ch": 0,
        "xor": 0
    }
    
    for i in stats.get('sig_segvi', []):
        if i[4] in mutator_stats:
            mutator_stats[i[4]] += 1
    
    for i in stats.get('sig_fpe', []):
        if i[4] in mutator_stats:
            mutator_stats[i[4]] += 1
            
    best_mutator = max(mutator_stats.items(), key=lambda x: x[1])[0] if any(mutator_stats.values()) else "None"
    return best_mutator

def get_coverage():
    """Get current code coverage"""
    try:
        if os.path.exists('out'):
            files = len([f for f in os.listdir('out') if os.path.isfile(os.path.join('out', f))])
        else:
            files = 0
        return files
    except:
        return 0

def format_time(seconds):
    """Format seconds into readable time"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{int(minutes)}m {int(seconds)}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{int(hours)}h {int(minutes)}m"

def create_stats_box(stats):
    """Create a formatted statistics box"""
    box_content = [
        "╔═══════════════ FUZZING STATISTICS ═══════════════╗",
        "║                                                  ║",
        f"║  Segmentation Faults: {len(stats.get('sig_segvi', [])):<24} ║",
        f"║  Floating Point Exceptions: {len(stats.get('sig_fpe', [])):<17} ║"
    ]
    
    # Add return codes if any exist
    if stats.get('codes_set'):
        for code in stats.get('codes_set', []):
            count = stats.get('codes_dict', {}).get(code, 0)
            box_content.append(f"║  Return Code {code}: {count:<28} ║")
    
    box_content.extend([
        "║                                                  ║",
        "╚══════════════════════════════════════════════════╝"
    ])
    
    return box_content

def display_stats(stats):
    """Display fuzzing statistics in a nice format with a centered box"""
    # Clear screen
    os.system('clear')
    
    # Create and display the statistics box
    stats_box = create_stats_box(stats)
    
    # Calculate terminal dimensions and center the box
    term_height = term.height
    term_width = term.width
    box_height = len(stats_box)
    box_width = len(stats_box[0])
    box_y = (term_height - box_height) // 2
    box_x = (term_width - box_width) // 2
    
    # Print the box
    for i, line in enumerate(stats_box):
        print("\033[{};{}H{}".format(box_y + i, box_x, colored(line, "cyan")))
    
    # Print exit instruction
    print("\033[{};{}H{}".format(box_y + box_height + 1, box_x, colored("Press Ctrl+C to exit", "yellow")))

def processing(listik, j, filik):
    mutated_err_data, mut_type = mutator.mutate(listik[0][1][j], 100, new_dict2, new_dict)
    try:
        ind = calibrator.info_dict[tuple(listik[0][1])]
        ind2 = calibrator.num + 1
    except:
        ind = calibrator.num + 1
        ind2 = calibrator.num + 2
        calibrator.info_dict.update({tuple(listik[0][1]):ind})
    xxxx = copy.deepcopy(listik)
    xxxx[0][1][j] = mutated_err_data
    if xxxx[0][1] != listik[0][1]:
        _, nnn, _, _ = calibrator.testing2(config.file_name, xxxx[0][1])
        calibrator.info.append([listik[0][1], xxxx[0][1], ind, ind2, '#ff9cc0', '#ff9cc0', 0, listik[0][0], nnn])
    listik[0][1][j] = mutated_err_data
    listik[0][4] = mut_type
    calibrator.calibrate(listik[0][1], filik, mut_type)

def extract_strings(file_path, min_length=4):
    strings = []
    with open(file_path, 'rb') as f:
        data = f.read()
        current_string = []
        
        for byte in data:
            if 32 <= byte <= 126:
                current_string.append(chr(byte))
            else:
                if current_string:
                    string = ''.join(current_string)
                    if len(string) >= min_length:
                        strings.append(string)
                    current_string = []
        if current_string:
            string = ''.join(current_string)
            if len(string) >= min_length:
                strings.append(string)
    
    return strings

file_path = config.file_name
strings = extract_strings(file_path)

def define_probability_of_mutations(no_error, sig_segvi, sig_fpe):
    try:
        c_in = 0
        c_chl = 0
        c_chs = 0
        c_x = 0
        for i in sig_segvi:
            if i[4] == "interesting":
                c_in += 1
            elif i[4] == "ch_symb":
                c_chs += 1
            elif i[4] == "length_ch":
                c_chl += 1
            elif i[4] == "xor":
                c_x += 1
        summochka = c_chl + c_x + c_in + c_chs
        try:
            mutator.probability_interesting = summochka // c_in * 100
        except:
            mutator.probability_interesting = 0

        try:
            mutator.probability_ch_symb = summochka // c_chs * 100
        except:
            mutator.probability_ch_symb = 0

        try:
            mutator.probability_length_ch = summochka // c_chl * 100
        except:
            mutator.probability_length_ch = 0

        try:
            mutator.probability_xor = summochka // c_x * 100
        except:
            mutator.probability_xor = 0
        # else:
        #     mutator.probability_dict = c_d * p_c
        #     mutator.probability_ch_symb = c_chs * p_c + 100 % summochka
        #     mutator.probability_length_ch = c_chl * p_c
        #     mutator.probability_xor = c_x * p_c
    except:
        pass

    chances= [c_chl,c_x,c_chs, c_in]
    try:
        chaces_fix=100/sum(chances)
        chances = [i*chaces_fix for i in chances]
    except:
        chances = [25,25,25,25]
    
    return chances

def main():
    global DEBUG_PROB_OF_MUT
    with open(config.output_file, 'w') as filik:
        if config.FUZZ not in config.args:
            calibrator.calibrate(copy.deepcopy(config.args), filik, "first_no_mut")
        else:
            calibrator.calibrate(copy.deepcopy(config.args), filik, "first_no_mut")

        step = -1
        while True:
            try:
                step += 1
                sig_segvi, time_out, no_error, sig_fpe = calibrator.ret_globals()
                
                # Prepare stats for display
                stats = {
                    'sig_segvi': sig_segvi,
                    'time_out': time_out,
                    'no_error': no_error,
                    'sig_fpe': sig_fpe,
                    'codes_set': calibrator.codes_set if hasattr(calibrator, 'codes_set') else set(),
                    'codes_dict': calibrator.codes_dict if hasattr(calibrator, 'codes_dict') else {}
                }
                
                # Update display
                display_stats(stats)

                # Original fuzzing logic
                if len(sig_segvi) != 0 and len(calibrator.queue_seg_fault) != 0:
                    if len(sig_segvi) == 1:
                        for i in range(len(sig_segvi)):
                            my_err = copy.deepcopy(calibrator.queue_seg_fault)
                    else:
                        my_err = copy.deepcopy(calibrator.queue_seg_fault)
                    if len(calibrator.queue_seg_fault[0][1]) > 1:
                        for j in range(len(calibrator.queue_seg_fault[0][1])):
                            processing(calibrator.queue_seg_fault, j, filik)
                        calibrator.queue_seg_fault.pop(0)      
                    else:
                        processing(calibrator.queue_seg_fault, 0, filik)
                        calibrator.queue_seg_fault.pop(0)

                if len(no_error) != 0 or len(sig_fpe) != 0:
                    if len(no_error) != 0:
                        if len(no_error) == 1:
                            for i in range(len(no_error)):
                                my_err = copy.deepcopy(calibrator.queue_no_error)
                        else:
                            my_err = copy.deepcopy(calibrator.queue_no_error)
                        try:
                            if len(calibrator.queue_no_error[0][1]) > 1:
                                for j in range(len(calibrator.queue_no_error[0][1])):
                                    processing(calibrator.queue_no_error, j, filik)
                                calibrator.queue_no_error.pop(0)
                            else:
                                processing(calibrator.queue_no_error, 0, filik)
                                calibrator.queue_no_error.pop(0)
                        except:
                            continue
                    else:
                        if len(sig_fpe) == 1 and len(calibrator.queue_sig_fpe) != 0:
                            for i in range(len(sig_fpe)):
                                sig_fpe_1 = copy.deepcopy(calibrator.queue_sig_fpe)
                        else:
                            sig_fpe_1 = copy.deepcopy(calibrator.queue_sig_fpe)
                        if len(calibrator.queue_sig_fpe[0][1]) > 1:
                            for j in range(len(calibrator.queue_sig_fpe[0][1])):
                                processing(calibrator.queue_sig_fpe, j, filik)
                            calibrator.queue_sig_fpe.pop(0)

                DEBUG_PROB_OF_MUT = define_probability_of_mutations(no_error, sig_segvi, sig_fpe)
                
            except KeyboardInterrupt:
                filik.write(f"-------------------TOTAL-------------------\n\n\n")
                if len(sig_segvi) > 0:
                    filik.write('with -11: ' + str(len(sig_segvi)) + '\n\n\n')
                if len(no_error) > 0:
                    for i in calibrator.codes_set:
                        filik.write(f"with {i}: " + str(calibrator.codes_dict[i]) + '\n\n\n')
                filik.write(f"-------------------------------------------\n\n\n")
                filik.write(f"{DEBUG_PROB_OF_MUT}")
                break

def show_welcome_screen():
    title = """
    ╔╦╗┌─┐┌─┐┌─┐┌─┐┬─┐
     ║║├─┤┌─┘┌─┘├┤ ├┬┘
    ═╩╝┴ ┴└─┘└─┘└─┘┴└─
    """
    menu_items = [
        "Start Fuzzing",
        "Exit"
    ]
    terminal_menu = TerminalMenu(
        menu_items,
        title=title,
        menu_cursor="→ ",
        menu_cursor_style=("fg_purple", "bold"),
        menu_highlight_style=("bg_purple", "fg_black"),
        cycle_cursor=True,
        clear_screen=True
    )
    
    print(colored("Welcome to Dazzer! I hope you've already read README.", "cyan"))
    time.sleep(0.4)
    print(colored("This fuzzer will help you find bugs and vulnerabilities.", "cyan"))
    time.sleep(0.2)
    print(colored("Results will be displayed in a dynamic interface.", "cyan"))
    time.sleep(0.2)
    
    selection = terminal_menu.show()
    return selection

if __name__ == '__main__':
    selection = show_welcome_screen()
    if selection == 0:  # Start Fuzzing
        try:
            main()
            nt.set_options("""
                const options = {
                "physics": {
                    "barnesHut": {
                    "gravitationalConstant": -26300
                    },
                    "minVelocity": 0.75
                }
                }""")
            for i in copy.deepcopy(calibrator.info):
                src, dst = i[0], i[1]
                if i[6] == 0: 
                    nt.add_node(i[2], str(src) + f";  code:{i[7]}", color=i[4], title=str(src))
                    nt.add_node(i[3], str(dst) + f";  code:{i[8]}", color=i[5], title=str(dst))
                    nt.add_edge(i[2], i[3], weight=5)
                    i[6] = 1
            print(colored("\nAll results were saved to 'output.txt'", "green"))
            print(calibrator.afiget)
        except Exception as e:
            print(colored(f"\nAn error occurred: {str(e)}", "red"))
            print(colored("Try resizing your terminal or restarting the fuzzer", "yellow"))
    else:
        print(colored("\nOkay, have a good time, bye! <3", "magenta"))
