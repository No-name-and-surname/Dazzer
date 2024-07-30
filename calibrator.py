import subprocess
import time
import statistics
import config
import mutator
import copy
from random import *

symbols_list = list("1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'!@#$%^&*()?><\|/:;~,.}{[]")
tests = copy.deepcopy(config.args)
outputich = []
sig_segv, time_out, no_err, sig_fpe = [], [], [], []
file_name = config.file_name
fileik = open('dict.txt', 'rb').read().decode().split('\r\n')
new_dict, new_dict2 = [], []

def testing(file_name, listik):
    p = ''.join(listik)
    start_time = time.time()
    try:
        result = subprocess.run([file_name], input=p, capture_output=True, text=True, timeout=5)
        end_time = time.time()
        exec_time = end_time - start_time
        # print(result.returncode, result.stdout)
        return exec_time, result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return float('inf'), -1, "", "Timeout"
    except subprocess.CalledProcessError:
        return float('inf'), -1, "", "Called_error"

def ret_globals():
    return sig_segv, time_out, no_err, sig_fpe

def check_no_error(list_of_inp, started_out):
    exec_time, returncode, stdout, stderr = testing(file_name, list_of_inp)
    if stdout == started_out:
        return [False, '', '']
    else:
        return [True, stdout, returncode]
    
def check_seg_segv(list_of_inp):
    exec_time, returncode, stdout, stderr = testing(file_name, list_of_inp)
    if returncode == -11:
        # print(exec_time, returncode, stdout, stderr)
        return [False, '', '']
    else:
        return [True, stdout, returncode]
    
def send_inp(file_name, i, testiki, read_count, filik):
    if i == 1:
        tests_2 = copy.deepcopy(tests)
    else:
        tests_2 = copy.deepcopy(testiki)
    # print(tests_2)
    file_times = []
    listik = []
    file_results = []
    forik = 0
    nn = ''
    times = []
    results = []
    read_count = 0
    strace_command = ["strace", file_name]
    f = chr(randint(97, 122))
    try:
        with subprocess.Popen(strace_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE) as process:        
            read_count = 0  
            for line in process.stderr:
                if 'read(' in line.decode():
                    try:
                        if tests_2[read_count] == config.FUZZ:
                            nn = mutator.mutate(f, 100)
                            f = nn
                            process.stdin.write(f.encode())
                            tests_2[read_count] = f
                            read_count += 1
                            process.stdin.flush()
                        else:
                            process.stdin.write(tests_2[read_count].encode())
                            read_count += 1
                            process.stdin.flush()
                    except:
                        break
    except:
        return
    exec_time, returncode, stdout, stderr = testing(file_name, tests_2)
    if returncode == -11:
        sig_segv.append([returncode, tests_2, read_count, stdout])
        filik.write("test: (" + ',    '.join(tests_2) + ')' + ' '+ str(returncode) + ' ' + str(read_count) + '\n\n\n')
        read_count = 0
    elif returncode == -8:
        sig_fpe.append([returncode, tests_2, read_count, stdout])
        filik.write("test: (" + ',    '.join(tests_2) + ')' +  ' '+ str(returncode) + ' ' + str(read_count) + '\n\n\n')
        read_count = 0
    elif line == -1:
        time_out.append([returncode, tests_2, read_count, stdout])
        filik.write("test: (" + ',    '.join(tests_2) + ')'  + ' '+ str(returncode) + ' ' + str(read_count) + '\n\n\n')
        read_count = 0
    else:
        no_err.append([returncode, tests_2, read_count, stdout])
        filik.write("test: (" + ',    '.join(tests_2) + ')'  + ' '+ str(returncode) + ' ' +  str(read_count) + '\n\n\n')
        read_count = 0
    file_times.append(exec_time)
    file_results.append((returncode, stdout, stderr))
    average_time = statistics.mean(file_times)
    times.append(average_time)
    results.append(file_results)
    read_count = 0
    forik = 0

def calibrate(testiki, filik):
    times = []
    results = []
    c_c = 0
    if config.FUZZ in tests:
        while True:
            c_c += 1
            read_count = 0
            send_inp(file_name, 1, testiki, read_count, filik)
            print(str(c_c) + "'s cycle")
    else:
        read_count = 0
        send_inp(file_name, 0, testiki, read_count, filik)
        
    return times, results

def no_error_try(index, mas):
    count = 0
    flagik = 0
    res = []
    rand_num = rand_num = randint(0, 87)
    for i in mas[index][1]:
        started_i = i
        started_out = mas[index][2]
        for j in range(len(symbols_list)):
            # print(i[:-1])
            if i[:-1] in '1234567890':
                # print('Our i:', i[:-1])
                rand_num = randint(10, 61)
            elif i[:-1] in 'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM':
                # print('Our i:', i[:-1])
                rand_num = randint(62, 87)
                # print(symbols_list[rand_num])
            elif i[:-1] in "'!@#$%^&*()?><\|/:;~,.}{[]":
                # print('Our i:', i[:-1])
                rand_num = randint(0, 9)
            i = symbols_list[rand_num] + '\n'
            # print(i)
            mas[index][1][count] = i
            Check = copy.deepcopy(check_no_error(mas[index][1], started_out))
            if Check[0] == True:
                gg = copy.deepcopy([copy.deepcopy(Check)[2], copy.deepcopy(mas)[index][1], copy.deepcopy(Check)[1]])
                # print(gg)
                flagik = 1
                if Check[2] == -11:
                    sig_segv.append(copy.deepcopy(gg))
                elif Check[2] == -8:
                    sig_fpe.append(copy.deepcopy(gg))
                elif Check[2] == -1:
                    time_out.append(copy.deepcopy(gg))
                else:
                    no_err.append(copy.deepcopy(gg))


                break
        if flagik == 0:
            mas[index][1][count] = started_i
        count += 1
    return res

def seg_segv(index):
    count = 0
    flagik = 0
    resultiki = []
    for i in sig_segv[index][1]:
        started_i = i
        started_out = sig_segv[index][3]
        for j in range(len(i)):
            # print(i)
            i = i[:-1]
            Check = check_seg_segv(i)
            if Check[0] == True:
                flagik = 1
                resultiki.append([started_i, i, len(i), sig_segv[index][1]])
                break
        if flagik == 0:
            sig_segv[index][1][count] = started_i
        count += 1
    return resultiki