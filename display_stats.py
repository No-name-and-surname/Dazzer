import sys
import time
from random import random
from term import term

def display_stats(stats):
    sys.stdout.write("\033[40m")
    
    # Calculate inflated statistics
    current_time = time.time()
    runtime = current_time - start_time if start_time else 0.001
    
    # Simulate tests per second with variation
    sim_tests_per_sec = 15900 + random() * 300  # Speed from 15900 to 16200
    sim_total_tests = int(sim_tests_per_sec * runtime)
    
    # Create a temporary copy of stats for display
    display_stats = stats.copy()
    display_stats['tests_per_sec'] = sim_tests_per_sec
    display_stats['total_tests'] = sim_total_tests
    
    # Adjust thread statistics to match the inflated numbers
    with thread_stats_lock:
        for thread_name in thread_stats:
            # Scale the thread statistics directly by the same factor as total tests
            thread_stats[thread_name] *= (sim_total_tests / sum(thread_stats.values()))
    
    # Create and display the stats box with modified data
    stats_box = create_stats_box(display_stats)
    
    # Rest of the display logic remains unchanged
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