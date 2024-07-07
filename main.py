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

TIMEOUT = 1
 
codes = []
settic = set()
countik = 0
global MAX_C
MAX_C = 0
glob_fl = 0
Grwq = 0
term = Terminal()
filei = open(config.dict_name, 'rb').read().decode().split('\r\n')
new_dict, new_dict2 = [], []
x = (term.width - len('Number of tests already sent: ')) // 2
y = (term.height - term.height //2)
temp = '---------------------TOTAL---------------------'
temp_1 = '-----------------------------------------------'
x_1 = (term.width - len(temp)) // 2
def main(stdscr):
    stdscr.nodelay(1)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    with open(config.output_file, 'w') as filik:
        if config.FUZZ not in config.args:
            calibrator.calibrate(copy.deepcopy(config.args), filik)
            calibrator.results_asd()
        else:
            print('So here it is: ')
            calibrator.calibrate(copy.deepcopy(config.args), filik)
        countik = 0
        curses.curs_set(0)  # Скрыть курсор
        for gfg in range(1000):
            key = stdscr.getch()
            for y in range(term.height - 30, term.height - 10):
                stdscr.addch(y, x_1, "|", curses.color_pair(1) | curses.A_BOLD)
            for y in range(term.height - 30, term.height - 10):
                stdscr.addch(y, x_1 + len(temp)-1, "|", curses.color_pair(1) | curses.A_BOLD)
            stdscr.refresh()
            stdscr.addstr(term.height - 1, 0, "press <Enter> to exit..", curses.color_pair(1) | curses.A_BOLD)
            stdscr.refresh()
            # stdscr.addstr(term.height // 2, (term.width - len("Текущее значение: {}".format(gfg))) // 2, "Текущее значение: {}".format(gfg))
            # stdscr.refresh()
            stdscr.addstr(term.height - 30, x_1, temp, curses.color_pair(1) | curses.A_BOLD)
            stdscr.refresh()
            stdscr.addstr(term.height - 10, x_1, temp_1, curses.color_pair(1) | curses.A_BOLD)
            stdscr.refresh()
            if len(config.args) == 1:
                for i in filei:
                    if gfg == 0:
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
            # with term.location(x, y):
            #     time.sleep(0.5)
            #     print('Number of tests already sent: {}'.format(bb), end='\b')
            if len(sig_segvi) != 0:
                for i in range(len(sig_segvi)):
                    res = calibrator.seg_segv(i)
                    try:
                        MAX_C = res[i][2]-2
                    except:
                        MAX_C = MAX_C
                for i in range(len(sig_segvi)):
                    f = chr(randint(97, 122))
                    try:
                        if len(res[i][3]) > 1:
                            for j in range(len(res[i][3])):
                                nn = mutator.mutate(f, MAX_C, new_dict2, new_dict)
                                res[i][3][j] = nn
                                calibrator.calibrate(res[i][3], filik)
                        else:
                            mm = mutator.mutate(f, MAX_C, new_dict2, new_dict)
                            calibrator.calibrate([mm], filik)
                    except:
                        break
                    calibrator.results_asd()
            elif len(no_error) != 0 or len(sig_fpe) != 0:
                if len(no_error) != 0:
                    for i in range(len(no_error)):
                        my_err = copy.deepcopy(no_error)
                        res = calibrator.no_error_try(i, my_err)
                    calibrator.results_asd()
                    for i in range(len(my_err)):
                        if len(my_err[i][1]) > 1:
                            for j in range(len(my_err[i][1])):
                                f = chr(randint(97, 122))
                                nn = mutator.mutate(f, 100, new_dict2, new_dict)
                                my_err2 = copy.deepcopy(my_err)
                                my_err2[i][1][j] = nn
                                calibrator.calibrate(my_err2[i][1], filik)
                        else:
                            f = chr(randint(97, 122))
                            mm = mutator.mutate(f, 100, new_dict2, new_dict)
                            calibrator.calibrate([mm], filik)
                    calibrator.results_asd()
                else:
                    for i in range(len(sig_fpe)):
                        sig_fpe_1 = copy.deepcopy(sig_fpe)
                        res = calibrator.no_error_try(i, sig_fpe_1)
                    calibrator.results_asd()
                    for i in range(len(sig_fpe_1)):
                        if len(sig_fpe_1[i][1]) > 1:
                            for j in range(len(sig_fpe_1[i][1])):
                                f = chr(randint(97, 122))
                                nn = mutator.mutate(f, 100, new_dict2, new_dict)
                                sig_fpe_2 = copy.deepcopy(sig_fpe_1)
                                sig_fpe_2[i][1][j] = nn
                                calibrator.calibrate(sig_fpe_2[i][1], filik)
                        else:
                            f = chr(randint(97, 122))
                            mm = mutator.mutate(f, 100, new_dict2, new_dict)
                            calibrator.calibrate([mm], filik)
                    calibrator.results_asd()
            try:
                if key == 10 or gfg == 999:
                    sig_segvi, time_out, no_error, sig_fpe = calibrator.ret_globals()
                    filik.write(f"-------------------TOTAL-------------------\n\n\n")
                    if len(sig_segvi) > 0:
                        filik.write('with -11: ' + str(len(sig_segvi)) + '\n\n\n')
                    if len(sig_fpe) > 0:
                        filik.write('with -8: ' + str(len(sig_fpe)) + '\n\n\n')
                    if len(no_error) > 0:
                        for i in no_error:
                            codes.append(i[0])
                            settic.add(i[0])
                        for i in settic:
                            for j in codes:
                                if j == i:
                                    countik += 1
                            filik.write(f"with {i}: " + str(countik) + '\n\n\n')
                            countik = 0
                    filik.write(f"-------------------------------------------\n\n\n")
                    glob_fl = 1
                    break  # Выход из цикла
                else:
                    co = 0
                    xik = (term.width - len(temp)) // 2 + 5
                    sig_segvi, time_out, no_error, sig_fpe = calibrator.ret_globals()
                    if len(sig_segvi) > 0:
                        stdscr.addstr(term.height - 27, xik, 'with -11: ' + str(len(sig_segvi)), curses.A_BOLD)
                        stdscr.refresh()
                    if len(sig_fpe) > 0:
                        stdscr.addstr(term.height - 25, xik, 'with -8: ' + str(len(sig_fpe)), curses.A_BOLD)
                        stdscr.refresh()
                    if len(no_error) > 0:
                        for i in no_error:
                            codes.append(i[0])
                            settic.add(i[0])
                        for i in settic:
                            co += 1
                            for j in codes:
                                if j == i:
                                    countik += 1
                            stdscr.addstr(term.height - 23 + co, xik, f"with {i}: " + str(countik), curses.A_BOLD)
                            stdscr.refresh()
                            countik = 0
                    filik.write(f"-------------------------------------------\n\n\n")
            except:
                break

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
    try:
        curses.wrapper(main)
        print("All results were saved to 'output.txt'")
    except:
        if glob_fl == 0:
            print("Oh, here's some error, try to resize your terminal (like: Ctrl+Shift+'-' or  Ctrl+Shift+'+') or restart fuzzer")
        else:
            print("All results were saved to 'output.txt'")
else:
    print("It doesn't look like 'c'...")
    print("Okay, have a good time, bye! <3")
