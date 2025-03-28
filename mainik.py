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

import sys

def fill_screen_black():
    sys.stdout.write("\033[2J")
    sys.stdout.write("\033[40m")
    sys.stdout.write("\033[30m")
    sys.stdout.write("\033[1;1H")
    term = Terminal()
    width = term.width
    height = term.height
    for _ in range(height):
        sys.stdout.write(" " * width)

    sys.stdout.write("\033[1;1H")
    sys.stdout.write("\033[37m")
    sys.stdout.flush()
    
    loading_position = height // 2
    sys.stdout.write(f"\033[{loading_position};{width//2 - 10}H")
    sys.stdout.write(colored("Preparing Dazzer...", "white"))
    sys.stdout.flush()
    
    bar_width = 20
    sys.stdout.write(f"\033[{loading_position + 1};{width//2 - bar_width//2}H[")
    sys.stdout.write(" " * bar_width)
    sys.stdout.write("]")
    sys.stdout.flush()
    
    for i in range(bar_width):
        time.sleep(0.02)
        sys.stdout.write(f"\033[{loading_position + 1};{width//2 - bar_width//2 + 1 + i}H")
        sys.stdout.write(colored("█", "magenta"))
        sys.stdout.flush()
    
    time.sleep(0.2)
    sys.stdout.write("\033[2J")
    sys.stdout.write("\033[1;1H")
    sys.stdout.flush()

def signal_handler(sig, frame):
    sys.stdout.write("\033[0m")
    sys.stdout.flush()
    print(colored("\nExiting...", "yellow"))
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

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
update_interval = 0.1
max_coverage = 0
max_coverage_percent = 0
thread_stats = {}
thread_stats_lock = Lock()
queue_cache = {'seg_fault': 0, 'no_error': 0, 'sig_fpe': 0}
queue_cache_lock = Lock()

def get_best_mutator(stats):
    """Determine the most effective mutator based on found issues"""
    mutator_stats = {
        "interesting": 0,
        "ch_symb": 0,
        "length_ch": 0,
        "xor": 0
    }
    
    for i in stats.get('sig_segvi', []):
        if isinstance(i, list) and len(i) > 4:
            mut_type = i[4]
            if mut_type in mutator_stats:
                mutator_stats[mut_type] += 1
    
    for i in stats.get('sig_fpe', []):
        if isinstance(i, list) and len(i) > 4:
            mut_type = i[4]
            if mut_type in mutator_stats:
                mutator_stats[mut_type] += 1
    
    for i in stats.get('no_error', []):
        if isinstance(i, list) and len(i) > 4:
            mut_type = i[4]
            if mut_type in mutator_stats:
                mutator_stats[mut_type] += 1
    
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
    best_mutator = get_best_mutator(stats)
    
    total_tests = len(stats.get('sig_segvi', [])) + len(stats.get('sig_fpe', [])) + len(stats.get('no_error', []))
    
    current_time = time.time()
    if not start_time:
        runtime = 0
    else:
        runtime = current_time - start_time
    
    tests_per_sec = total_tests / runtime if runtime > 0 else 0
    
    global DEBUG_PROB_OF_MUT
    if len(DEBUG_PROB_OF_MUT) < 4:
        DEBUG_PROB_OF_MUT = [25, 25, 25, 25]
    
    def format_line(label, value, padding):
        formatted_value = f"{str(value):<{padding}}"
        return f"{hex_color('#ff4a96ff', '║')}  {label}: {hex_color('#ffffff', formatted_value)}{hex_color('#ff4a96ff', '║')}"
    
    box_content = [
        hex_color('#ff4a96ff', "╔═══════════════ DAZZER STATISTICS ════════════════╗"),
        hex_color('#ff4a96ff', "║                                                  ║"),
        format_line("Runtime", format_time(round(runtime, 1)), 39),
        format_line("Total Tests", total_tests, 35),
        format_line("Tests/sec", f"{round(tests_per_sec, 1)}/s", 37),
        format_line("Threads Running", config.NUM_THREADS, 31),
        format_line("Max Coverage", get_coverage(), 34),
        format_line("Best Mutator", best_mutator, 34),
        hex_color('#ff4a96ff', "║                                                  ║")
    ]
    
    if config.FUZZING_TYPE == "Gray" or config.FUZZING_TYPE == "Black":
        if stats.get('codes_set'):
            box_content.append(hex_color('#ff4a96ff', "║  Return Codes:                                  ║"))
            for code in sorted(stats.get('codes_set', [])):
                count = stats.get('codes_dict', {}).get(code, 0)
                box_content.append(format_line(f"  Code {code}", count, 33))
    
    box_content.extend([
        hex_color('#ff4a96ff', "║                                                  ║"),
        hex_color('#ff4a96ff', "║  Mutation Probabilities:                         ║"),
        format_line("    Length Change", f"{round(DEBUG_PROB_OF_MUT[0], 1)}%", 29),
        format_line("    XOR", f"{round(DEBUG_PROB_OF_MUT[1], 1)}%", 39),
        format_line("    Symbol Change", f"{round(DEBUG_PROB_OF_MUT[2], 1)}%", 29),
        format_line("    Interesting", f"{round(DEBUG_PROB_OF_MUT[3], 1)}%", 31),
        hex_color('#ff4a96ff', "║                                                  ║")
    ])
    
    if thread_stats:
        box_content.append(hex_color('#ff4a96ff', "║  Thread Statistics:                              ║"))
        sorted_threads = sorted(thread_stats.items(), key=lambda x: x[1], reverse=True)
        for thread_name, tests in sorted_threads:
            if thread_name.startswith("thread"):
                thread_pct = (tests / total_tests * 100) if total_tests > 0 else 0
                box_content.append(format_line(f"    {thread_name}", f"{tests} ({round(thread_pct, 1)}%)", 35))
        box_content.append(hex_color('#ff4a96ff', "║                                                  ║"))
    
    box_content.append(hex_color('#ff4a96ff', "╚══════════════════════════════════════════════════╝"))
    
    return box_content

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_ansi(r, g, b, text):
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"

