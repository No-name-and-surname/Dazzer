import subprocess
import time
import statistics
import config
import mutator
import copy
import os
import sys
import re
import datetime
from random import *
import shlex
import tempfile
import threading
import fnmatch
import functools
import heapq
import glob
import queue
import concurrent.futures

debug_error_by_mutator = {
    "length_ch": {},
    "xor": {},
    "ch_symb": {},
    "interesting": {}
}
afiget = 'dfghjkl'
interesting_tests = []
queue_no_error = []
queue_sig_fpe = []
info = []
global num
num = 0
global num1
num1 = 0
info_set = set()
info_dict = {}
list_not_imp_tests = []
queue_seg_fault = []
symbols_list = list("1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'!@#$%^&*()?><\|/:;~,.}{[]")
tests = copy.deepcopy(config.args)
outputich = []
bbbbb = []
returncode = 0
sig_segv, time_out, no_err, sig_fpe = [], [], [], []
file_name = config.file_name
fileik = open('dict.txt', 'rb').read().decode().split('\r\n')
new_dict, new_dict2 = [], []
codes_set, codes_dict = set(), {}
codes_set1, codes_dict1 = set(), {}
dictionary = open(config.dict_name, 'rb').read().decode().split('\r\n')
OUTPUT_DIR = config.Corpus_dir
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

coverage_cache = {}
base_coverage_cache = {}

def safe_get_from_cache(cache, key, default_value=None):
    try:
        return cache.get(key, default_value)
    except:
        return default_value

def safe_set_in_cache(cache, key, value, max_size=10000):
    try:
        if len(cache) >= max_size:
            keys_to_remove = list(cache.keys())[:int(max_size * 0.1)]
            for k in keys_to_remove:
                if k in cache:
                    del cache[k]
        cache[key] = value
    except:
        pass

global_max_coverage = 0
global_error_codes = set()
global_coverage_lock = threading.Lock()
global_error_lock = threading.Lock()
global_saved_tests_count = 0
global_saved_tests_lock = threading.Lock()
global_error_details_lock = threading.Lock()

error_details = {}
error_by_mutator = {}

SANITIZER_ERROR_CODES = {
    -100: "Generic Sanitizer Error",
    -101: "AddressSanitizer Error",
    -102: "UndefinedBehaviorSanitizer Error",
    -103: "ThreadSanitizer Error",
    -104: "MemorySanitizer Error",
    -105: "LeakSanitizer Error",
    -106: "Go Race Detector Error"
}

error_descriptions = {
    -11: "Segmentation Fault",
    -8: "Floating Point Exception",
    -6: "Aborted",
    -4: "Illegal Instruction",
    -7: "Bus Error",
    -9: "Killed",
    -1: "Timeout",
    1: "Generic Error",
    2: "Misuse of Shell Builtins",
    126: "Command Not Executable",
    127: "Command Not Found",
    128: "Invalid Exit Argument",
    130: "Script Terminated by Ctrl+C",
    137: "Process Killed (SIGKILL)",
    139: "Segmentation Fault (SIGSEGV)",
    134: "Abort Signal (SIGABRT)",
    136: "Floating Point Exception (SIGFPE)"
}

error_descriptions.update(SANITIZER_ERROR_CODES)

error_by_mutator = {
    "interesting": {},
    "ch_symb": {},
    "length_ch": {},
    "xor": {},
    "first_no_mut": {}
}

mutation_success = {
    "interesting": {"new_coverage": 0, "new_crash": 0, "total": 0},
    "ch_symb": {"new_coverage": 0, "new_crash": 0, "total": 0},
    "length_ch": {"new_coverage": 0, "new_crash": 0, "total": 0},
    "xor": {"new_coverage": 0, "new_crash": 0, "total": 0},
    "first_no_mut": {"new_coverage": 0, "new_crash": 0, "total": 0}
}
mutation_success_lock = threading.Lock()

mutator_error_counts = {
    "interesting": 0,
    "ch_symb": 0,
    "length_ch": 0,
    "xor": 0
}
mutator_error_lock = threading.Lock()

def get_error_description(code):
    if code in error_descriptions:
        return error_descriptions[code]
    return f"Unknown Error ({code})"

def if_interesting(test_case):
    if test_case[0] < 0:
        return 1
    else:
        return 0

def graph_collecting_tests(color1, color2, index, bbbb, mas, flag):
    if flag == 0:
        gf = copy.deepcopy(mas)[index]
        _, nnn, _, _ = testing2(config.file_name, gf)
        info.append([bbbb, gf, num1, num, color1, color2, 0, returncode, nnn])
    else:
        gf = copy.deepcopy(mas)[index][1]
        _, nnn, _, _ = testing2(config.file_name, gf[0])
        info.append([bbbb, gf, num1, num, color1, color2, 0, returncode, nnn])

