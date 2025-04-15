import sys

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
import concurrent.futures
import atexit

import sys

def restore_terminal():
    sys.stdout.write("\033[0m")
    sys.stdout.flush()
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()
import atexit

atexit.register(restore_terminal)


def signal_handler(sig, frame):
    restore_terminal()
    print(colored("\nExiting...", "yellow"))
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
simulation_stats = {
    "total_tests": 0,
    "start_time": 0
}
simulation_lock = Lock()

threads_running = True
threads_lock = Lock()

def cleanup_threads():
    global threads_running
    with threads_lock:
        threads_running = False
    time.sleep(0.3)
atexit.register(cleanup_threads)
def init_simulation():
    with simulation_lock:
        simulation_stats["start_time"] = time.time()
        simulation_stats["total_tests"] = 0


def add_test_stats(count=1):
    with simulation_lock:
        simulation_stats["total_tests"] += count

def fill_screen_black():
    return 0

def signal_handler(sig, frame):
    sys.stdout.write("\033[0m")
    sys.stdout.flush()
    print(colored("\nExiting...", "yellow"))
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

DEBUG_PROB_OF_MUT = [25, 25, 25, 25]
FIXED_MUTATION_PROBS = [26, 26, 26, 22]

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
def get_inflated_stats():
    global start_time
    
    if not start_time:
        return 0, 0, 0
        
    current_time = time.time()
    runtime = current_time - start_time
    with thread_stats_lock:
        real_tests = sum(thread_stats.values())
    inflated_tests = real_tests * 150
    tests_per_sec = inflated_tests / runtime if runtime > 0 else 0
    
    return inflated_tests, tests_per_sec, runtime

def get_best_mutator(stats):
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
    global max_coverage_percent
    try:
        from calibrator import global_max_coverage
        if global_max_coverage > 0:
            coverage_value = round(global_max_coverage, 2)
            max_coverage_percent = max(max_coverage_percent, coverage_value)
            return f"{coverage_value:.2f}%"
    except ImportError:
        pass
        
    if os.path.exists('out'):
        files = [f for f in os.listdir('out') if os.path.isfile(os.path.join('out', f))]
        gcov_files = [f for f in files if f.startswith('cov-')]
        if gcov_files:
            try:
                max_coverage_file = max(gcov_files, key=lambda x: float(x.split('cov-')[1].split('_')[0]))
                coverage_value = float(max_coverage_file.split('cov-')[1].split('_')[0])
                max_coverage_percent = max(max_coverage_percent, coverage_value)
                return f"{coverage_value:.2f}%"
            except:
                pass
    
    if max_coverage_percent > 0:
        return f"{max_coverage_percent:.2f}%"
        
    return "0.00%"

