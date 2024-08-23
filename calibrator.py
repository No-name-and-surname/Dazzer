import subprocess
import time
import statistics
import config
import mutator
import copy
from random import *

queue_no_error = []
queue_sig_fpe = []
info = []
global num
num = 1
global num1
num1 = 0
info_set = set()
info_dict = {}
list_not_imp_tests = []
queue_seg_fault = []
symbols_list = list("1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'!@#$%^&*()?><\|/:;~,.}{[]")
tests = copy.deepcopy(config.args)
outputich = []
sig_segv, time_out, no_err, sig_fpe = [], [], [], []
file_name = config.file_name
fileik = open('dict.txt', 'rb').read().decode().split('\r\n')
new_dict, new_dict2 = [], []
codes_set, codes_dict = set(), {}
codes_set1, codes_dict1 = set(), {}
dictionary = open(config.dict_name, 'rb').read().decode().split('\r\n')
if len(config.args) == 1:
    for i in dictionary:
        if i.startswith(config.args[0].lower()) == True:
            if config.args[0].lower() != config.args[0]:
                i = list(i)
                i[0] = i[0].upper()
                new_dict.append(''.join(i))
            else:
                new_dict.append(i)
        elif config.args[0] in i:
            new_dict2.append(i)
def testing2(file_name, listik):
    p = ''.join(listik)
    start_time = time.time()
    try:
        result = subprocess.run([file_name], input=p, capture_output=True, text=True, timeout=5)
        end_time = time.time()
        exec_time = end_time - start_time
        return exec_time, result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return float('inf'), -1, "", "Timeout"
    except subprocess.CalledProcessError:
        return float('inf'), -1, "", "Called_error"

def testing(file_name, listik):
    if len(listik) == 1:
        tests_2 = copy.deepcopy(tests)
    else:
        tests_2 = copy.deepcopy(listik)
    try:
        strace_command = ["strace", file_name]
        with subprocess.Popen(strace_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE) as process:        
            read_count = 0  
            for line in process.stderr:
                if 'read(' in line.decode():
                    try:
                        process.stdin.write(tests_2[read_count].encode())
                        read_count += 1
                        process.stdin.flush()
                    except:
                        break
        exec_time, returncode, stdout, stderr = testing2(file_name, tests_2)
        return exec_time, returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        return float('inf'), -1, "", "Timeout"
    except subprocess.CalledProcessError:
        return float('inf'), -1, "", "Called_error"

def ret_globals():
    return sig_segv, time_out, no_err, sig_fpe

def check_no_error(list_of_inp, started_out):
    exec_time, returncode, stdout, stderr = testing2(file_name, list_of_inp)
    started_out1 = started_out
    if stdout == started_out:
        return [False, '', '']
    else:
        return [True, stdout, returncode]
    
def check_seg_segv(list_of_inp):
    exec_time, returncode, stdout, stderr = testing2(file_name, list_of_inp)
    if returncode == -11:
        return [False, '', '']
    else:
        return [True, stdout, returncode]
    
def send_inp(file_name, i, testiki, read_count, filik):
    global num
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
    exec_time, returncode, stdout, stderr = testing2(file_name, tests_2)
    if returncode == -11:
        sig_segv.append([returncode, tests_2, read_count, stdout])
        queue_seg_fault.append([returncode, tests_2, read_count, stdout])
        num += 1
        info_set.add(num)
        info_dict.update({tuple(tests_2):num})
        filik.write("test: (" + ',    '.join(tests_2) + ')' + ' '+ str(returncode) + ' ' + str(read_count) + '\n\n\n')
        read_count = 0
    elif returncode == -8:
        sig_fpe.append([returncode, tests_2, read_count, stdout])
        queue_sig_fpe.append([returncode, tests_2, read_count, stdout])
        num += 1
        info_set.add(num)
        info_dict.update({tuple(tests_2):num})
        filik.write("test: (" + ',    '.join(tests_2) + ')' +  ' '+ str(returncode) + ' ' + str(read_count) + '\n\n\n')
        read_count = 0
    elif line == -1:
        time_out.append([returncode, tests_2, read_count, stdout])
        num += 1
        info_set.add(num)
        info_dict.update({tuple(tests_2):num})
        filik.write("test: (" + ',    '.join(tests_2) + ')'  + ' '+ str(returncode) + ' ' + str(read_count) + '\n\n\n')
        read_count = 0
    else:
        no_err.append([returncode, tests_2, read_count, stdout])
        queue_no_error.append([returncode, tests_2, read_count, stdout])
        num += 1
        info_set.add(num)
        info_dict.update({tuple(tests_2):num})
        filik.write("test: (" + ',    '.join(tests_2) + ')'  + ' '+ str(returncode) + ' ' +  str(read_count) + '\n\n\n')
        if returncode not in codes_set:
            codes_dict.update({returncode:0})
        else:
            codes_dict.update({returncode : codes_dict[returncode] + 1})
        codes_set.add(returncode)
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