def tests_sorting(listik, queue_name, tests_2, stdout, stderr, filik, flag, read_count, num, mut_type, is_interesting):
    global global_max_coverage, global_error_codes, global_saved_tests_count
    
    executed, total, coverage = get_coverage(file_name, tests_2)
    
    with mutation_success_lock:
        if mut_type in mutation_success:
            mutation_success[mut_type]["total"] += 1
    
    first_test = False
    with global_coverage_lock:
        if global_max_coverage == 0 and coverage > 0:
            first_test = True
            global_max_coverage = coverage
            with mutation_success_lock:
                if mut_type in mutation_success:
                    mutation_success[mut_type]["new_coverage"] += 1
    
    increased_coverage = False
    with global_coverage_lock:
        if coverage >= global_max_coverage and coverage > 0:
            increased_coverage = True
            if coverage > global_max_coverage:
                global_max_coverage = coverage
                with mutation_success_lock:
                    if mut_type in mutation_success:
                        mutation_success[mut_type]["new_coverage"] += 1
    
    new_error = False
    with global_error_lock:
        if returncode not in global_error_codes:
            new_error = True
            global_error_codes.add(returncode)
            with mutation_success_lock:
                if mut_type in mutation_success and returncode < 0:
                    mutation_success[mut_type]["new_crash"] += 1
    
    with global_error_details_lock:
        if returncode not in error_details:
            error_details[returncode] = {
                "count": 0,
                "description": get_error_description(returncode),
                "first_seen": datetime.datetime.now().strftime("%H:%M:%S"),
                "examples": []
            }
        error_details[returncode]["count"] += 1
        
        if mut_type not in error_by_mutator:
            error_by_mutator[mut_type] = {}
        if returncode not in error_by_mutator[mut_type]:
            error_by_mutator[mut_type][returncode] = 0
        error_by_mutator[mut_type][returncode] += 1
        
        if len(error_details[returncode]["examples"]) < 5:
            error_example = {
                "test": tests_2,
                "stderr": stderr if stderr else "",
                "stdout": stdout if stdout else "",
                "mutation": mut_type,
                "coverage": coverage
            }
            error_details[returncode]["examples"].append(error_example)
    
    sanitizer_detected = False
    sanitizer_info = check_sanitizer(stderr)
    if sanitizer_info["detected"]:
        sanitizer_detected = True
    
    local_increased_coverage = False
    if len(listik) == 0:
        local_increased_coverage = True
    else:
        prev_max_coverage = max(item[5] for item in listik) if listik else 0
        local_increased_coverage = coverage > prev_max_coverage
    
    error_count = stderr.count("error") + stderr.count("Error")
    max_previous_errors = 0
    if len(sig_segv) > 0:
        for item in sig_segv:
            _, _, _, prev_stderr = testing2(file_name, item[1])
            prev_errors = prev_stderr.count("error") + prev_stderr.count("Error")
            max_previous_errors = max(max_previous_errors, prev_errors)
    more_errors = error_count > max_previous_errors
    
    listik.append([returncode, tests_2, read_count, stdout, mut_type, coverage, is_interesting])
    queue_name.append([returncode, tests_2, read_count, stdout, mut_type, coverage, is_interesting])
    
    num += 1
    info_set.add(num)
    info_dict.update({tuple(tests_2):num})
    if tests_2 not in bbbbb:
        bbbbb.append(tests_2)
    
    filik.write("test: (" + ',    '.join(tests_2) + ')'  + ' '+ str(returncode) + ' ' + str(coverage) + '%\n\n\n')
    current_thread = threading.current_thread()
    thread_name = current_thread.name.replace("(", "_").replace(")", "_").replace(" ", "_")

    tests_output_dir = os.path.join(OUTPUT_DIR, f"tests_{thread_name}")
    os.makedirs(tests_output_dir, exist_ok=True)

    if first_test or increased_coverage or new_error or sanitizer_detected:
        timestamp = datetime.datetime.now().time().strftime("%H-%M-%S-%f")
        sanitizer_suffix = "_sanitizer" if sanitizer_detected else ""
        file_namus = f"time-{timestamp}_mut_type-{mut_type}_cov-{coverage}{sanitizer_suffix}"
        file_path = os.path.join(tests_output_dir, file_namus)
 
        with open(file_path, 'w') as f:
            f.write(f"Test: {tests_2}\n")
            f.write(f"Coverage: {coverage}%\n")
            f.write(f"Return code: {returncode} ({get_error_description(returncode)})\n")
            f.write(f"Mutation type: {mut_type}\n")
            if stdout:
                f.write(f"Stdout: {stdout}\n")
            if stderr:
                f.write(f"Stderr: {stderr}\n")
                
            if sanitizer_detected:
                f.write(f"\n--- SANITIZER DETAILS ---\n")
                f.write(f"Sanitizer type: {sanitizer_info['type']}\n")
                if sanitizer_info["details"]:
                    f.write(f"Details: {sanitizer_info['details']}\n")
                f.write(f"Full sanitizer output:\n{stderr}\n")
                
        with global_saved_tests_lock:
            global_saved_tests_count += 1
            
        save_reason = ""
        if first_test:
            save_reason = "первый тест"
        elif increased_coverage:
            save_reason = f"увеличено покрытие до {coverage}%"
        elif new_error:
            save_reason = f"новый код ошибки {returncode} ({get_error_description(returncode)})"
        elif sanitizer_detected:
            save_reason = f"обнаружена ошибка санитайзера: {sanitizer_info['type']}"
            
        filik.write(f"[INFO] Сохранен тест: {file_namus}. Причина: {save_reason}\n\n")
    
    if flag == 1:
        if returncode not in codes_set:
            codes_dict.update({returncode:0})
        else:
            codes_dict.update({returncode : codes_dict[returncode] + 1})
        codes_set.add(returncode)
    read_count = 0

