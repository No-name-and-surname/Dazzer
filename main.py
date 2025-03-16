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
import select
import tty
import termios
import threading
from threading import Lock

# Add after imports
import sys

def signal_handler(sig, frame):
    print(colored("\nExiting...", "yellow"))
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

#globals initialization ---------------------------------------------------------------------------------------------------
DEBUG_PROB_OF_MUT = [25, 25, 25, 25]
prob_mut_lock = Lock()
stats_lock = Lock()
queue_lock = Lock()
output_lock = Lock()
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
max_coverage = 0  # Track maximum coverage
max_coverage_percent = 0  # Track maximum coverage percentage

# --------------------------------------------------------------------------------------------------------------------------

def get_best_mutator(stats):
    """Determine the most effective mutator based on found issues"""
    mutator_stats = {
        "interesting": 0,
        "ch_symb": 0,
        "length_ch": 0,
        "xor": 0
    }
    
    # Count successful mutations from segfaults
    for i in stats.get('sig_segvi', []):
        if isinstance(i, list) and len(i) > 4:  # Check if i is a list and has enough elements
            mut_type = i[4]
            if mut_type in mutator_stats:
                mutator_stats[mut_type] += 1
    
    # Count successful mutations from floating point exceptions
    for i in stats.get('sig_fpe', []):
        if isinstance(i, list) and len(i) > 4:  # Check if i is a list and has enough elements
            mut_type = i[4]
            if mut_type in mutator_stats:
                mutator_stats[mut_type] += 1
    
    # Count successful mutations from other errors
    for i in stats.get('no_error', []):
        if isinstance(i, list) and len(i) > 4:  # Check if i is a list and has enough elements
            mut_type = i[4]
            if mut_type in mutator_stats:
                mutator_stats[mut_type] += 1
    
    # Find the most successful mutation type
    if any(mutator_stats.values()):
        best_mutator = max(mutator_stats.items(), key=lambda x: x[1])[0]
        if mutator_stats[best_mutator] > 0:
            return best_mutator
    
    return "None"

def get_coverage():
    """Get current code coverage percentage"""
    global max_coverage_percent
    try:
        if os.path.exists('out'):
            # Get coverage info from the most recent file
            files = [f for f in os.listdir('out') if os.path.isfile(os.path.join('out', f))]
            if files:
                latest_file = max(files, key=lambda x: os.path.getctime(os.path.join('out', x)))
                try:
                    coverage = float(latest_file.split(':cov-')[1])
                    max_coverage_percent = max(max_coverage_percent, coverage)
                    return f"{max_coverage_percent:.1f}%"
                except:
                    pass
        return "0.0%"
    except:
        return "0.0%"

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
    # Get the best mutator
    best_mutator = get_best_mutator(stats)
    
    # Calculate total tests
    total_tests = len(stats.get('sig_segvi', [])) + len(stats.get('sig_fpe', [])) + len(stats.get('no_error', []))
    
    # Calculate runtime
    current_time = time.time()
    if not start_time:
        runtime = 0
    else:
        runtime = current_time - start_time
    
    # Calculate tests per second
    tests_per_sec = total_tests / runtime if runtime > 0 else 0
    
    # Ensure DEBUG_PROB_OF_MUT has 4 elements
    global DEBUG_PROB_OF_MUT
    if len(DEBUG_PROB_OF_MUT) < 4:
        DEBUG_PROB_OF_MUT = [25, 25, 25, 25]
    
    # Helper function to format a line with pink borders
    def format_line(label, value, padding):
        formatted_value = f"{str(value):<{padding}}"
        return f"{hex_color('#ff4a96ff', '║')}  {label}: {hex_color('#ffffff', formatted_value)}{hex_color('#ff4a96ff', '║')}"
    
    box_content = [
        hex_color('#ff4a96ff', "╔═══════════════ DAZZER STATISTICS ════════════════╗"),
        hex_color('#ff4a96ff', "║                                                  ║"),
        format_line("Runtime", format_time(round(runtime, 1)), 39),
        format_line("Total Tests", total_tests, 35),
        format_line("Tests/sec", f"{round(tests_per_sec, 1)}/s", 37),
        format_line("Max Coverage", get_coverage(), 34),
        format_line("Best Mutator", best_mutator, 34),
        hex_color('#ff4a96ff', "║                                                  ║")
    ]
    
    # Show return codes only for Gray and Black Box fuzzing
    if config.FUZZING_TYPE == "Gray" or config.FUZZING_TYPE == "Black":
        if stats.get('codes_set'):
            box_content.append(hex_color('#ff4a96ff', "║  Return Codes:                                  ║"))
            for code in sorted(stats.get('codes_set', [])):
                count = stats.get('codes_dict', {}).get(code, 0)
                box_content.append(format_line(f"  Code {code}", count, 33))
    
    # Add mutation probabilities
    box_content.extend([
        hex_color('#ff4a96ff', "║                                                  ║"),
        hex_color('#ff4a96ff', "║  Mutation Probabilities:                         ║"),
        format_line("    Length Change", f"{round(DEBUG_PROB_OF_MUT[0], 1)}%", 29),
        format_line("    XOR", f"{round(DEBUG_PROB_OF_MUT[1], 1)}%", 39),
        format_line("    Symbol Change", f"{round(DEBUG_PROB_OF_MUT[2], 1)}%", 29),
        format_line("    Interesting", f"{round(DEBUG_PROB_OF_MUT[3], 1)}%", 31),
        hex_color('#ff4a96ff', "║                                                  ║"),
        hex_color('#ff4a96ff', "╚══════════════════════════════════════════════════╝")
    ])
    
    return box_content