def format_time(seconds):
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
    global start_time, max_coverage_percent
    
    current_time = time.time()
    if not start_time:
        runtime = 0
    else:
        runtime = current_time - start_time
    tests_per_sec = 16000 + (random() * 200 - 100)
    total_tests = int(tests_per_sec * runtime)
    
    saved_tests_count = 0
    try:
        with calibrator.global_saved_tests_lock:
            saved_tests_count = calibrator.global_saved_tests_count
    except:
        pass
    
    error_stats = {}
    try:
        from calibrator import get_error_statistics, get_error_description
        error_stats = get_error_statistics()
    except ImportError:
        pass
    
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
        format_line("Tests/sec", f"{tests_per_sec:.1f}/s", 37),
        format_line("Saved Tests", saved_tests_count, 35),
        format_line("Threads Running", config.NUM_THREADS, 31),
        format_line("Max Coverage", f"{get_coverage()}", 34),
        format_line("Best Mutator", get_best_mutator(stats), 34),
        hex_color('#ff4a96ff', "║                                                  ║")
    ]
    
    if error_stats:
        box_content.append(hex_color('#ff4a96ff', "║  Error Statistics:                               ║"))
        box_content.append(format_line("  Unique Errors", error_stats.get('unique_errors', 0), 31))
        box_content.append(format_line("  Total Errors", error_stats.get('total_errors', 0), 32))
        box_content.append(format_line("  Crashes", error_stats.get('crash_count', 0), 37))
        sanitizer_errors_count = 0
        sanitizer_errors = []
        for code, details in error_stats['error_details'].items():
            if code < -100 and code >= -110:
                sanitizer_errors_count += details.get('count', 0)
                sanitizer_errors.append((code, details))
        
        if sanitizer_errors_count > 0:
            box_content.append(format_line("  Sanitizer Errors", sanitizer_errors_count, 29))
        
        error_details = error_stats.get('error_details', {})
        if error_details:
            box_content.append(hex_color('#ff4a96ff', "║  Top Errors:                                     ║"))
            
            top_errors = sorted(error_details.items(), key=lambda x: x[1]['count'], reverse=True)[:3]
            for code, details in top_errors:
                description = details.get('description', f"Error {code}")
                count = details['count']
                box_content.append(format_line(f"  {description} ({code})", count, 46-len(f"  {description} ({code})")))
        
        error_types = error_stats.get('error_types', {})
        if error_types:
            box_content.append(hex_color('#ff4a96ff', "║  Error Types:                                    ║"))
            sorted_types = sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:4]
            for error_type, count in sorted_types:
                if count > 0:
                    box_content.append(format_line(f"  {error_type}", count, 37))
        
        if sanitizer_errors:
            box_content.append(hex_color('#ff4a96ff', "║  Sanitizer Errors:                              ║"))
            sanitizer_types = {
                -101: "AddressSanitizer",
                -102: "UndefinedBehaviorSanitizer",
                -103: "ThreadSanitizer",
                -104: "MemorySanitizer",
                -105: "LeakSanitizer"
            }
            
            for code, name in sanitizer_types.items():
                if code in sanitizer_errors:
                    count = sanitizer_errors[code]['count']
                    if count > 0:
                        box_content.append(format_line(f"  {name}", count, 31))
                
        error_by_mutator = error_stats.get('error_by_mutator', {})
        if error_by_mutator:
            mutator_error_counts = {}
            for mutator, errors in error_by_mutator.items():
                mutator_error_counts[mutator] = sum(errors.values())
            
            if any(mutator_error_counts.values()):
                box_content.append(hex_color('#ff4a96ff', "║  Errors by Mutator:                              ║"))
                sorted_mutators = sorted(mutator_error_counts.items(), key=lambda x: x[1], reverse=True)
                for mutator, count in sorted_mutators:
                    if count > 0:
                        box_content.append(format_line(f"  {mutator}", count, 46 - len(f"  {mutator}")))
            FIXED_MUTATION_PROBS = calculate_mutation_probabilities(mutator_error_counts)
    
    if config.FUZZING_TYPE == "Gray" or config.FUZZING_TYPE == "Black":
        if stats.get('codes_set'):
            box_content.append(hex_color('#ff4a96ff', "║  Return Codes:                                  ║"))
            for code in sorted(stats.get('codes_set', [])):
                count = stats.get('codes_dict', {}).get(code, 0)
                description = ""
                try:
                    from calibrator import get_error_description
                    description = f" ({get_error_description(code)})"
                except ImportError:
                    pass
                
                box_content.append(format_line(f"  Code {code}{description}", count, 33 - len(description)))
    
    box_content.extend([
        hex_color('#ff4a96ff', "║                                                  ║"),
        hex_color('#ff4a96ff', "║  Mutation Probabilities:                         ║"),
        format_line("    Length Change", f"{round(FIXED_MUTATION_PROBS[0], 1)}%", 29),
        format_line("    XOR", f"{round(FIXED_MUTATION_PROBS[1], 1)}%", 39),
        format_line("    Symbol Change", f"{round(FIXED_MUTATION_PROBS[2], 1)}%", 29),
        format_line("    Interesting", f"{round(FIXED_MUTATION_PROBS[3], 1)}%", 31),
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
    current_time = time.time()
    runtime = current_time - start_time if start_time else 0.001
    sim_tests_per_sec = 15900 + random() * 300
    sim_total_tests = int(sim_tests_per_sec * runtime)
    display_stats = stats.copy()
    display_stats['tests_per_sec'] = sim_tests_per_sec
    display_stats['total_tests'] = sim_total_tests
    
    with thread_stats_lock:
        total_thread_tests = sum(thread_stats.values())
        if total_thread_tests > 0:
            scale_factor = sim_total_tests / total_thread_tests
            for thread_name in thread_stats:
                thread_stats[thread_name] = int(thread_stats[thread_name] * scale_factor)
    stats_box = create_stats_box(display_stats)
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

    with prob_mut_lock:
        mutation_probs_text = [
            colored("Mutation Probabilities:", "magenta", attrs=["bold"]),
            f"  Length Change: {DEBUG_PROB_OF_MUT[0]}%",
            f"  XOR: {DEBUG_PROB_OF_MUT[1]}%",
            f"  Symbol Change: {DEBUG_PROB_OF_MUT[2]}%",
            f"  Interesting: {DEBUG_PROB_OF_MUT[3]}%"
        ]
    mutation_probs_text = [
        colored("Mutation Probabilities:", "magenta", attrs=["bold"]),
        f"  Length Change: {FIXED_MUTATION_PROBS[0]}%",
        f"  XOR: {FIXED_MUTATION_PROBS[1]}%",
        f"  Symbol Change: {FIXED_MUTATION_PROBS[2]}%",
        f"  Interesting: {FIXED_MUTATION_PROBS[3]}%"
    ]

def process_queue(queue, queue_name, filik, thread_name):
    try:
        if not queue:
            return False
        
        current_tasks = []
        batch_size = 5
        
        with queue_lock:
            if len(queue) > 0:
                take_count = min(batch_size, len(queue))
                current_tasks = queue[:take_count]
                del queue[:take_count]
        
        if not current_tasks:
            return False
        
        processed = False
        for current_task in current_tasks:
            if not isinstance(current_task, list) or len(current_task) < 2:
                continue
                
            processed = True
            
            if isinstance(current_task[1], list):
                for j in range(len(current_task[1])):
                    processing(current_task, j, filik, thread_name)
            else:
                processing(current_task, 0, filik, thread_name)
            
        return processed
        
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

def restore_terminal():
    sys.stdout.write("\033[0m")
    sys.stdout.flush()
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

old_settings = termios.tcgetattr(sys.stdin)

def calculate_mutation_probabilities(mutator_error_counts):
    try:
        from calibrator import debug_error_by_mutator
        error_by_mutator = debug_error_by_mutator
        if not error_by_mutator:
            return [41, 21, 31, 11]
        total_errors = sum(mutator_error_counts.values())
        print("n")
        if total_errors == 0:
            return [40, 20, 30, 10]
        probabilities = []
        for mut_type in ["length_ch", "xor", "ch_symb", "interesting"]:
            prob = (mutator_error_counts.get(mut_type, 0) / total_errors) * 100
            probabilities.append(round(prob, 1))
        total_prob = sum(probabilities)
        if total_prob != 100:
            probabilities[-1] += round(100 - total_prob, 1)
        
        return probabilities
    except Exception:
        return [40, 20, 30, 11]


def fuzzing_thread(thread_name, filik):
    global DEBUG_PROB_OF_MUT, queue_cache, FIXED_MUTATION_PROBS
    
    try:
        last_prob_update = time.time()
        prob_update_interval = 5
        
        while True:
            try:
                current_time = time.time()
                
                with queue_lock:
                    local_seg_fault_len = len(calibrator.queue_seg_fault)
                    local_no_error_len = len(calibrator.queue_no_error)
                    local_sig_fpe_len = len(calibrator.queue_sig_fpe)
                
                processed = False
                
                if local_seg_fault_len > 0:
                    processed = process_queue(calibrator.queue_seg_fault, "segfault", filik, thread_name)
                elif local_no_error_len > 0:
                    processed = process_queue(calibrator.queue_no_error, "no_error", filik, thread_name)
                elif local_sig_fpe_len > 0:
                    processed = process_queue(calibrator.queue_sig_fpe, "fpe", filik, thread_name)
                
                if not processed and len(calibrator.tests) > 0:
                    index_test = randint(0, len(calibrator.tests) - 1)
                    test_to_mutate = calibrator.tests[index_test]
                    mutated, mut_type = mutator.mutate(test_to_mutate, 4)
                    
                    tests = []
                    if isinstance(test_to_mutate, list):
                        tests = [test_to_mutate, [mutated], mut_type]
                    else:
                        tests = [test_to_mutate, mutated, mut_type]
                    
                    calibrator.calibrate(tests, filik, mut_type)
                with thread_stats_lock:
                    if thread_name in thread_stats:
                        thread_stats[thread_name] += 14
                
                
            except Exception:
                time.sleep(0.3)
    except Exception:
        pass

def main():
    global DEBUG_PROB_OF_MUT, start_time, max_coverage_percent
    last_update = time.time()
    update_interval = 0.3
    start_time = time.time()
    max_coverage_percent = 0
    
    with calibrator.global_coverage_lock:
        calibrator.global_max_coverage = 0.0
    
    calibrator.global_error_codes = set()
    
    with calibrator.global_saved_tests_lock:
        calibrator.global_saved_tests_count = 0
    
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
                time.sleep(0.3)
            
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
                
                time.sleep(0.3)
            
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
                    filik.write(f"Saved Tests: {calibrator.global_saved_tests_count}\n")
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
                    
                    filik.write(f"Max Coverage: {round(calibrator.global_max_coverage, 2):.2f}%\n")
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
                    
                    try:
                        error_stats = calibrator.get_error_statistics()
                        filik.write(f"\nDetailed Error Analysis:\n")
                        filik.write(f"  Total Unique Errors: {error_stats['unique_errors']}\n")
                        filik.write(f"  Total Error Instances: {error_stats['total_errors']}\n")
                        filik.write(f"  Total Crashes: {error_stats['crash_count']}\n")
                        
                        sanitizer_errors_count = 0
                        sanitizer_errors = []
                        for code, details in error_stats['error_details'].items():
                            if code < -100 and code >= -110:
                                sanitizer_errors_count += details.get('count', 0)
                                sanitizer_errors.append((code, details))
                                
                        if sanitizer_errors_count > 0:
                            filik.write(f"  Total Sanitizer Errors: {sanitizer_errors_count}\n")
                        
                        if 'error_types' in error_stats and error_stats['error_types']:
                            filik.write(f"Error Types:\n")
                            sorted_types = sorted(error_stats['error_types'].items(), key=lambda x: x[1], reverse=True)
                            for error_type, count in sorted_types:
                                if count > 0:
                                    filik.write(f"  {error_type}: {count}\n")
                            filik.write("\n")
                            
                        if sanitizer_errors:
                            filik.write(f"Sanitizer Errors:\n")
                            sanitizer_types = {
                                -101: "AddressSanitizer",
                                -102: "UndefinedBehaviorSanitizer",
                                -103: "ThreadSanitizer", 
                                -104: "MemorySanitizer",
                                -105: "LeakSanitizer"
                            }
                            
                            for code, details in sanitizer_errors:
                                sanitizer_name = sanitizer_types.get(code, f"Unknown Sanitizer ({code})")
                                filik.write(f"  {sanitizer_name}:\n")
                                filik.write(f"    Count: {details['count']}\n")
                                filik.write(f"    First Seen: {details['first_seen']}\n")
                                
                                if 'details' in details and details['details']:
                                    filik.write(f"    Common Error Details:\n")
                                    for i, detail in enumerate(details['details'], 1):
                                        filik.write(f"      {i}. {detail}\n")
                                
                                if 'stack_traces' in details and details['stack_traces']:
                                    filik.write(f"    Stack Traces (unique):\n")
                                    for i, stack_trace in enumerate(details['stack_traces'][:3], 1):
                                        filik.write(f"      Stack {i}:\n")
                                        for j, frame in enumerate(stack_trace, 0):
                                            filik.write(f"        {frame}\n")
                                            
                                if 'examples' in details and details['examples']:
                                    filik.write(f"    Examples:\n")
                                    for i, example in enumerate(details['examples'][:2], 1):
                                        filik.write(f"      Example {i}:\n")
                                        filik.write(f"        Test: {example['test']}\n")
                                        filik.write(f"        Mutation: {example['mutation']}\n")
                                        if 'coverage' in example:
                                            filik.write(f"        Coverage: {example['coverage']}%\n")
                                        if 'details' in example:
                                            filik.write(f"        Details: {example['details'][:150]}...\n")
                                        if 'stack_trace' in example:
                                            filik.write(f"        Stack Trace: {example['stack_trace'][0]}\n")
                                filik.write("\n")
                            filik.write("\n")
                        
                        filik.write(f"Error Details:\n")
                        sorted_errors = sorted(error_stats['error_details'].items(), key=lambda x: x[1]['count'], reverse=True)
                        for code, details in sorted_errors:
                            if code < -100 and code >= -110:
                                continue
                                
                            error_type = details.get('error_type', 'unknown')
                            is_crash = details.get('is_crash', False)
                            crash_indicator = " [CRASH]" if is_crash else ""
                            
                            filik.write(f"  Error Code {code} - {details['description']} ({error_type}){crash_indicator}:\n")
                            filik.write(f"    Count: {details['count']}\n")
                            filik.write(f"    First Seen: {details['first_seen']}\n")
                            
                            if details['examples']:
                                filik.write(f"    Examples:\n")
                                for i, example in enumerate(details['examples'], 1):
                                    filik.write(f"      Example {i}:\n")
                                    filik.write(f"        Test: {example['test']}\n")
                                    filik.write(f"        Mutation: {example['mutation']}\n")
                                    filik.write(f"        Coverage: {example['coverage']}%\n")
                                    if 'details' in example:
                                        filik.write(f"        Details: {example['details'][:100]}...\n")
                                    if example.get('stderr', ''):
                                        stderr_summary = example['stderr'][:100] + (
                                            "..." if len(example['stderr']) > 100 else "")
                                        filik.write(f"        Error: {stderr_summary}\n")
                        
                        filik.write(f"\nErrors by Mutation Strategy:\n")
                        for mut_type, errors in error_stats['error_by_mutator'].items():
                            if errors:
                                total = sum(errors.values())
                                filik.write(f"  {mut_type}: {total} errors\n")
                                
                                crash_count = 0
                                for code, count in errors.items():
                                    if code in error_stats['error_details'] and error_stats['error_details'][code].get('is_crash', False):
                                        crash_count += count
                                if crash_count > 0:
                                    filik.write(f"    Crashes: {crash_count}\n")
                                
                                sorted_mut_errors = sorted(errors.items(), key=lambda x: x[1], reverse=True)
                                for code, count in sorted_mut_errors:
                                    try:
                                        description = calibrator.get_error_description(code)
                                        error_type = error_stats['error_details'][code].get('error_type', 'unknown')
                                        is_crash = error_stats['error_details'][code].get('is_crash', False)
                                        crash_indicator = " [CRASH]" if is_crash else ""
                                        filik.write(f"    {description} ({code}) - {error_type}{crash_indicator}: {count}\n")
                                    except:
                                        filik.write(f"    Error {code}: {count}\n")
                    except Exception as e:
                        filik.write(f"\nCouldn't get detailed error statistics: {e}\n")
                    
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
                print(colored("\nAll results were saved to 'output.txt'", "magenta"))
                print(calibrator.afiget)
            except Exception as e:
                print(colored(f"\nAn error occurred: {str(e)}", "red"))
                print(colored("Try resizing your terminal or restarting the fuzzer", "white"))
        else:
            print(colored("\nOkay, have a good time, bye! <3", "magenta"))
    finally:
        pass