def run_command(command, error_message, input_data=None):
    if input_data is not None:
        process = subprocess.run(command, shell=True, check=True, input=input_data,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        process = subprocess.run(command, shell=True, check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process.stdout.decode(), process.stderr.decode()

def check_sanitizer(stderr):
    if not stderr or len(stderr) < 10:
        return {"detected": False, "type": "", "details": ""}
    
    result = {
        "detected": False,
        "type": "",
        "details": ""
    }
    go_sanitizer_markers = [
        "WARNING:.*race.*detected",
        "fatal error:.*runtime",
        "panic:.*",
    ]
    
    sanitizer_markers = [
        "==ERROR: AddressSanitizer:",
        "AddressSanitizer: heap-use-after-free",
        "AddressSanitizer: heap-buffer-overflow",
        "AddressSanitizer: stack-buffer-overflow",
        "AddressSanitizer: global-buffer-overflow",
        "AddressSanitizer: stack-use-after-return",
        "AddressSanitizer: use-after-poison",
        "AddressSanitizer: stack-use-after-scope",
        "AddressSanitizer: SEGV",
        "AddressSanitizer: requested allocation size",
        "AddressSanitizer: attempting double-free",
        "AddressSanitizer: attempting free on address which was not malloc",
        
        "==ERROR: UndefinedBehaviorSanitizer:",
        "UndefinedBehaviorSanitizer: undefined-behavior",
        "UndefinedBehaviorSanitizer: runtime error",
        "UndefinedBehaviorSanitizer: shift exponent",
        "UndefinedBehaviorSanitizer: signed-integer-overflow",
        "UndefinedBehaviorSanitizer: unsigned-integer-overflow",
        "UndefinedBehaviorSanitizer: load of misaligned",
        "UndefinedBehaviorSanitizer: null pointer",

        "==ERROR: ThreadSanitizer:",
        "ThreadSanitizer: data race",
        "ThreadSanitizer: race condition",
        
        "==ERROR: MemorySanitizer:",
        "MemorySanitizer: use-of-uninitialized-value",
        
        "==ERROR: LeakSanitizer:",
        "LeakSanitizer: detected memory leaks",
        
        "runtime error:",
        "Sanitizer:",
        "SUMMARY: Sanitizer:"
    ]
    
    sanitizer_markers.extend(go_sanitizer_markers)
    
    for marker in sanitizer_markers:
        if re.search(marker, stderr, re.IGNORECASE):
            result["detected"] = True
            
            if "race.*detected" in stderr.lower():
                result["type"] = "GoRaceDetector"
                result["details"] = re.search(r"WARNING:.*race.*detected.*?\n.*?\n", stderr, re.IGNORECASE).group(0) if re.search(r"WARNING:.*race.*detected.*?\n.*?\n", stderr, re.IGNORECASE) else "Race detected"
            elif "AddressSanitizer" in stderr:
                result["type"] = "AddressSanitizer"
            elif "UndefinedBehaviorSanitizer" in stderr:
                result["type"] = "UndefinedBehaviorSanitizer"
            elif "ThreadSanitizer" in stderr:
                result["type"] = "ThreadSanitizer"
            elif "MemorySanitizer" in stderr:
                result["type"] = "MemorySanitizer"
            elif "LeakSanitizer" in stderr:
                result["type"] = "LeakSanitizer"
            elif "panic:" in stderr.lower():
                result["type"] = "GoPanic"
                result["details"] = re.search(r"panic:.*?\n", stderr, re.IGNORECASE).group(0) if re.search(r"panic:.*?\n", stderr, re.IGNORECASE) else "Panic occurred"
            else:
                result["type"] = "Sanitizer"
                
            lines = stderr.split('\n')
            for line in lines:
                if "ERROR:" in line or "WARNING:" in line or "panic:" in line.lower():
                    result["details"] = line.strip()
                    break
                elif "SUMMARY: " in line:
                    result["details"] = line.strip()
                    break
            
            if not result["details"]:
                for line in lines:
                    if marker in line:
                        result["details"] = line.strip()
                        break
            
            if not result["details"] and lines:
                for line in lines:
                    if line.strip():
                        result["details"] = line.strip()
                        break
            
            break
    
    return result

def add_sanitizer_error(stderr, test_input=None, mut_type=None):
    sanitizer_info = check_sanitizer(stderr)
    if sanitizer_info["detected"]:
        error_code = -100
        
        if "AddressSanitizer" in sanitizer_info["type"]:
            error_code = -101
        elif "UndefinedBehaviorSanitizer" in sanitizer_info["type"]:
            error_code = -102
        elif "ThreadSanitizer" in sanitizer_info["type"]:
            error_code = -103
        elif "MemorySanitizer" in sanitizer_info["type"]:
            error_code = -104
        elif "LeakSanitizer" in sanitizer_info["type"]:
            error_code = -105
        elif "GoRaceDetector" in sanitizer_info["type"]:
            error_code = -106
        
        with global_error_details_lock:
            if error_code not in error_details:
                error_details[error_code] = {
                    "count": 0,
                    "description": f"Sanitizer: {sanitizer_info['type']}",
                    "first_seen": datetime.datetime.now().strftime("%H:%M:%S"),
                    "examples": [],
                    "details": [],
                    "is_crash": True,
                    "error_type": sanitizer_info["type"].lower().replace("sanitizer", "").strip()
                }
            error_details[error_code]["count"] += 1
            
            if sanitizer_info["details"] and sanitizer_info["details"] not in error_details[error_code]["details"]:
                error_details[error_code]["details"].append(sanitizer_info["details"])
                
            if test_input and mut_type and len(error_details[error_code]["examples"]) < 5:
                example = {
                    "test": test_input,
                    "stderr": stderr,
                    "mutation": mut_type,
                    "details": sanitizer_info["details"],
                    "sanitizer_type": sanitizer_info["type"]
                }
                error_details[error_code]["examples"].append(example)
                
            if mut_type:
                if mut_type not in error_by_mutator:
                    error_by_mutator[mut_type] = {}
                if error_code not in error_by_mutator[mut_type]:
                    error_by_mutator[mut_type][error_code] = 0
                error_by_mutator[mut_type][error_code] += 1
        
        return True, error_code
    return False, None

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

testing_cache = {}
testing_cache_size = 1000
testing_cache_lock = threading.Lock()

fast_result_cache = {}
MAX_FAST_CACHE = 50000

testing_queue = queue.Queue(maxsize=100)
testing_results = {}

def batch_testing_worker():
    while True:
        try:
            task_id, file_name, input_data, timeout = testing_queue.get()
            result = _perform_test(file_name, input_data, timeout)
            testing_results[task_id] = result
            testing_queue.task_done()
        except Exception as e:
            continue

for _ in range(min(4, os.cpu_count() or 1)):
    t = threading.Thread(target=batch_testing_worker, daemon=True)
    t.start()

def testing2(file_name, listik):
    if isinstance(listik, list):
        cache_key = (file_name, tuple(listik))
    else:
        cache_key = (file_name, listik)
    
    if cache_key in testing_cache:
        return testing_cache[cache_key]
    
    timeout = 0.5 if config.FAST_MODE else 5.0
    
    try:
        if config.FUZZING_TYPE == "Black":
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                
                start_time = time.time()
                
                if isinstance(listik, list):
                    input_data = b"\n".join(x.encode() if isinstance(x, str) else x for x in listik) + b"\n"
                else:
                    input_data = listik.encode() if isinstance(listik, str) else listik + b"\n"
                
                sock.connect((config.TARGET_HOST, config.TARGET_PORT))
                sock.sendall(input_data)
                stdout = b""
                stderr = b""
                
                while True:
                    try:
                        data = sock.recv(4096)
                        if not data:
                            break
                        stdout += data
                    except socket.timeout:
                        break
                    
                end_time = time.time()
                sock.close()
                
                exec_time = end_time - start_time
                try:
                    return_code = 0 if stdout else -1
                    with testing_cache_lock:
                        if len(testing_cache) >= testing_cache_size:
                            for k in list(testing_cache.keys())[:100]:
                                del testing_cache[k]
                        testing_cache[cache_key] = (exec_time, return_code, stdout.decode(), stderr.decode())
                    return testing_cache[cache_key]
                except:
                    result = (float('inf'), -1, "", "Decode error")
                    with testing_cache_lock:
                        testing_cache[cache_key] = result
                    return result
                    
            except socket.error as e:
                result = (float('inf'), -1, "", f"Network error: {str(e)}")
                with testing_cache_lock:
                    testing_cache[cache_key] = result
                return result
                
        else:
            if isinstance(listik, list):
                if len(listik) >= 2:
                    cmd = [file_name]
                    if config.TARGET_LANGUAGE == "go":
                        cmd.append("-race")
                    process = subprocess.Popen(cmd, 
                                            stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
                    start_time = time.time()
                    try:
                        input1 = listik[0].encode() if isinstance(listik[0], str) else listik[0]
                        process.stdin.write(input1 + b'\n')
                        process.stdin.flush()
                        input2 = listik[1].encode() if isinstance(listik[1], str) else listik[1]
                        process.stdin.write(input2 + b'\n')
                        process.stdin.flush()
                        stdout, stderr = process.communicate(timeout=timeout)
                        end_time = time.time()
                        exec_time = end_time - start_time
                        with testing_cache_lock:
                            if len(testing_cache) >= testing_cache_size:
                                for k in list(testing_cache.keys())[:100]:
                                    del testing_cache[k]
                            testing_cache[cache_key] = (exec_time, process.returncode, stdout.decode(), stderr.decode())
                        return testing_cache[cache_key]
                    except subprocess.TimeoutExpired:
                        process.kill()
                        result = (float('inf'), -1, "", "Timeout")
                        with testing_cache_lock:
                            testing_cache[cache_key] = result
                        return result
                else:
                    start_time = time.time()
                    try:
                        cmd = [file_name]
                        if config.TARGET_LANGUAGE == "go":
                            cmd.append("-race")
                        input_data = listik[0].encode() if isinstance(listik[0], str) else listik[0]
                        result = subprocess.run(cmd, 
                                             input=input_data,
                                             capture_output=True,
                                             text=True,
                                             timeout=timeout)
                        end_time = time.time()
                        exec_time = end_time - start_time
                        with testing_cache_lock:
                            if len(testing_cache) >= testing_cache_size:
                                for k in list(testing_cache.keys())[:100]:
                                    del testing_cache[k]
                            testing_cache[cache_key] = (exec_time, result.returncode, result.stdout, result.stderr)
                        return testing_cache[cache_key]
                    except subprocess.TimeoutExpired:
                        result = (float('inf'), -1, "", "Timeout")
                        with testing_cache_lock:
                            testing_cache[cache_key] = result
                        return result
            else:
                start_time = time.time()
                try:
                    cmd = [file_name]
                    if config.TARGET_LANGUAGE == "go":
                        cmd.append("-race")
                    input_data = listik.encode() if isinstance(listik, str) else listik
                    result = subprocess.run(cmd,
                                         input=input_data,
                                         capture_output=True,
                                         text=True,
                                         timeout=timeout)
                    end_time = time.time()
                    exec_time = end_time - start_time
                    with testing_cache_lock:
                        if len(testing_cache) >= testing_cache_size:
                            for k in list(testing_cache.keys())[:100]:
                                del testing_cache[k]
                        testing_cache[cache_key] = (exec_time, result.returncode, result.stdout, result.stderr)
                    return testing_cache[cache_key]
                except subprocess.TimeoutExpired:
                    result = (float('inf'), -1, "", "Timeout")
                    with testing_cache_lock:
                        testing_cache[cache_key] = result
                    return result
            return float('inf'), -1, "", "Error"
    except Exception as e:
        result = (float('inf'), -1, "", str(e)) 
        with testing_cache_lock:
            testing_cache[cache_key] = result
        return result

def testing(file_name, listik):
    if len(listik) == 1:
        tests_2 = copy.deepcopy(tests)
    else:
        tests_2 = copy.deepcopy(listik)
        try:
            strace_command = [f"{file_name}"]
            if config.TARGET_LANGUAGE == "go":
                strace_command.append("-race")
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
    return queue_seg_fault, time_out, queue_no_error, queue_sig_fpe

def get_error_statistics():
    with global_error_details_lock:
        total_errors = sum(details["count"] for details in error_details.values())
        unique_errors = len(error_details)
        
        error_types = {}
        crash_count = 0
        sanitizer_count = 0
        
        for code, details in error_details.items():
            error_type = details.get("error_type", "unknown")
            
            if error_type not in error_types:
                error_types[error_type] = 0
            error_types[error_type] += details["count"]
            
            if details.get("is_crash", False):
                crash_count += details["count"]
                
            if code < -100 and code >= -110:
                sanitizer_count += details["count"]
                
            if error_type == "sanitizer" and "sanitizer_type" in details:
                sanitizer_type = details["sanitizer_type"]
                sanitizer_key = f"{sanitizer_type}_error"
                if sanitizer_key not in error_types:
                    error_types[sanitizer_key] = 0
                error_types[sanitizer_key] += details["count"]
                
        return {
            "total_errors": total_errors,
            "unique_errors": unique_errors,
            "error_types": error_types,
            "crash_count": crash_count,
            "sanitizer_count": sanitizer_count,
            "error_details": error_details,
            "error_by_mutator": error_by_mutator
        }

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
    
def send_inp(file_name, i, testiki, read_count, filik, mut_type):
    global num
    if i == 1:
        tests_2 = copy.deepcopy(tests)
    else:
        tests_2 = copy.deepcopy(testiki)
    file_times = []
    file_results = []
    nn = ''
    times = []
    results = []
    read_count = 0
    strace_command = ["strace", file_name]
    if config.TARGET_LANGUAGE == "go":
        strace_command.append("-race")
    f = chr(randint(97, 122))
    if config.FUZZING_TYPE == "Gray":
        try:
            with subprocess.Popen(strace_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE) as process:        
                read_count = 0  
                for line in process.stderr:
                    if 'read(' in line.decode():
                        try:
                            if tests_2[read_count] == config.FUZZ:
                                nn, mut_type = mutator.mutate(f, 100)
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
            exec_time, returncode, stdout, stderr = testing2(file_name, tests_2)
            is_interesting = if_interesting([returncode, tests_2, stdout])
            
            sanitizer_info = check_sanitizer(stderr)
            
            error_info = categorize_error(returncode, stderr, stdout)
            
            if sanitizer_info["detected"]:
                error_info["type"] = "sanitizer"
                error_info["sanitizer_output"] = stderr
                error_info["sanitizer_details"] = sanitizer_info["details"]
                error_info["sanitizer_type"] = sanitizer_info["type"]
                error_info["is_crash"] = True
                
                filik.write(f"\n[SANITIZER DETECTED] {sanitizer_info['type']}: {sanitizer_info['details']}\n")
                filik.write(f"Test: {tests_2}\nMutation: {mut_type}\n\n")
                
            is_crash = log_error(error_info, tests_2, mut_type, 0)
            
            if is_crash or returncode == -11 or returncode == -8 or sanitizer_info["detected"]:
                tests_sorting(sig_segv, queue_seg_fault, tests_2, stdout, stderr, filik, 0, read_count, num, mut_type, is_interesting)
            else:
                tests_sorting(no_err, queue_no_error, tests_2, stdout, stderr, filik, 1, read_count, num, mut_type, is_interesting)
            file_times.append(exec_time)
            file_results.append((returncode, stdout, stderr))
            average_time = statistics.mean(file_times)
            times.append(average_time)
            results.append(file_results)
            read_count = 0
            forik = 0
        except:
            return
    elif config.FUZZING_TYPE == "White":
        src = config.source_file
        global afiget
        
        exec_time, returncode, stdout, stderr = testing2(file_name, tests_2)
        is_interesting = if_interesting([returncode, tests_2, stdout])
        
        executed, total, coverage = get_coverage(file_name, tests_2)
        
        sanitizer_info = check_sanitizer(stderr)
        
        error_info = categorize_error(returncode, stderr, stdout)
        
        if sanitizer_info["detected"]:
            error_info["type"] = "sanitizer"
            error_info["sanitizer_output"] = stderr
            error_info["sanitizer_details"] = sanitizer_info["details"]
            error_info["sanitizer_type"] = sanitizer_info["type"]
            error_info["is_crash"] = True
            
            filik.write(f"\n[SANITIZER DETECTED] {sanitizer_info['type']}: {sanitizer_info['details']}\n")
            filik.write(f"Test: {tests_2}\nMutation: {mut_type}\nCoverage: {coverage}%\n\n")
            
        is_crash = log_error(error_info, tests_2, mut_type, coverage)
        
        if is_crash or returncode == -11 or returncode == -8 or sanitizer_info["detected"]:
            tests_sorting(sig_segv, queue_seg_fault, tests_2, stdout, stderr, filik, 0, read_count, num, mut_type, is_interesting)
        else:
            tests_sorting(no_err, queue_no_error, tests_2, stdout, stderr, filik, 1, read_count, num, mut_type, is_interesting)
        
        file_times.append(exec_time)
        file_results.append((returncode, stdout, stderr))
        average_time = statistics.mean(file_times)
        times.append(average_time)
        results.append(file_results)
        read_count = 0
        forik = 0
        afiget = datetime.datetime.now().time()
    elif config.FUZZING_TYPE == "Black":
        exec_time, returncode, stdout, stderr = testing2(file_name, tests_2)
        is_interesting = if_interesting([returncode, tests_2, stdout])
        
        sanitizer_info = check_sanitizer(stderr)
        
        error_info = categorize_error(returncode, stderr, stdout)
        
        if sanitizer_info["detected"]:
            error_info["type"] = "sanitizer"
            error_info["sanitizer_output"] = stderr
            error_info["sanitizer_details"] = sanitizer_info["details"]
            error_info["sanitizer_type"] = sanitizer_info["type"]
            error_info["is_crash"] = True
            
            filik.write(f"\n[SANITIZER DETECTED] {sanitizer_info['type']}: {sanitizer_info['details']}\n")
            filik.write(f"Test: {tests_2}\nMutation: {mut_type}\n\n")
            
        is_crash = log_error(error_info, tests_2, mut_type, 0)
        new_output = True
        if len(no_err) > 0:
            for item in no_err:
                if item[3] == stdout:
                    new_output = False
                    break
        
        if is_crash or returncode < 0 or sanitizer_info["detected"]:
            tests_sorting(sig_segv, queue_seg_fault, tests_2, stdout, stderr, filik, 0, read_count, num, mut_type, is_interesting)
        elif new_output:
            tests_sorting(no_err, queue_no_error, tests_2, stdout, stderr, filik, 1, read_count, num, mut_type, is_interesting)
        
        file_times.append(exec_time)
        file_results.append((returncode, stdout, stderr))
        average_time = statistics.mean(file_times)
        times.append(average_time)
        results.append(file_results)
        read_count = 0
        forik = 0

def calibrate(testiki, filik, mut_type):
    times = []
    results = []
    c_c = 0
    if config.FUZZ in tests:
        while True:
            c_c += 1
            read_count = 0
            if config.FAST_MODE and c_c > 10:
                break
            send_inp(file_name, 1, testiki, read_count, filik, mut_type)
    else:
        read_count = 0
        send_inp(file_name, 0, testiki, read_count, filik, mut_type)
            
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
            if mas[index][1] not in config.args:
                if j != 0:
                    i, mut_type = mutator.mutate(symbols_list[rand_num], 100, new_dict2, new_dict)
                    mas[index][1][count] = i
                    try:
                        ggggg = info_dict[tuple(mas[index][1])]
                        kkk = 0
                        while kkk != 1:
                            i, mut_type = mutator.mutate(symbols_list[rand_num], 100, new_dict2, new_dict)
                            mas[index][1][count] = i
                            try:
                                ggggg = info_dict[tuple(mas[index][1])]
                            except:
                                kkk = 1
                                num += 1
                                info_dict.update({tuple(mas[index][1]):num})
                    except:
                        i, mut_type = mutator.mutate(symbols_list[rand_num], 100, new_dict2, new_dict)
                        num += 1
                        info_dict.update({tuple(mas[index][1]):num})
            Check = copy.deepcopy(check_no_error(mas[index][1], started_out))
            if Check[0] == True:
                gg = copy.deepcopy([copy.deepcopy(Check)[2], copy.deepcopy(mas)[index][1], copy.deepcopy(Check)[1], 0, mut_type])
                flagik = 1
                if Check[2] == -11 or no_error_try:
                    sig_segv.append(copy.deepcopy(gg))
                    queue_seg_fault.append(copy.deepcopy(gg))
                elif Check[2] == -1:
                    time_out.append(copy.deepcopy(gg))
                else:
                    no_err.append(copy.deepcopy(gg))
                    queue_no_error.append(copy.deepcopy(gg))
                returncode = copy.deepcopy(Check)[2]
                if copy.deepcopy(mas)[index][1] not in bbbbb:
                    bbbbb.append(copy.deepcopy(mas)[index][1])
                _, nnn, _, _ = testing2(config.file_name, copy.deepcopy(mas)[index][1])
                filik.write("test: (" + ',    '.join(copy.deepcopy(mas)[index][1]) + ')'  + ' '+ str(nnn) + ' ' +  str(0) + '\n\n\n')
                if copy.deepcopy(mas)[index][1][:-1] == started_i:
                    continue
                else:
                    if bbbb in config.args:
                        if type(copy.deepcopy(mas)[index][1]) == list and len(copy.deepcopy(mas)[index][1]) == 1:
                            if num1 != num:
                                if bbbb == copy.deepcopy(mas)[index][1]:
                                    copy.deepcopy(mas)[index][1], mut_type = mutator.mutate(copy.deepcopy(mas)[index][1], 100, new_dict2, new_dict)
                                    _, nnn, _, _ = testing2(config.file_name, copy.deepcopy(mas)[index][1])
                                    info.append([bbbb, copy.deepcopy(mas)[index][1], num1, num, '#daffb5', '#001aff', 0, returncode, nnn])
                                else:
                                    graph_collecting_tests('#daffb5', '#001aff', index, bbbb, mas, 1)
                        else:
                            if num1 != num:
                                if bbbb == copy.deepcopy(mas)[index][1]:
                                    copy.deepcopy(mas)[index][1], mut_type = mutator.mutate(copy.deepcopy(mas)[index][1], 100, new_dict2, new_dict)
                                    _, nnn, _, _ = testing2(config.file_name, copy.deepcopy(mas)[index][1])
                                    info.append([bbbb, copy.deepcopy(mas)[index][1], num1, num, '#daffb5', '#001aff', 0, returncode, nnn])
                                else:
                                    graph_collecting_tests('#daffb5', '#001aff', index, bbbb, mas, 0)
                    else:
                        if type(copy.deepcopy(mas)[index][1]) == list and len(copy.deepcopy(mas)[index][1]) == 1:
                            if num1 != num:
                                if bbbb == copy.deepcopy(mas)[index][1]:
                                    copy.deepcopy(mas)[index][1], mut_type = mutator.mutate(copy.deepcopy(mas)[index][1], 100, new_dict2, new_dict)
                                    _, nnn, _, _ = testing2(config.file_name, copy.deepcopy(mas)[index][1])
                                    info.append([bbbb, copy.deepcopy(mas)[index][1], num1, num, '#fff3bd', '#001aff', 0, returncode, nnn])
                                else:
                                    graph_collecting_tests('#fff3bd', '#001aff', index, bbbb, mas, 1)
                        else:
                            if num1 != num:
                                if bbbb == copy.deepcopy(mas)[index][1]:
                                    copy.deepcopy(mas)[index][1], mut_type = mutator.mutate(copy.deepcopy(mas)[index][1], 100, new_dict2, new_dict)
                                    _, nnn, _, _ = testing2(config.file_name, copy.deepcopy(mas)[index][1])
                                    info.append([bbbb, copy.deepcopy(mas)[index][1], num1, num, '#fff3bd', '#001aff', 0, returncode, nnn])
                                else:
                                    graph_collecting_tests('#fff3bd', '#001aff', index, bbbb, mas, 0)
                                    
                    if len(mas[index][1]) == 1:
                        return res
                    else:
                        break
            else:
                gg = copy.deepcopy([copy.deepcopy(Check)[2], copy.deepcopy(mas)[index][1], copy.deepcopy(Check)[1]])
                list_not_imp_tests.append(copy.deepcopy(gg))
                returncode = copy.deepcopy(Check)[2]
                ll = randint(0, 20)
                if copy.deepcopy(mas)[index][1] not in bbbbb:
                    bbbbb.append(copy.deepcopy(mas)[index][1])
                _, nnn, _, _ = testing2(config.file_name, copy.deepcopy(mas)[index][1])
                filik.write("test: (" + ',    '.join(copy.deepcopy(mas)[index][1]) + ')'  + ' '+ str(nnn) + ' ' +  str(0) + '\n\n\n')
                if ll == 6 and i != mas[index][1]:
                    if returncode not in codes_set1:
                        codes_dict1.update({returncode:0})
                    else:
                        codes_dict1.update({returncode : codes_dict1[returncode] + 1})
                    codes_set1.add(returncode)
                    if bbbb in config.args:
                        if num1 != num:
                            if type(copy.deepcopy(mas)[index][1]) == list and len(copy.deepcopy(mas)[index][1]) == 1:
                                if bbbb == copy.deepcopy(mas)[index][1]:
                                        gf, mut_type = mutator.mutate(copy.deepcopy(mas)[index][1], 100, new_dict2, new_dict)
                                        _, nnn, _, _ = testing2(config.file_name, gf)
                                        info.append([bbbb, gf, num1, num, '#daffb5', '#ff9cc0', 0, returncode, nnn])
                                else:
                                    gf = copy.deepcopy(mas)[index][1]
                                    _, nnn, _, _ = testing2(config.file_name, gf[0])
                                    info.append([bbbb, gf, num1, num, '#daffb5', '#ff9cc0', 0, returncode, nnn])
                            else:
                                if bbbb == copy.deepcopy(mas)[index][1]:
                                        gf, mut_type = mutator.mutate(copy.deepcopy(mas)[index][1], 100, new_dict2, new_dict)
                                        _, nnn, _, _ = testing2(config.file_name, gf)
                                        info.append([bbbb, gf, num1, num, '#daffb5', '#ff9cc0', 0, returncode, nnn])
                                else:
                                    gf = copy.deepcopy(mas)[index]
                                    _, nnn, _, _ = testing2(config.file_name, gf)
                                    info.append([bbbb, gf, num1, num, '#daffb5', '#ff9cc0', 0, returncode, nnn])
                    else:
                        break
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

def compile_with_coverage(source_file, binary_name):
    try:
        if config.TARGET_LANGUAGE == "go":
            compile_cmd = f"go build -o {binary_name} {source_file}"
        else:
            compile_cmd = f"gcc -fprofile-arcs -ftest-coverage {source_file} -o {binary_name}"
        process = subprocess.run(compile_cmd, shell=True, check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def reset_coverage_data(binary_name):
    try:
        if config.TARGET_LANGUAGE == "go":
            subprocess.run(f"rm -f *.coverprofile", shell=True)
        else:
            subprocess.run(f"rm -f *.gcda", shell=True)
        return True
    except:
        return False

def get_go_coverage(cover_file):
    if not os.path.exists(cover_file):
        return 0, 0, 0.0
    
    try:
        with open(cover_file, 'r') as f:
            lines = f.readlines()
        
        total_statements = 0
        covered_statements = 0
        
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            count = int(parts[-2])
            statements = int(parts[-1])
            total_statements += statements
            if count > 0:
                covered_statements += statements
        
        coverage = (covered_statements / total_statements * 100) if total_statements > 0 else 0.0
        return covered_statements, total_statements, coverage
    except:
        return 0, 0, 0.0

def get_line_coverage(gcov_file):
    if not os.path.exists(gcov_file):
        return 0, 0, 0.0
    
    try:
        with open(gcov_file, 'r') as f:
            lines = f.readlines()
        
        total_lines = 0
        executed_lines = 0
        
        for line in lines:
            parts = line.split(':', 2)
            if len(parts) < 3:
                continue
                
            execution_count = parts[0].strip()
            source_line = parts[2].strip()
            if not source_line or source_line.startswith('//'):
                continue
                
            if execution_count != '-':
                total_lines += 1
                if execution_count != '#####' and execution_count != '0':
                    executed_lines += 1
        
        coverage = (executed_lines / total_lines * 100) if total_lines > 0 else 0.0
        return executed_lines, total_lines, coverage
    except:
        return 0, 0, 0.0

def get_function_coverage(gcov_file):
    if not os.path.exists(gcov_file):
        return 0, 0, 0.0
    
    try:
        with open(gcov_file, 'r') as f:
            lines = f.readlines()
        
        total_functions = 0
        executed_functions = 0
        current_function = None
        
        for line in lines:
            if 'function' in line:
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    total_functions += 1
                    execution_count = parts[0].strip()
                    if execution_count != '#####' and execution_count != '0':
                        executed_functions += 1
        
        coverage = (executed_functions / total_functions * 100) if total_functions > 0 else 0.0
        return executed_functions, total_functions, coverage
    except:
        return 0, 0, 0.0

def get_branch_coverage(gcov_file):
    if not os.path.exists(gcov_file):
        return 0, 0, 0.0
    
    try:
        with open(gcov_file, 'r') as f:
            lines = f.readlines()
        
        total_branches = 0
        executed_branches = 0
        
        for line in lines:
            if 'branch' in line:
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    total_branches += 1
                    execution_count = parts[0].strip()
                    if execution_count != '#####' and execution_count != '0':
                        executed_branches += 1
        
        coverage = (executed_branches / total_branches * 100) if total_branches > 0 else 0.0
        return executed_branches, total_branches, coverage
    except:
        return 0, 0, 0.0

def get_coverage(binary_path, input_data):
    global global_max_coverage
    try:
        input_key = str(input_data) if not isinstance(input_data, list) else tuple(input_data)
        if input_key in coverage_cache:
            return coverage_cache[input_key]
            
        source_file = config.source_file
        if not os.path.exists(source_file):
            return 0, 1, 0.0
            
        thread_name = threading.current_thread().name.replace("(", "_").replace(")", "_").replace(" ", "_")
        temp_dir = os.path.join(OUTPUT_DIR, f"temp_{thread_name}")
        os.makedirs(temp_dir, exist_ok=True)
        gcov_output_dir = os.path.join(OUTPUT_DIR, f"gcov_{thread_name}")
        os.makedirs(gcov_output_dir, exist_ok=True)
        
        source_base = os.path.basename(source_file)
        binary_base = os.path.basename(binary_path)
        temp_source = os.path.join(temp_dir, source_base)
        
        need_compile = not os.path.exists(os.path.join(temp_dir, binary_base))
        
        original_dir = os.getcwd()
        
        try:
            if need_compile:
                with open(source_file, 'r') as src, open(temp_source, 'w') as dst:
                    dst.write(src.read())
            
            os.chdir(temp_dir)
        
            if need_compile:
                if config.TARGET_LANGUAGE == "go":
                    compile_cmd = f"go build -o {binary_base} {source_base}"
                else:
                    compile_cmd = f"gcc -fprofile-arcs -ftest-coverage {source_base} -o {binary_base}"
                subprocess.run(compile_cmd, shell=True, check=True)
        
            for gcda_file in [f for f in os.listdir('.') if f.endswith('.gcda') or f.endswith('.coverprofile')]:
                try:
                    os.unlink(gcda_file)
                except:
                    pass
        
            if isinstance(input_data, list):
                input_str = "\n".join(str(x) for x in input_data) + "\n"
            else:
                input_str = str(input_data) + "\n"
                
            cover_file = f"coverage_{thread_name}.coverprofile"
            cmd = [f"./{binary_base}"]
            if config.TARGET_LANGUAGE == "go":
                cmd = ["go", "run", "-coverprofile", cover_file, source_base]
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            try:
                stdout, stderr = process.communicate(input=input_str.encode(), timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            
            if config.TARGET_LANGUAGE == "go":
                if os.path.exists(cover_file):
                    executed, total, coverage = get_go_coverage(cover_file)
                    if total > 0:
                        coverage = round(coverage, 2)
                        
                        if coverage > global_max_coverage:
                            global_max_coverage = coverage
                            timestamp = datetime.datetime.now().time().strftime("%H-%M-%S-%f")
                            output_filename = f"cov-{coverage}_time-{timestamp}_{source_base}.coverprofile"
                            output_gcov = os.path.join(gcov_output_dir, output_filename)
                            with open(cover_file, 'r') as src, open(output_gcov, 'w') as dst:
                                dst.write(src.read())
                            
                        result = (executed, total, coverage)
                        coverage_cache[input_key] = result
                        return result
            else:
                subprocess.run(
                    ["gcov", source_base],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )

                gcov_file = f"{source_base}.gcov"
                if os.path.exists(gcov_file):
                    executed, total, coverage = get_line_coverage(gcov_file)
                    
                    if total > 0:
                        coverage = round(coverage, 2)
                        
                        if coverage > global_max_coverage:
                            global_max_coverage = coverage
                            timestamp = datetime.datetime.now().time().strftime("%H-%M-%S-%f")
                            output_filename = f"cov-{coverage}_time-{timestamp}_{source_base}.gcov"
                            output_gcov = os.path.join(gcov_output_dir, output_filename)
                            with open(gcov_file, 'r') as src, open(output_gcov, 'w') as dst:
                                dst.write(src.read())
                            
                        result = (executed, total, coverage)
                        coverage_cache[input_key] = result
                        return result
            
            result = (0, 1, 0.0)
            coverage_cache[input_key] = result
            return result
            
        finally:
            os.chdir(original_dir)
            
    except Exception as e:
        return 0, 1, 0.0

def parse_gcov_output(source_file):
    gcov_file = f"{os.path.basename(source_file)}.gcov"
    if not os.path.exists(gcov_file):
        return 0.0
    
    executed_lines = 0
    total_lines = 0
    
    with open(gcov_file, 'r') as f:
        for line in f:
            if line.strip().startswith('-') or line.strip().startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) > 1 and parts[0].strip().isdigit():
                executed_lines += 1
            total_lines += 1
    
    coverage = (executed_lines / total_lines) * 100 if total_lines > 0 else 0.0
    return coverage

def categorize_error(returncode, stderr, stdout):
    error_info = {
        "code": returncode,
        "type": "unknown",
        "is_crash": False
    }
    
    sanitizer_info = check_sanitizer(stderr)
    if sanitizer_info["detected"]:
        if sanitizer_info["type"] == "AddressSanitizer":
            error_info["code"] = -101
        elif sanitizer_info["type"] == "UndefinedBehaviorSanitizer":
            error_info["code"] = -102
        elif sanitizer_info["type"] == "ThreadSanitizer":
            error_info["code"] = -103  
        elif sanitizer_info["type"] == "MemorySanitizer":
            error_info["code"] = -104
        elif sanitizer_info["type"] == "LeakSanitizer":
            error_info["code"] = -105
        elif sanitizer_info["type"] == "GoRaceDetector":
            error_info["code"] = -106
        elif sanitizer_info["type"] == "GoPanic":
            error_info["code"] = -107
        
        error_info["type"] = "sanitizer"
        error_info["sanitizer_type"] = sanitizer_info["type"]
        error_info["details"] = sanitizer_info["details"]
        error_info["is_crash"] = True
        
        return error_info
    
    if returncode == -11:
        error_info["type"] = "segmentation_fault" 
        error_info["is_crash"] = True
    elif returncode == -8:
        error_info["type"] = "floating_point_exception"
        error_info["is_crash"] = True
    elif returncode == -6:
        error_info["type"] = "aborted"
        error_info["is_crash"] = True
    elif returncode == -9:
        error_info["type"] = "killed"
        error_info["is_crash"] = True
    elif returncode == -4:
        error_info["type"] = "illegal_instruction"
        error_info["is_crash"] = True
    elif returncode == -7:
        error_info["type"] = "bus_error"
        error_info["is_crash"] = True
    elif returncode == -1:
        error_info["type"] = "timeout"
    elif returncode > 128:
        error_info["type"] = f"signal_{returncode - 128}"
        error_info["is_crash"] = True
    
    if stderr:
        if "memory" in stderr.lower() and "corruption" in stderr.lower():
            error_info["type"] = "memory_corruption"
            error_info["is_crash"] = True
        elif "stack" in stderr.lower() and "overflow" in stderr.lower():
            error_info["type"] = "stack_overflow"
            error_info["is_crash"] = True
        elif "heap" in stderr.lower() and ("overflow" in stderr.lower() or "corruption" in stderr.lower()):
            error_info["type"] = "heap_corruption"
            error_info["is_crash"] = True
        elif "double free" in stderr.lower():
            error_info["type"] = "double_free"
            error_info["is_crash"] = True
        elif "use after free" in stderr.lower():
            error_info["type"] = "use_after_free"
            error_info["is_crash"] = True
        elif "segmentation fault" in stderr.lower() or "segfault" in stderr.lower():
            error_info["type"] = "segmentation_fault"
            error_info["is_crash"] = True
            
        if stderr.strip():
            lines = stderr.split('\n')
            for line in lines:
                if "error:" in line.lower() or "fault" in line.lower() or "crash" in line.lower():
                    error_info["details"] = line.strip()
                    break
            
            if "details" not in error_info:
                for line in lines:
                    if line.strip():
                        error_info["details"] = line.strip()
                        break
    
    return error_info

def log_error(error_info, test_input, mut_type, coverage):
    with global_error_details_lock:
        error_code = error_info["code"]
        error_type = error_info["type"]
        
        if error_code not in error_details:
            error_details[error_code] = {
                "count": 0,
                "description": get_error_description(error_code),
                "first_seen": datetime.datetime.now().strftime("%H:%M:%S"),
                "examples": [],
                "error_type": error_type,
                "is_crash": error_info.get("is_crash", False)
            }
        
        error_details[error_code]["count"] += 1
        
        with mutator_error_lock:
            if mut_type in mutator_error_counts:
                mutator_error_counts[mut_type] += 1
        
        if mut_type not in error_by_mutator:
            error_by_mutator[mut_type] = {}
        if error_code not in error_by_mutator[mut_type]:
            error_by_mutator[mut_type][error_code] = 0
        error_by_mutator[mut_type][error_code] += 1
        
        if len(error_details[error_code]["examples"]) < 5:
            example = {
                "test": test_input,
                "mutation": mut_type,
                "coverage": coverage,
                "error_type": error_type,
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S.%f")
            }
            
            if "details" in error_info:
                example["details"] = error_info["details"]
            
            if error_type == "sanitizer":
                if "sanitizer_output" in error_info:
                    example["sanitizer_output"] = error_info["sanitizer_output"]
                if "sanitizer_type" in error_info:
                    example["sanitizer_type"] = error_info["sanitizer_type"]
                if "sanitizer_details" in error_info:
                    example["sanitizer_details"] = error_info["sanitizer_details"]
            
            error_details[error_code]["examples"].append(example)
    
    return error_info["is_crash"]

def inflate_stats_for_display():
    return True

def update_mutation_success(mut_type, coverage_increased, new_crash):
    with mutation_success_lock:
        if mut_type in mutation_success:
            mutation_success[mut_type]["total"] += 1
            if coverage_increased:
                mutation_success[mut_type]["new_coverage"] += 1
            if new_crash:
                mutation_success[mut_type]["new_crash"] += 1