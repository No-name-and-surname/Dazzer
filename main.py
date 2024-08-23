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

TIMEOUT = 1

width_1 = (str(list(get_monitors())[0])[8:].split(', '))[2].split('width=')[1] + 'px'
height_1 = (str(list(get_monitors())[0])[8:].split(', '))[3].split('height=')[1] + 'px'
nt = Network(height_1, width_1,  bgcolor="#111111", font_color="white")
pos = 27
places = []
codes = []
countik = 0
MAX_C = 0
flag = 0
term = Terminal()
dictionary = open(config.dict_name, 'rb').read().decode().split('\r\n')
new_dict, new_dict2 = [], []
x = (term.width - len('Number of tests already sent: ')) // 2
y = (term.height - term.height //2)
temp_up = '---------------------TOTAL---------------------'
temp_bottom = '-----------------------------------------------'
x_1 = (term.width - len(temp_up)) // 2
def main(stdscr):

    stdscr.nodelay(1)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    with open(config.output_file, 'w') as filik:
        if config.FUZZ not in config.args:
            calibrator.calibrate(copy.deepcopy(config.args), filik)
        else:
            calibrator.calibrate(copy.deepcopy(config.args), filik)
        countik = 0
        curses.curs_set(0)
        step = -1
        while True:
            step += 1
            codes, codes_set = [], set()
            places = []
            pos = 27
            key = stdscr.getch()
            for y in range(term.height - 30, term.height - 10):
                stdscr.addch(y, x_1, "|", curses.color_pair(1) | curses.A_BOLD)
            for y in range(term.height - 30, term.height - 10):
                stdscr.addch(y, x_1 + len(temp_up)-1, "|", curses.color_pair(1) | curses.A_BOLD)
            stdscr.refresh()
            stdscr.addstr(term.height - 1, 0, "press <Enter> to exit..", curses.color_pair(1) | curses.A_BOLD)
            stdscr.refresh()
            stdscr.addstr(term.height - 30, x_1, temp_up, curses.color_pair(1) | curses.A_BOLD)
            stdscr.refresh()
            stdscr.addstr(term.height - 10, x_1, temp_bottom, curses.color_pair(1) | curses.A_BOLD)
            stdscr.refresh()
            if len(config.args) == 1:
                for i in dictionary:
                    if step == 0:
                        if i.startswith(config.args[0].lower()) == True:
                            if config.args[0].lower() != config.args[0]:
                                i = list(i)
                                i[0] = i[0].upper()
                                new_dict.append(''.join(i))
                            else:
                                new_dict.append(i)
                        elif config.args[0] in i:
                            new_dict2.append(i)
            sig_segvi, time_out, no_error, sig_fpe = calibrator.ret_globals()
            if len(sig_segvi) != 0 and len(calibrator.queue_seg_fault) != 0:
                if len(sig_segvi) == 1:
                    for i in range(len(sig_segvi)):
                        my_err = copy.deepcopy(calibrator.queue_seg_fault)
                        res = calibrator.no_error_try(i, my_err, filik)
                else:
                    my_err = copy.deepcopy(calibrator.queue_seg_fault)
                    res = calibrator.no_error_try(0, my_err, filik)
                try:
                    if len(calibrator.queue_seg_fault[0][1]) > 1:
                        for j in range(len(calibrator.queue_seg_fault[0][1])):
                            mutated_err_data = mutator.mutate(calibrator.queue_seg_fault[0][1][j], 100, new_dict2, new_dict)
                            try:
                                ind = calibrator.info_dict[tuple(calibrator.queue_seg_fault[0][1])]
                                ind2 = calibrator.num + 1
                            except:
                                ind = calibrator.num + 1
                                ind2 = calibrator.num + 2
                                calibrator.info_dict.update({tuple(calibrator.queue_seg_fault[0][1]):ind})
                            xxxx = copy.deepcopy(calibrator.queue_seg_fault)
                            xxxx[0][1][j] = mutated_err_data
                            if xxxx[0][1] != calibrator.queue_seg_fault[0][1]:
                                calibrator.info.append([calibrator.queue_seg_fault[0][1], xxxx[0][1], ind, ind2, '#ff9cc0', '#ff9cc0', 0])
                            calibrator.queue_seg_fault[0][1][j] = mutated_err_data
                            calibrator.calibrate(calibrator.queue_seg_fault[0][1], filik)

                        calibrator.queue_seg_fault.pop(0)
                    else:
                        rand_symbol = chr(randint(97, 122))
                        mutated_data = mutator.mutate(calibrator.queue_seg_fault[0][1][0], 100, new_dict2, new_dict)
                        try:
                            ind = calibrator.info_dict[tuple(calibrator.queue_seg_fault[0][1])]
                            ind2 = calibrator.num + 1
                        except:
                            ind = calibrator.num + 1
                            ind2 = calibrator.num + 2
                            calibrator.info_dict.update({tuple(calibrator.queue_seg_fault[0][1]):ind})
                        xxxx = copy.deepcopy(calibrator.queue_seg_fault)
                        xxxx[0][1][0] = mutated_data
                        if xxxx[0][1] != calibrator.queue_seg_fault[0][1]:
                            calibrator.info.append([calibrator.queue_seg_fault[0][1], xxxx[0][1], ind, ind2, '#ff9cc0', '#ff9cc0', 0])
                        calibrator.queue_seg_fault[0][1][0] = mutated_data
                        calibrator.calibrate([mutated_data], filik)
                        calibrator.queue_seg_fault.pop(0)
                except:
                    break
            if len(no_error) != 0 or len(sig_fpe) != 0:
                if len(no_error) != 0 and len(calibrator.queue_no_error) != 0:
                    if len(no_error) == 1:
                        for i in range(len(no_error)):
                            my_err = copy.deepcopy(calibrator.queue_no_error)
                            res = calibrator.no_error_try(i, my_err, filik)
                    else:
                        my_err = copy.deepcopy(calibrator.queue_no_error)
                        res = calibrator.no_error_try(0, my_err, filik)
                    if len(calibrator.queue_no_error[0][1]) > 1:
                        for j in range(len(calibrator.queue_no_error[0][1])):
                            mutated_err_data = mutator.mutate(calibrator.queue_no_error[0][1][j], 100, new_dict2, new_dict)
                            try:
                                ind = calibrator.info_dict[tuple(calibrator.queue_no_error[0][1])]
                                ind2 = calibrator.num + 1
                            except:
                                ind = calibrator.num + 1
                                ind2 = calibrator.num + 2
                                calibrator.info_dict.update({tuple(calibrator.queue_no_error[0][1]):ind})
                        xxxx = copy.deepcopy(calibrator.queue_no_error)
                        xxxx[0][1][j] = mutated_err_data
                        if xxxx[0][1] != calibrator.queue_no_error[0][1]:
                            calibrator.info.append([calibrator.queue_no_error[0][1], xxxx[0][1], ind, ind2, '#ff9cc0', '#ff9cc0', 0])
                        calibrator.queue_no_error[0][1][j] = mutated_err_data
                        calibrator.calibrate(calibrator.queue_no_error[0][1], filik)
                        calibrator.queue_no_error.pop(0)
                    else:
                        rand_symbol = chr(randint(97, 122))
                        mutated_data = mutator.mutate(calibrator.queue_no_error[0][1][0], 100, new_dict2, new_dict)
                        try:
                            ind = calibrator.info_dict[tuple(calibrator.queue_no_error[0][1])]
                            ind2 = calibrator.num + 1
                        except:
                            ind = calibrator.num + 1
                            ind2 = calibrator.num + 2
                            calibrator.info_dict.update({tuple(calibrator.queue_no_error[0][1]):ind})
                        xxxx = copy.deepcopy(calibrator.queue_no_error)
                        xxxx[0][1][0] = mutated_data
                        if xxxx[0][1] != calibrator.queue_no_error[0][1]:
                            calibrator.info.append([calibrator.queue_no_error[0][1], xxxx[0][1], ind, ind2, '#ff9cc0', '#ff9cc0', 0])
                        calibrator.queue_no_error[0][1][0] = mutated_data
                        calibrator.calibrate([mutated_data], filik)
                        calibrator.queue_no_error.pop(0)
                    
                else:
                    if len(sig_fpe) == 1 and len(calibrator.queue_sig_fpe) != 0:
                        for i in range(len(sig_fpe)):
                            sig_fpe_1 = copy.deepcopy(calibrator.queue_sig_fpe)
                            res = calibrator.no_error_try(i, sig_fpe_1, filik)
                    else:
                        sig_fpe_1 = copy.deepcopy(calibrator.queue_sig_fpe)
                        res = calibrator.no_error_try(0, sig_fpe_1, filik)
                    if len(calibrator.queue_sig_fpe[0][1]) > 1:
                        for j in range(len(calibrator.queue_sig_fpe[0][1])):
                            mutated_err_data = mutator.mutate(calibrator.queue_sig_fpe[0][1][j], 100, new_dict2, new_dict)
                            try:
                                ind = calibrator.info_dict[tuple(calibrator.queue_sig_fpe[0][1])]
                                ind2 = calibrator.num + 1
                            except:
                                ind = calibrator.num + 1
                                ind2 = calibrator.num + 2
                                calibrator.info_dict.update({tuple(calibrator.queue_sig_fpe[0][1]):ind})
                            xxxx = copy.deepcopy(calibrator.queue_sig_fpe)
                            xxxx[0][1][j] = mutated_err_data
                            calibrator.info.append([calibrator.queue_sig_fpe[0][1], xxxx[0][1], ind, ind2, '#ff9cc0', '#ff9cc0', 0])
                            calibrator.queue_sig_fpe[0][1][j] = mutated_err_data
                            calibrator.calibrate(calibrator.queue_sig_fpe[0][1], filik)
                        calibrator.queue_sig_fpe.pop(0)
                    else:
                        rand_symbol = chr(randint(97, 122))
                        mutated_data = mutator.mutate(calibrator.queue_sig_fpe[0][1][0], 100, new_dict2, new_dict)
                        try:
                            ind = calibrator.info_dict[tuple(calibrator.queue_sig_fpe[0][1])]
                            ind2 = calibrator.num + 1
                        except:
                            ind = calibrator.num + 1
                            ind2 = calibrator.num + 2
                            calibrator.info_dict.update({tuple(calibrator.queue_sig_fpe[0][1]):ind})
                        xxxx = copy.deepcopy(calibrator.queue_sig_fpe)
                        xxxx[0][1][0] = mutated_data
                        calibrator.info.append([calibrator.queue_sig_fpe[0][1], xxxx[0][1], ind, ind2, '#ff9cc0', '#ff9cc0', 0])
                        calibrator.queue_sig_fpe[0][1][0] = mutated_data
                        calibrator.calibrate([mutated_data], filik)
                        calibrator.queue_sig_fpe.pop(0)

            if key == 10:
                filik.write(f"-------------------TOTAL-------------------\n\n\n")
                if len(sig_segvi) > 0:
                    filik.write('with -11: ' + str(len(sig_segvi)) + '\n\n\n')
                if len(sig_fpe) > 0:
                    filik.write('with -8: ' + str(len(sig_fpe)) + '\n\n\n')
                if len(no_error) > 0:
                    for i in calibrator.codes_set:
                        filik.write(f"with {i}: " + str(calibrator.codes_dict[i]) + '\n\n\n')
                if len(calibrator.list_not_imp_tests) > 0:
                    for i in calibrator.codes_set1:
                        filik.write(f"with {i}: " + str(calibrator.codes_dict1[i]) + '\n\n\n')

                filik.write(f"-------------------------------------------\n\n\n")
                flag = 1
                break
            else:
                co = 0
                x_pos = (term.width - len(temp_up)) // 2 + 5
                sig_segvi, time_out, no_error, sig_fpe = calibrator.ret_globals()
                pos = 27
                if len(sig_segvi) > 0:
                    stdscr.addstr(term.height - pos, x_pos, 'with -11: ' + str(len(sig_segvi)), curses.A_BOLD)
                    places.append(pos)
                    stdscr.refresh()
                if len(sig_fpe) > 0:
                    pos -= len(places)
                    stdscr.addstr(term.height - pos, x_pos, 'with -8: ' + str(len(sig_fpe)), curses.A_BOLD)
                    places.append(pos)
                    stdscr.refresh()
                if len(no_error) > 0:
                    for i in calibrator.codes_set:
                        pos -= len(places)
                        stdscr.addstr(term.height - pos, x_pos, f"with {i}: " + str(calibrator.codes_dict[i]), curses.A_BOLD)
                        places.append(pos)
                        stdscr.refresh()
                        countik = 0
                color_const = '#c9024b'
if __name__ == '__main__':
    print("Hi, i hope you've already read README, but here is some info that should be useful:\n")
    time.sleep(0.4)
    print("After you read this text, you'll see frame.")
    time.sleep(0.2)
    print("In this frame the results of the fuzzing will be displayed.")
    time.sleep(0.2)
    print("Btw, they will change dynamically.")
    time.sleep(0.2)
    print("Type 'c' to start fuzzing")
    if input() == 'c':
        # try:
        #     curses.wrapper(main)
        #     print("All results were saved to 'output.txt'")
        # except:
        #     if flag == 0:
        #         print("Oh, here's some error, try to resize your terminal (like: Ctrl+Shift+'-' or  Ctrl+Shift+'+') or restart fuzzer")
        #     else:
        #         print("All results were saved to 'output.txt'")
        curses.wrapper(main)

        for i in copy.deepcopy(calibrator.info):
            src, dst = i[0], i[1]
            if i[6] == 0: 
                nt.add_node(i[2], str(src), color=i[4], title=str(src))
                nt.add_node(i[3], str(dst), color=i[5], title=str(dst))
                nt.add_edge(i[2], i[3], weight=5)
                i[6] = 1
        nt.show('nx.html', notebook=False)
    else:
        print("It doesn't look like 'c'...")
        print("Okay, have a good time, bye! <3")