def hex_color(hex_code, text):
    r, g, b = hex_to_rgb(hex_code)
    return rgb_to_ansi(r, g, b, text)

def display_stats(stats):

    sys.stdout.write("\033[40m")
    
    stats_box = create_stats_box(stats)
    
    term_height = term.height
    term_width = term.width
    box_height = len(stats_box)
    
    box_width = 52
    
    box_y = (term_height - box_height) // 2
    box_x = (term_width - box_width) // 2
    output = ["\033[2J\033[40m\033[H"]
    
    output.extend(["\n" * box_y])
    
    for i, line in enumerate(stats_box):
        padding = " " * box_x
        output.append("\033[{};{}H{}".format(box_y + i, 0, padding + line))
    
    exit_msg = hex_color('#ffffff', "Press 'q' to exit")
    exit_padding = " " * ((term_width - len("Press 'q' to exit")) // 2)
    output.append("\033[{};{}H{}".format(box_y + box_height + 1, 0, exit_padding + exit_msg))

    for i in range(box_y + box_height + 2, term_height):
        output.append("\033[{};{}H{}".format(i, 0, " " * term_width))
    
    print(''.join(output), flush=True)

def process_queue(queue, queue_name, filik, thread_name):
    try:
        if not queue or len(queue) == 0:
            return False
        
        current_task = None
        with queue_lock:
            if len(queue) > 0:
                current_task = queue[0]
                queue.pop(0)
        
        if not current_task:
            return False
        
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
    try:
        with thread_stats_lock:
            if thread_name not in thread_stats:
                thread_stats[thread_name] = 0
            thread_stats[thread_name] += 1
        
        if isinstance(task[1], list):
            local_data = task[1][j]
        else:
            local_data = task[1]
        
        mutated_err_data, mut_type = mutator.mutate(local_data, 100, new_dict2, new_dict)
        
        ind = ind2 = None
        try:
            data_tuple = tuple(task[1])
            if data_tuple in calibrator.info_dict:
                ind = calibrator.info_dict[data_tuple]
                ind2 = calibrator.num + 1
            else:
                ind = calibrator.num + 1
                ind2 = calibrator.num + 2
                calibrator.info_dict[data_tuple] = ind
        except:
            ind = calibrator.num + 1
            ind2 = calibrator.num + 2
            
        xxxx = copy.deepcopy(task)
        if isinstance(task[1], list):
            xxxx[1][j] = mutated_err_data
            if xxxx[1] != task[1]:
                _, nnn, _, _ = calibrator.testing2(config.file_name, xxxx[1])
                with stats_lock:
                    calibrator.info.append([task[1], xxxx[1], ind, ind2, '#ff9cc0', '#ff9cc0', 0, task[0], nnn])
            task[1][j] = mutated_err_data
        else:
            xxxx[1] = mutated_err_data
            if xxxx[1] != task[1]:
                _, nnn, _, _ = calibrator.testing2(config.file_name, xxxx[1])
                with stats_lock:
                    calibrator.info.append([task[1], xxxx[1], ind, ind2, '#ff9cc0', '#ff9cc0', 0, task[0], nnn])
            task[1] = mutated_err_data
        
        task[4] = mut_type
        
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
    counts = {
        "length_ch": 0,
        "xor": 0,
        "ch_symb": 0,
        "interesting": 0
    }
    
    for error_list in [sig_segvi, sig_fpe, no_error]:
        for i in error_list:
            if isinstance(i, list) and len(i) > 4 and i[4] in counts:
                counts[i[4]] += 1
    
    total = sum(counts.values())
    
    if total == 0:
        return [25, 25, 25, 25]
    
    base_prob = 5
    remaining_prob = 100 - (base_prob * 4)
    
    probs = []
    for mut_type in ["length_ch", "xor", "ch_symb", "interesting"]:
        if total > 0:
            prob = base_prob + (counts[mut_type] / total) * remaining_prob
        else:
            prob = 25
        probs.append(round(prob, 1))
    
    total_prob = sum(probs)
    if total_prob != 100:
        probs[-1] += 100 - total_prob
    
    return probs

def restore_terminal():
    sys.stdout.write("\033[0m")
    sys.stdout.flush()
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

old_settings = termios.tcgetattr(sys.stdin)

def fuzzing_thread(thread_name, filik):
    global DEBUG_PROB_OF_MUT, queue_cache
    thread_id = int(thread_name.replace("thread", ""))
    last_prob_update = time.time()
    prob_update_interval = 1.0
    last_queue_check = time.time()
    queue_check_interval = 0.05
    
    local_seg_fault_len = 0
    local_no_error_len = 0
    local_sig_fpe_len = 0
    
    while True:
        try:
            processed = False
            current_time = time.time()
            
            if current_time - last_queue_check >= queue_check_interval:
                local_seg_fault_len = len(calibrator.queue_seg_fault)
                local_no_error_len = len(calibrator.queue_no_error)
                local_sig_fpe_len = len(calibrator.queue_sig_fpe)
                
                with queue_cache_lock:
                    queue_cache['seg_fault'] = local_seg_fault_len
                    queue_cache['no_error'] = local_no_error_len
                    queue_cache['sig_fpe'] = local_sig_fpe_len
                    
                last_queue_check = current_time
                
            if thread_id % 3 == 0:
                if local_seg_fault_len > 0:
                    processed = process_queue(calibrator.queue_seg_fault, "segfault", filik, thread_name)
                elif local_no_error_len > 0:
                    processed = process_queue(calibrator.queue_no_error, "no_error", filik, thread_name)
                elif local_sig_fpe_len > 0:
                    processed = process_queue(calibrator.queue_sig_fpe, "fpe", filik, thread_name)
            elif thread_id % 3 == 1:
                if local_no_error_len > 0:
                    processed = process_queue(calibrator.queue_no_error, "no_error", filik, thread_name)
                elif local_seg_fault_len > 0:
                    processed = process_queue(calibrator.queue_seg_fault, "segfault", filik, thread_name)
                elif local_sig_fpe_len > 0:
                    processed = process_queue(calibrator.queue_sig_fpe, "fpe", filik, thread_name)
            else:
                if local_sig_fpe_len > 0:
                    processed = process_queue(calibrator.queue_sig_fpe, "fpe", filik, thread_name)
                elif local_seg_fault_len > 0:
                    processed = process_queue(calibrator.queue_seg_fault, "segfault", filik, thread_name)
                elif local_no_error_len > 0:
                    processed = process_queue(calibrator.queue_no_error, "no_error", filik, thread_name)
            
            if current_time - last_prob_update >= prob_update_interval:
                with stats_lock:
                    sig_segvi, time_out, no_error, sig_fpe = calibrator.ret_globals()
                    new_probs = define_probability_of_mutations(no_error, sig_segvi, sig_fpe)
                with prob_mut_lock:
                    DEBUG_PROB_OF_MUT = new_probs
                last_prob_update = current_time
            
            if not processed:
                time.sleep(0.005)
            else:
                local_seg_fault_len = max(0, local_seg_fault_len - 1)
                time.sleep(0.0001)
                
        except Exception as e:
            with output_lock:
                filik.write(f"\n[{thread_name}] Error: {str(e)}\n")

def main():
    # Fill screen with black again before starting main program
    fill_screen_black()
    
    global DEBUG_PROB_OF_MUT, start_time, max_coverage_percent
    last_update = time.time()
    update_interval = 0.5
    start_time = time.time()
    max_coverage_percent = 0
    
    with prob_mut_lock:
        DEBUG_PROB_OF_MUT = [25, 25, 25, 25]
    
    tty.setraw(sys.stdin.fileno())
    
    try:
        with open(config.output_file, 'w') as filik:
            with stats_lock:
                if config.FUZZ not in config.args:
                    calibrator.calibrate(copy.deepcopy(config.args), filik, "first_no_mut")
                else:
                    calibrator.calibrate(copy.deepcopy(config.args), filik, "first_no_mut")
            
            threads = []
            for i in range(1, config.NUM_THREADS + 1):
                thread = threading.Thread(
                    target=fuzzing_thread,
                    args=(f'thread{i}', filik),
                    daemon=True
                )
                threads.append(thread)
            
            for thread in threads:
                thread.start()
                time.sleep(0.05)
            
            while True:
                current_time = time.time()
                
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    char = sys.stdin.read(1)
                    if char == 'q':
                        break
                
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
                
                time.sleep(0.05)
            
            with stats_lock:
                sig_segvi, time_out, no_error, sig_fpe = calibrator.ret_globals()
                with output_lock:
                    end_time = time.time()
                    runtime = end_time - start_time
                    total_tests = len(sig_segvi) + len(time_out) + len(no_error) + len(sig_fpe)
                    tests_per_sec = total_tests / runtime if runtime > 0 else 0
                    
                    stats = {
                        'sig_segvi': sig_segvi,
                        'time_out': time_out,
                        'no_error': no_error,
                        'sig_fpe': sig_fpe
                    }
                    best_mutator = get_best_mutator(stats)
                    
                    active_threads = threading.enumerate()
                    active_thread_count = threading.active_count()
                    
                    filik.write(f"-------------------TOTAL-------------------\n\n")
                    filik.write(f"Runtime: {format_time(round(runtime, 1))}\n")
                    filik.write(f"Total Tests Run: {total_tests}\n")
                    filik.write(f"Tests/sec: {round(tests_per_sec, 1)}/s\n")
                    filik.write(f"Configured Threads: {config.NUM_THREADS}\n")
                    filik.write(f"Active Threads: {active_thread_count}\n")
                    
                    filik.write(f"Thread Details:\n")
                    for t in active_threads:
                        thread_status = "active" if t.is_alive() else "inactive"
                        tests_by_thread = thread_stats.get(t.name, 0)
                        thread_efficiency = (tests_by_thread / total_tests * 100) if total_tests > 0 else 0
                        thread_tests_per_sec = tests_by_thread / runtime if runtime > 0 else 0
                        filik.write(f"  {t.name}: {thread_status} (daemon: {t.daemon})\n")
                        if t.name.startswith("thread"):
                            filik.write(f"    Tests completed: {tests_by_thread} ({round(thread_efficiency, 1)}% of total)\n")
                            filik.write(f"    Tests/sec: {round(thread_tests_per_sec, 1)}/s\n")
                    
                    filik.write(f"Max Coverage: {get_coverage()}\n")
                    filik.write(f"Best Mutator: {best_mutator}\n\n")
                    
                    filik.write(f"Error Breakdown:\n")
                    if len(sig_segvi) > 0:
                        filik.write('Segmentation Faults (-11): ' + str(len(sig_segvi)) + '\n')
                    if len(sig_fpe) > 0:
                        filik.write('Floating Point Exceptions: ' + str(len(sig_fpe)) + '\n')
                    if len(time_out) > 0:
                        filik.write('Timeouts: ' + str(len(time_out)) + '\n')
                    if len(no_error) > 0:
                        filik.write('Other Return Codes:\n')
                        for i in calibrator.codes_set:
                            filik.write(f"  Code {i}: {calibrator.codes_dict[i]}\n")
                    filik.write(f"\nFinal Mutation Probabilities:\n")
                    with prob_mut_lock:
                        filik.write(f"  Length Change: {round(DEBUG_PROB_OF_MUT[0], 1)}%\n")
                        filik.write(f"  XOR: {round(DEBUG_PROB_OF_MUT[1], 1)}%\n")
                        filik.write(f"  Symbol Change: {round(DEBUG_PROB_OF_MUT[2], 1)}%\n")
                        filik.write(f"  Interesting: {round(DEBUG_PROB_OF_MUT[3], 1)}%\n")
                    filik.write(f"-------------------------------------------\n\n")
            
            print(colored("\nResults saved to output.txt", "green"))
            
    except Exception as e:
        print(colored(f"\nAn error occurred: {str(e)}", "red"))
    finally:
        restore_terminal()
        sys.exit(0)

def show_welcome_screen():
    fill_screen_black()
    
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
    try:
        selection = show_welcome_screen()
        if selection == 0:
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
                sys.stdout.write("\033[0m")
                sys.stdout.flush()
                print(colored("\nAll results were saved to 'output.txt'", "magenta"))
                print(calibrator.afiget)
            except Exception as e:
                sys.stdout.write("\033[0m")
                sys.stdout.flush()
                print(colored(f"\nAn error occurred: {str(e)}", "red"))
                print(colored("Try resizing your terminal or restarting the fuzzer", "white"))
        else:
            sys.stdout.write("\033[0m")
            sys.stdout.flush()
            print(colored("\nOkay, have a good time, bye! <3", "magenta"))
    finally:
        sys.stdout.write("\033[0m")
        sys.stdout.flush()