def no_error_try(index, mas, filik):
    global num
    global num1
    count = 0
    flagik = 0
    res = []
    rand_num = randint(0, 87)
    for i in mas[index][1]:
        bbbb = mas[index][1]
        started_i = i
        try:
            num1 = info_dict[tuple(mas[index][1])]
        except:
            num1 = num + 1
        try:
            started_out = mas[index][3]
        except:
            started_out = mas[index][2]
        for j in range(len(symbols_list)):
            if i[:-1] in '1234567890':
                rand_num = randint(10, 61)
            elif i[:-1] in 'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM':
                rand_num = randint(62, 87)
            elif i[:-1] in "'!@#$%^&*()?><\|/:;~,.}{[]":
                rand_num = randint(0, 9)
            if j != 0:
                i = mutator.mutate(symbols_list[rand_num], 100, new_dict2, new_dict)
                mas[index][1][count] = i
                try:
                    ggggg = info_dict[tuple(mas[index][1])]
                    kkk = 0
                    while kkk != 1:
                        i = mutator.mutate(symbols_list[rand_num], 100, new_dict2, new_dict)
                        mas[index][1][count] = i
                        try:
                            ggggg = info_dict[tuple(mas[index][1])]
                        except:
                            kkk = 1
                            num += 1
                            info_dict.update({tuple(mas[index][1]):num})
                except:
                    num += 1
                    info_dict.update({tuple(mas[index][1]):num})
            Check = copy.deepcopy(check_no_error(mas[index][1], started_out))
            if Check[0] == True:
                gg = copy.deepcopy([copy.deepcopy(Check)[2], copy.deepcopy(mas)[index][1], copy.deepcopy(Check)[1]])
                flagik = 1
                if Check[2] == -11:
                    sig_segv.append(copy.deepcopy(gg))
                    queue_seg_fault.append(copy.deepcopy(gg))
                elif Check[2] == -8:
                    sig_fpe.append(copy.deepcopy(gg))
                    queue_sig_fpe.append(copy.deepcopy(gg))
                elif Check[2] == -1:
                    time_out.append(copy.deepcopy(gg))
                else:
                    no_err.append(copy.deepcopy(gg))
                    queue_no_error.append(copy.deepcopy(gg))
                returncode = copy.deepcopy(Check)[2]
                filik.write("test: (" + ',    '.join(copy.deepcopy(mas)[index][1]) + ')'  + ' '+ str(returncode) + ' ' +  str(0) + '\n\n\n')
                if copy.deepcopy(mas)[index][1][:-1] == started_i:
                    continue
                else:
                    if bbbb in config.args:
                        if type(copy.deepcopy(mas)[index][1]) == list:
                            if num1 != num:
                                info.append([bbbb, copy.deepcopy(mas)[index][1], num1, num, '#daffb5', '#001aff', 0])
                        else:
                            if num1 != num:
                                info.append([bbbb, copy.deepcopy(mas)[index][1], num1, num, '#daffb5', '#001aff', 0])
                    else:
                        if type(copy.deepcopy(mas)[index][1]) == list:
                            if num1 != num:
                                info.append([bbbb, copy.deepcopy(mas)[index][1], num1, num, '#fff3bd', '#001aff', 0])
                        else:
                            if num1 != num:
                                info.append([bbbb, copy.deepcopy(mas)[index][1], num1, num, '#fff3bd', '#001aff', 0])
                    if len(mas[index][1]) == 1:
                        return res
                    else:
                        break
            else:
                gg = copy.deepcopy([copy.deepcopy(Check)[2], copy.deepcopy(mas)[index][1], copy.deepcopy(Check)[1]])
                list_not_imp_tests.append(copy.deepcopy(gg))
                returncode = copy.deepcopy(Check)[2]
                ll = randint(0, 20)
                filik.write("test: (" + ',    '.join(copy.deepcopy(mas)[index][1]) + ')'  + ' '+ str(returncode) + ' ' +  str(0) + '\n\n\n')
                if ll == 6 and i != mas[index][1]:
                    if returncode not in codes_set1:
                        codes_dict1.update({returncode:0})
                    else:
                        codes_dict1.update({returncode : codes_dict1[returncode] + 1})
                    codes_set1.add(returncode)
                    if bbbb in config.args:
                        if type(copy.deepcopy(mas)[index][1]) == list:
                            info.append([bbbb, copy.deepcopy(mas)[index][1], num1, num, '#daffb5', '#ff9cc0', 0])
                        else:
                            info.append([bbbb, copy.deepcopy(mas)[index][1], num1, num, '#daffb5', '#ff9cc0', 0])
                    else:
                        if type(copy.deepcopy(mas)[index][1]) == list:
                            info.append([bbbb, copy.deepcopy(mas)[index][1], num1, num, '#fff3bd', '#ff9cc0', 0])
                        else:
                            info.append([bbbb, copy.deepcopy(mas)[index][1], num1, num, '#fff3bd', '#ff9cc0', 0])
        if flagik == 0:
            try:
                mas[index][1][count] = started_i
            except:
                mas[index][1] = started_i
        else:
            if len(mas[index][1]) == 1:
                break
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