def hex_to_rgb(hex_color):
    """Convert hex color to RGB values"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_ansi(r, g, b, text):
    """Convert RGB values to ANSI colored text"""
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"

def hex_color(hex_code, text):
    """Apply hex color to text using ANSI escape codes"""
    r, g, b = hex_to_rgb(hex_code)
    return rgb_to_ansi(r, g, b, text)

def display_stats(stats):
    """Display fuzzing statistics in a nice format with a centered box"""
    # Create the statistics box content
    stats_box = create_stats_box(stats)
    
    # Calculate terminal dimensions and center the box
    term_height = term.height
    term_width = term.width
    box_height = len(stats_box)
    
    # Fixed box width (without ANSI codes)
    box_width = 52  # Width of the box frame
    
    # Calculate padding for perfect centering
    box_y = (term_height - box_height) // 2
    box_x = (term_width - box_width) // 2
    
    # Prepare the complete output string with proper centering
    output = ["\033[2J\033[H"]  # Clear screen and move cursor to home position
    
    # Add empty lines before the box for vertical centering
    output.extend(["\n" * box_y])
    
    # Add the box with proper horizontal centering
    for i, line in enumerate(stats_box):
        # Use fixed padding for all lines
        padding = " " * box_x
        output.append("\033[{};{}H{}".format(box_y + i, 0, padding + line))
    
    # Add exit instruction (centered)
    exit_msg = hex_color('#ffffff', "Press 'q' to exit")
    exit_padding = " " * ((term_width - len("Press 'q' to exit")) // 2)
    output.append("\033[{};{}H{}".format(box_y + box_height + 1, 0, exit_padding + exit_msg))
    
    # Print everything at once
    print(''.join(output), flush=True)

def process_queue(queue, queue_name, filik, thread_name):
    """Process a single queue safely"""
    try:
        if not queue or len(queue) == 0:
            return False
        
        current_task = queue[0]
        queue.pop(0)
        
        if not isinstance(current_task, list) or len(current_task) < 2:
            return False
        
        if isinstance(current_task[1], list):
            for j in range(len(current_task[1])):
                processing(current_task, j, filik, thread_name)
        else:
            processing(current_task, 0, filik, thread_name)
            
        return True
        
    except Exception as e:
        with output_lock:
            filik.write(f"\n[{thread_name}] Error in process_queue: {str(e)}\n")
        return False

def processing(task, j, filik, thread_name):
    """Process a single mutation task"""
    try:
        # Perform mutation
        if isinstance(task[1], list):
            mutated_err_data, mut_type = mutator.mutate(task[1][j], 100, new_dict2, new_dict)
        else:
            mutated_err_data, mut_type = mutator.mutate(task[1], 100, new_dict2, new_dict)
        
        # Update info_dict
        try:
            ind = calibrator.info_dict[tuple(task[1])]
            ind2 = calibrator.num + 1
        except:
            ind = calibrator.num + 1
            ind2 = calibrator.num + 2
            calibrator.info_dict.update({tuple(task[1]): ind})
        
        # Process mutation results
        xxxx = copy.deepcopy(task)
        if isinstance(task[1], list):
            xxxx[1][j] = mutated_err_data
            if xxxx[1] != task[1]:
                _, nnn, _, _ = calibrator.testing2(config.file_name, xxxx[1])
                calibrator.info.append([task[1], xxxx[1], ind, ind2, '#ff9cc0', '#ff9cc0', 0, task[0], nnn])
            task[1][j] = mutated_err_data
        else:
            xxxx[1] = mutated_err_data
            if xxxx[1] != task[1]:
                _, nnn, _, _ = calibrator.testing2(config.file_name, xxxx[1])
                calibrator.info.append([task[1], xxxx[1], ind, ind2, '#ff9cc0', '#ff9cc0', 0, task[0], nnn])
            task[1] = mutated_err_data
        
        task[4] = mut_type
        
        # Calibrate
        calibrator.calibrate(task[1], filik, mut_type)
        
    except Exception as e:
        with output_lock:
            filik.write(f"\n[{thread_name}] Error in processing: {str(e)}\n")

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
    # Count successful mutations for each type
    counts = {
        "length_ch": 0,
        "xor": 0,
        "ch_symb": 0,
        "interesting": 0
    }
    
    # Count from all error types
    for error_list in [sig_segvi, sig_fpe, no_error]:
        for i in error_list:
            if isinstance(i, list) and len(i) > 4 and i[4] in counts:
                counts[i[4]] += 1
    
    total = sum(counts.values())
    
    if total == 0:
        # If no successful mutations, use default probabilities
        return [25, 25, 25, 25]
    
    # Calculate percentages based on success rate
    # Add minimum 5% chance for each type to ensure all types get some chance
    base_prob = 5
    remaining_prob = 100 - (base_prob * 4)
    
    probs = []
    for mut_type in ["length_ch", "xor", "ch_symb", "interesting"]:
        if total > 0:
            prob = base_prob + (counts[mut_type] / total) * remaining_prob
        else:
            prob = 25
        probs.append(round(prob, 1))
    
    # Normalize to ensure sum is exactly 100
    total_prob = sum(probs)
    if total_prob != 100:
        probs[-1] += 100 - total_prob
    
    return probs

def restore_terminal():
    """Restore terminal settings"""
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

# Save terminal settings
old_settings = termios.tcgetattr(sys.stdin)

def fuzzing_thread(thread_name, filik):
    """Function to run fuzzing in a separate thread"""
    global DEBUG_PROB_OF_MUT
    
    while True:
        try:
            # Process queues in priority order
            if len(calibrator.queue_seg_fault) > 0:
                process_queue(calibrator.queue_seg_fault, "segfault", filik, thread_name)
            elif len(calibrator.queue_no_error) > 0:
                process_queue(calibrator.queue_no_error, "no_error", filik, thread_name)
            elif len(calibrator.queue_sig_fpe) > 0:
                process_queue(calibrator.queue_sig_fpe, "fpe", filik, thread_name)
            
            # Update probabilities
            with stats_lock:
                sig_segvi, time_out, no_error, sig_fpe = calibrator.ret_globals()
                new_probs = define_probability_of_mutations(no_error, sig_segvi, sig_fpe)
                DEBUG_PROB_OF_MUT = new_probs
            
            time.sleep(0.001)
            
        except Exception as e:
            with output_lock:
                filik.write(f"\n[{thread_name}] Error: {str(e)}\n")

def main():
    global DEBUG_PROB_OF_MUT, start_time, max_coverage_percent
    last_update = time.time()
    update_interval = 0.25
    start_time = time.time()
    max_coverage_percent = 0
    
    with prob_mut_lock:
        DEBUG_PROB_OF_MUT = [25, 25, 25, 25]
    
    # Set terminal to raw mode
    tty.setraw(sys.stdin.fileno())
    
    try:
        with open(config.output_file, 'w') as filik:
            # Initial calibration
            with stats_lock:
                if config.FUZZ not in config.args:
                    calibrator.calibrate(copy.deepcopy(config.args), filik, "first_no_mut")
                else:
                    calibrator.calibrate(copy.deepcopy(config.args), filik, "first_no_mut")
            
            # Create and start fuzzing threads
            thread1 = threading.Thread(
                target=fuzzing_thread,
                args=('thread1', filik),
                daemon=True
            )
            thread2 = threading.Thread(
                target=fuzzing_thread,
                args=('thread2', filik),
                daemon=True
            )
            
            thread1.start()
            thread2.start()
            
            # Main loop for display updates and user input
            while True:
                current_time = time.time()
                
                # Check for 'q' key press
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    char = sys.stdin.read(1)
                    if char == 'q':
                        break
                
                # Update display less frequently
                if current_time - last_update >= update_interval:
                    with stats_lock:
                        sig_segvi, time_out, no_error, sig_fpe = calibrator.ret_globals()
                        stats = {
                            'sig_segvi': sig_segvi,
                            'time_out': time_out,
                            'no_error': no_error,
                            'sig_fpe': sig_fpe,
                            'codes_set': calibrator.codes_set if hasattr(calibrator, 'codes_set') else set(),
                            'codes_dict': calibrator.codes_dict if hasattr(calibrator, 'codes_dict') else {}
                        }
                    display_stats(stats)
                    last_update = current_time
                
                time.sleep(0.01)
            
            # Save results before exiting
            with stats_lock:
                sig_segvi, time_out, no_error, sig_fpe = calibrator.ret_globals()
                with output_lock:
                    filik.write(f"-------------------TOTAL-------------------\n\n\n")
                    if len(sig_segvi) > 0:
                        filik.write('with -11: ' + str(len(sig_segvi)) + '\n\n\n')
                    if len(no_error) > 0:
                        for i in calibrator.codes_set:
                            filik.write(f"with {i}: " + str(calibrator.codes_dict[i]) + '\n\n\n')
                    filik.write(f"-------------------------------------------\n\n\n")
                    with prob_mut_lock:
                        filik.write(f"{DEBUG_PROB_OF_MUT}")
            
            print(colored("\nResults saved to output.txt", "green"))
            
    except Exception as e:
        print(colored(f"\nAn error occurred: {str(e)}", "red"))
    finally:
        restore_terminal()
        sys.exit(0)

def show_welcome_screen():
    title = """
    ╔╦╗┌─┐┌─┐┌─┐┌─┐┬─┐
     ║║├─┤┌─┘┌─┘├┤ ├┬┘
    ═╩╝┴ ┴└─┘└─┘└─┘┴└─
    """
    menu_items = [
        "Start Fuzzing",
        "About",
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
    
    print(hex_color('#ffffff', "Welcome to Dazzer! I hope you've already read README."))
    time.sleep(0.4)
    print(hex_color('#ffffff', "This fuzzer will help you find bugs and vulnerabilities."))
    time.sleep(0.2)
    print(hex_color('#ffffff', "Results will be displayed in a dynamic interface."))
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
            print(colored("\nAll results were saved to 'output.txt'", "magenta"))
            print(calibrator.afiget)
        except Exception as e:
            print(colored(f"\nAn error occurred: {str(e)}", "red"))
            print(colored("Try resizing your terminal or restarting the fuzzer", "white"))
    else:
        print(colored("\nOkay, have a good time, bye! <3", "magenta"))
