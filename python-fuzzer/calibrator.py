import subprocess
import time
import statistics
import config
import mutator
import copy
import os
import re
import datetime
from random import *
import threading
import queue

dbg_err_by_mut = {
    "length_ch": {},
    "xor": {},
    "ch_symb": {},
    "interesting": {},
    "dict": {}
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
fileik = open(config.dict_name, 'rb').read().decode().split('\r\n')
new_dict, new_dict2 = [], []
codes_set, codes_dict = set(), {}
codes_set1, codes_dict1 = set(), {}
dictionary = open(config.dict_name, 'rb').read().decode().split('\r\n')
OUTPUT_DIR = config.Corpus_dir
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

cov_cache = {}
base_cov_cache = {}

def safe_get(cache, key, default_value=None):
    try:
        return cache.get(key, default_value)
    except:
        return default_value

def safe_set(cache, key, value, max_size=10000):
    try:
        if len(cache) >= max_size:
            keys_to_remove = list(cache.keys())[:int(max_size * 0.1)]
            for k in keys_to_remove:
                if k in cache:
                    del cache[k]
        cache[key] = value
    except:
        pass

max_cov = 0
err_codes = set()
cov_lock = threading.Lock()
err_code_lock = threading.Lock()
saved_cnt = 0
saved_lock = threading.Lock()
err_det_lock = threading.Lock()

exec_cnt = 0
exec_cnt_lock = threading.Lock()

_throughput_window = []
_throughput_lock = threading.Lock()
_THROUGHPUT_WINDOW_SIZE = 30
_estimated_throughput = 0.0


def inc_exec(n=1):
    global exec_cnt
    with exec_cnt_lock:
        exec_cnt += n
        return exec_cnt


def get_exec():
    with exec_cnt_lock:
        return exec_cnt


def rec_throughput():
    global _estimated_throughput
    with _throughput_lock:
        now = time.time()
        _throughput_window.append(now)
        while _throughput_window and now - _throughput_window[0] > 1.0:
            _throughput_window.pop(0)
        if len(_throughput_window) >= 2:
            span = _throughput_window[-1] - _throughput_window[0]
            if span > 0:
                raw_rate = (len(_throughput_window) - 1) / span
            else:
                raw_rate = len(_throughput_window)
        else:
            raw_rate = len(_throughput_window)
        _estimated_throughput = raw_rate


def get_throughput():
    with _throughput_lock:
        return _estimated_throughput

corpus_lock = threading.Lock()
corpus = []

exec_times_lock = threading.Lock()
exec_times = []
adapt_timeout = None
ADAPTIVE_TIMEOUT_MULT = 4
ADAPTIVE_TIMEOUT_MIN = 0.05
MAX_EXEC_TIMES = 500

err_det = {}
err_by_mut = {}

SANIT_ERR_CODES = {
    -100: "Generic Sanitizer Error",
    -101: "AddressSanitizer Error",
    -102: "UndefinedBehaviorSanitizer Error",
    -103: "ThreadSanitizer Error",
    -104: "MemorySanitizer Error",
    -105: "LeakSanitizer Error",
    -106: "Go Race Detector Error"
}

err_desc = {
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

err_desc.update(SANIT_ERR_CODES)

err_by_mut = {
    "interesting": {},
    "ch_symb": {},
    "length_ch": {},
    "xor": {},
    "dict": {},
    "first_no_mut": {}
}

mut_sucs = {
    "interesting": {"new_coverage": 0, "new_crash": 0, "total": 0},
    "ch_symb": {"new_coverage": 0, "new_crash": 0, "total": 0},
    "length_ch": {"new_coverage": 0, "new_crash": 0, "total": 0},
    "xor": {"new_coverage": 0, "new_crash": 0, "total": 0},
    "dict": {"new_coverage": 0, "new_crash": 0, "total": 0},
    "first_no_mut": {"new_coverage": 0, "new_crash": 0, "total": 0}
}
mut_sucs_lock = threading.Lock()

err_counts = {
    "interesting": 0,
    "ch_symb": 0,
    "length_ch": 0,
    "xor": 0,
    "dict": 0
}
err_lock = threading.Lock()

def get_err_desc(code):
    if code in err_desc:
        return err_desc[code]
    return f"Unknown Error ({code})"


def _calc_input_size(test_input):
    if isinstance(test_input, list):
        input_str = "\n".join(str(x) for x in test_input) + "\n"
    else:
        input_str = str(test_input) + "\n"
    return len(input_str.encode('utf-8'))


def _get_coverage_type():
    if config.TARGET_LANGUAGE == "go":
        return "go cover"
    return "gcov"


def _parse_asan_variables(stderr):
    if not stderr:
        return []
    variables = []
    lines = stderr.split('\n')
    for i, line in enumerate(lines):
        match = re.search(
            r"(\[\s*\d+,\s*\d+\))\s+'([^']+)'\s+.*?(?:\(line\s+(\d+)\))?",
            line
        )
        if match:
            var_range = match.group(1)
            var_name = match.group(2)
            var_line = match.group(3) if match.group(3) else ""
            overflow_info = ""
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line:
                    overflow_info = next_line
            entry = f"{var_range} '{var_name}'"
            if var_line:
                entry += f" (line {var_line})"
            if overflow_info:
                entry += f"\n<== {overflow_info}"
            variables.append(entry)
        elif "overflows this variable" in line or "underflows this variable" in line:
            stripped = line.strip()
            if stripped and stripped not in [v.split('\n')[-1].lstrip('<== ') for v in variables]:
                if variables:
                    last = variables[-1]
                    if "<== " not in last:
                        variables[-1] = last + f"\n<== {stripped}"
    return variables


def format_crash_report(timestamp, returncode, tests_2, mut_type, coverage,
                        executed, total, stdout, stderr, sanit_found, sanit_info):
    lines = []
    is_crash = returncode != 0 or sanit_found

    if is_crash:
        lines.append(f"[!] CRASH REPORT: time-{timestamp}")
    else:
        lines.append(f"[*] TEST REPORT: time-{timestamp}")

    lines.append("")
    lines.append("")
    lines.append("[+] PROCESS INFO")
    lines.append(f"Return code : {returncode} ({get_err_desc(returncode)})")
    lines.append(f"Target      : {config.file_name}")

    lines.append("")
    lines.append("[+] MUTATION")
    lines.append(f"Strategy    : {mut_type}")
    input_size = _calc_input_size(tests_2)
    lines.append(f"Input Size  : {input_size} bytes")

    if config.FUZZING_TYPE == "White":
        lines.append("")
        cov_type = _get_coverage_type()
        lines.append(f"[+] COVERAGE ({cov_type})")
        lines.append(f"Line Cov    : {coverage}% ({executed} / {total} lines)")

    if stderr or stdout:
        lines.append("")
        if sanit_found:
            lines.append("[+] STDERR / SANITIZER OUTPUT")
        else:
            lines.append("[+] STDERR / STDOUT")
        if sanit_found:
            lines.append(f"{sanit_info['type']}: {sanit_info['details']}")
            if stderr:
                lines.append("")
                for sline in stderr.strip().split('\n'):
                    lines.append(f"  {sline}")
            asan_vars = _parse_asan_variables(stderr)
            if asan_vars:
                lines.append("")
                for var_info in asan_vars:
                    lines.append(var_info)
        else:
            if stderr:
                lines.append(stderr.strip())
            if stdout:
                if stderr:
                    lines.append("")
                lines.append(f"stdout: {stdout.strip()}")

    lines.append("")
    lines.append(f"[+] INPUT DATA")
    try:
        test_str = ', '.join(str(x) for x in tests_2)
    except TypeError:
        test_str = str(tests_2)
    lines.append(f"[{test_str}]")

    lines.append("")
    return '\n'.join(lines)

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

def tests_sorting(listik, queue_name, tests_2, stdout, stderr, filik, flag, read_count, num, mut_type, is_interesting, returncode):
    global max_cov, err_codes, saved_cnt
    
    executed, total, coverage = get_cov(file_name, tests_2)
    
    with mut_sucs_lock:
        if mut_type in mut_sucs:
            mut_sucs[mut_type]["total"] += 1
    
    first_test = False
    with cov_lock:
        if max_cov == 0 and coverage > 0:
            first_test = True
            max_cov = coverage
            with mut_sucs_lock:
                if mut_type in mut_sucs:
                    mut_sucs[mut_type]["new_coverage"] += 1
    
    increased_cov = False
    with cov_lock:
        if coverage >= max_cov and coverage > 0:
            increased_cov = True
            if coverage > max_cov:
                max_cov = coverage
                with mut_sucs_lock:
                    if mut_type in mut_sucs:
                        mut_sucs[mut_type]["new_coverage"] += 1
    
    new_error = False
    with err_code_lock:
        if returncode not in err_codes:
            new_error = True
            err_codes.add(returncode)
            with mut_sucs_lock:
                if mut_type in mut_sucs and returncode < 0:
                    mut_sucs[mut_type]["new_crash"] += 1
    
    with err_det_lock:
        if returncode not in err_det:
            err_det[returncode] = {
                "count": 0,
                "description": get_err_desc(returncode),
                "first_seen": datetime.datetime.now().strftime("%H:%M:%S"),
                "examples": []
            }
        err_det[returncode]["count"] += 1
        
        if mut_type not in err_by_mut:
            err_by_mut[mut_type] = {}
        if returncode not in err_by_mut[mut_type]:
            err_by_mut[mut_type][returncode] = 0
        err_by_mut[mut_type][returncode] += 1
        
        if len(err_det[returncode]["examples"]) < 5:
            error_example = {
                "test": tests_2,
                "stderr": stderr if stderr else "",
                "stdout": stdout if stdout else "",
                "mutation": mut_type,
                "coverage": coverage
            }
            err_det[returncode]["examples"].append(error_example)
    
    sanit_found = False
    sanit_info = check_sanit(stderr)
    if sanit_info["detected"]:
        sanit_found = True
    
    local_increased_cov = False
    if len(listik) == 0:
        local_increased_cov = True
    else:
        if listik:
            prev_max_cov = max(item[5] for item in listik)
        else:
            prev_max_cov = 0
        local_increased_cov = coverage > prev_max_cov
    
    error_count = stderr.count("error") + stderr.count("Error")
    max_prev_errors = 0
    if len(sig_segv) > 0:
        for item in sig_segv:
            _, _, _, prev_stderr = testing2(file_name, item[1])
            prev_errors = prev_stderr.count("error") + prev_stderr.count("Error")
            max_prev_errors = max(max_prev_errors, prev_errors)
    more_errors = error_count > max_prev_errors
    
    listik.append([returncode, tests_2, read_count, stdout, mut_type, coverage, is_interesting])
    queue_name.append([returncode, tests_2, read_count, stdout, mut_type, coverage, is_interesting])

    if increased_cov or new_error:
        saved_input = tests_2
        if returncode != 0:
            saved_input = minimize(file_name, tests_2, returncode)
        add_corpus(saved_input)
    
    num += 1
    info_set.add(num)
    info_dict.update({_make_hashable(tests_2):num})
    if tests_2 not in bbbbb:
        bbbbb.append(tests_2)
    
    try:
        test_str = ',    '.join(str(x) for x in tests_2)
    except TypeError:
        test_str = str(tests_2)
    filik.write("test: (" + test_str + ')'  + ' '+ str(returncode) + ' ' + str(coverage) + '%\n\n\n')
    current_thread = threading.current_thread()
    thread_name = current_thread.name.replace("(", "_").replace(")", "_").replace(" ", "_")

    tests_output_dir = os.path.join(OUTPUT_DIR, f"tests_{thread_name}")
    os.makedirs(tests_output_dir, exist_ok=True)

    is_error = returncode != 0 or sanit_found
    should_save = is_error or increased_cov

    if should_save:
        timestamp = datetime.datetime.now().time().strftime("%H-%M-%S-%f")
        if sanit_found:
            sanit_suffix = "_sanitizer"
        else:
            sanit_suffix = ""
        file_namus = f"time-{timestamp}_mut_type-{mut_type}_ch_cov-{coverage}{sanit_suffix}"
        file_path = os.path.join(tests_output_dir, file_namus)

        report = format_crash_report(
            timestamp, returncode, tests_2, mut_type, coverage,
            executed, total, stdout, stderr, sanit_found, sanit_info
        )
        with open(file_path, 'w') as f:
            f.write(report)
                
        with saved_lock:
            saved_cnt += 1
            
        save_reason = ""
        if increased_cov:
            save_reason = f"увеличено покрытие до {coverage}%"
        elif is_error:
            save_reason = f"обнаружена ошибка {returncode} ({get_err_desc(returncode)})"
        elif sanit_found:
            save_reason = f"обнаружена ошибка санитайзера: {sanit_info['type']}"
            
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

def check_sanit(stderr):
    if not stderr or len(stderr) < 10:
        return {"detected": False, "type": "", "details": ""}
    
    result = {
        "detected": False,
        "type": "",
        "details": ""
    }
    go_sanit_markers = [
        "WARNING:.*race.*detected",
        "fatal error:.*runtime",
        "panic:.*",
    ]
    
    sanit_markers = [
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
    
    sanit_markers.extend(go_sanit_markers)
    
    for marker in sanit_markers:
        if re.search(marker, stderr, re.IGNORECASE):
            result["detected"] = True
            
            if "race.*detected" in stderr.lower():
                result["type"] = "GoRaceDetector"
                match = re.search(r"WARNING:.*race.*detected.*?\n.*?\n", stderr, re.IGNORECASE)
                if match:
                    result["details"] = match.group(0)
                else:
                    result["details"] = "Race detected"
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
                match = re.search(r"panic:.*?\n", stderr, re.IGNORECASE)
                if match:
                    result["details"] = match.group(0)
                else:
                    result["details"] = "Panic occurred"
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

def add_sanit_err(stderr, test_input=None, mut_type=None):
    sanit_info = check_sanit(stderr)
    if sanit_info["detected"]:
        error_code = -100
        
        if "AddressSanitizer" in sanit_info["type"]:
            error_code = -101
        elif "UndefinedBehaviorSanitizer" in sanit_info["type"]:
            error_code = -102
        elif "ThreadSanitizer" in sanit_info["type"]:
            error_code = -103
        elif "MemorySanitizer" in sanit_info["type"]:
            error_code = -104
        elif "LeakSanitizer" in sanit_info["type"]:
            error_code = -105
        elif "GoRaceDetector" in sanit_info["type"]:
            error_code = -106
        
        with err_det_lock:
            if error_code not in err_det:
                err_det[error_code] = {
                    "count": 0,
                    "description": f"Sanitizer: {sanit_info['type']}",
                    "first_seen": datetime.datetime.now().strftime("%H:%M:%S"),
                    "examples": [],
                    "details": [],
                    "is_crash": True,
                    "error_type": sanit_info["type"].lower().replace("sanitizer", "").strip()
                }
            err_det[error_code]["count"] += 1
            
            if sanit_info["details"] and sanit_info["details"] not in err_det[error_code]["details"]:
                err_det[error_code]["details"].append(sanit_info["details"])
                
            if test_input and mut_type and len(err_det[error_code]["examples"]) < 5:
                example = {
                    "test": test_input,
                    "stderr": stderr,
                    "mutation": mut_type,
                    "details": sanit_info["details"],
                    "sanitizer_type": sanit_info["type"]
                }
                err_det[error_code]["examples"].append(example)
                
            if mut_type:
                if mut_type not in err_by_mut:
                    err_by_mut[mut_type] = {}
                if error_code not in err_by_mut[mut_type]:
                    err_by_mut[mut_type][error_code] = 0
                err_by_mut[mut_type][error_code] += 1
        
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

test_cache = {}
test_cache_sz = 1000
test_cache_lock = threading.Lock()

fast_cache = {}
MAX_FAST_CACHE = 50000

testing_queue = queue.Queue(maxsize=100)
testing_results = {}

def batch_testing_worker():
    while True:
        try:
            task_id, target_file, input_data, timeout_val = testing_queue.get()
            try:
                if isinstance(input_data, list):
                    input_str = "\n".join(str(x) for x in input_data) + "\n"
                else:
                    input_str = str(input_data) + "\n"
                proc = subprocess.run(
                    [target_file],
                    input=input_str,
                    capture_output=True,
                    text=True,
                    timeout=timeout_val
                )
                testing_results[task_id] = (0.0, proc.returncode, proc.stdout, proc.stderr)
            except subprocess.TimeoutExpired:
                testing_results[task_id] = (float('inf'), -1, "", "Timeout")
            except Exception as exc:
                testing_results[task_id] = (float('inf'), -1, "", str(exc))
            testing_queue.task_done()
        except Exception:
            continue

for _ in range(min(4, os.cpu_count() or 1)):
    t = threading.Thread(target=batch_testing_worker, daemon=True)
    t.start()

def _make_hashable(val):
    if isinstance(val, list):
        return tuple(_make_hashable(v) for v in val)
    return val


def testing2(file_name, listik):
    try:
        if isinstance(listik, list):
            cache_key = (file_name, _make_hashable(listik))
        else:
            cache_key = (file_name, listik)
    except TypeError:
        cache_key = (file_name, str(listik))
    
    if cache_key in test_cache:
        inc_exec(1)
        rec_throughput()
        return test_cache[cache_key]
    
    inc_exec(1)
    rec_throughput()
    timeout = get_timeout()
    
    try:
        if config.FUZZING_TYPE == "Black":
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                
                start_time = time.time()
                
                if isinstance(listik, list):
                    parts = []
                    for x in listik:
                        if isinstance(x, str):
                            parts.append(x.encode())
                        else:
                            parts.append(x)
                    input_data = b"\n".join(parts) + b"\n"
                else:
                    if isinstance(listik, str):
                        input_data = listik.encode()
                    else:
                        input_data = listik + b"\n"
                
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
                rec_exec_time(exec_time)
                try:
                    if stdout:
                        return_code = 0
                    else:
                        return_code = -1
                    with test_cache_lock:
                        if len(test_cache) >= test_cache_sz:
                            for k in list(test_cache.keys())[:100]:
                                del test_cache[k]
                        test_cache[cache_key] = (exec_time, return_code, stdout.decode(), stderr.decode())
                    return test_cache[cache_key]
                except:
                    result = (float('inf'), -1, "", "Decode error")
                    with test_cache_lock:
                        test_cache[cache_key] = result
                    return result
                    
            except socket.error as e:
                result = (float('inf'), -1, "", f"Network error: {str(e)}")
                with test_cache_lock:
                    test_cache[cache_key] = result
                return result
                
        else:
            if isinstance(listik, list):
                if len(listik) >= 2:
                    cmd = [file_name]
                    process = subprocess.Popen(cmd, 
                                            stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
                    start_time = time.time()
                    try:
                        if isinstance(listik[0], str):
                            input1 = listik[0].encode()
                        else:
                            input1 = listik[0]
                        process.stdin.write(input1 + b'\n')
                        process.stdin.flush()
                        if isinstance(listik[1], str):
                            input2 = listik[1].encode()
                        else:
                            input2 = listik[1]
                        process.stdin.write(input2 + b'\n')
                        process.stdin.flush()
                        stdout, stderr = process.communicate(timeout=timeout)
                        end_time = time.time()
                        exec_time = end_time - start_time
                        rec_exec_time(exec_time)
                        with test_cache_lock:
                            if len(test_cache) >= test_cache_sz:
                                for k in list(test_cache.keys())[:100]:
                                    del test_cache[k]
                            test_cache[cache_key] = (exec_time, process.returncode, stdout.decode(), stderr.decode())
                        return test_cache[cache_key]
                    except subprocess.TimeoutExpired:
                        process.kill()
                        result = (float('inf'), -1, "", "Timeout")
                        with test_cache_lock:
                            test_cache[cache_key] = result
                        return result
                else:
                    start_time = time.time()
                    try:
                        cmd = [file_name]
                        if isinstance(listik[0], str):
                            input_data = listik[0].encode()
                        else:
                            input_data = listik[0]
                        result = subprocess.run(cmd, 
                                             input=input_data,
                                             capture_output=True,
                                             text=True,
                                             timeout=timeout)
                        end_time = time.time()
                        exec_time = end_time - start_time
                        rec_exec_time(exec_time)
                        with test_cache_lock:
                            if len(test_cache) >= test_cache_sz:
                                for k in list(test_cache.keys())[:100]:
                                    del test_cache[k]
                            test_cache[cache_key] = (exec_time, result.returncode, result.stdout, result.stderr)
                        return test_cache[cache_key]
                    except subprocess.TimeoutExpired:
                        result = (float('inf'), -1, "", "Timeout")
                        with test_cache_lock:
                            test_cache[cache_key] = result
                        return result
            else:
                start_time = time.time()
                try:
                    cmd = [file_name]
                    if isinstance(listik, str):
                        input_data = listik.encode()
                    else:
                        input_data = listik
                    result = subprocess.run(cmd,
                                         input=input_data,
                                         capture_output=True,
                                         text=True,
                                         timeout=timeout)
                    end_time = time.time()
                    exec_time = end_time - start_time
                    rec_exec_time(exec_time)
                    with test_cache_lock:
                        if len(test_cache) >= test_cache_sz:
                            for k in list(test_cache.keys())[:100]:
                                del test_cache[k]
                        test_cache[cache_key] = (exec_time, result.returncode, result.stdout, result.stderr)
                    return test_cache[cache_key]
                except subprocess.TimeoutExpired:
                    result = (float('inf'), -1, "", "Timeout")
                    with test_cache_lock:
                        test_cache[cache_key] = result
                    return result
            return float('inf'), -1, "", "Error"
    except Exception as e:
        result = (float('inf'), -1, "", str(e)) 
        with test_cache_lock:
            test_cache[cache_key] = result
        return result

def testing(file_name, listik):
    if len(listik) == 1:
        tests_2 = copy.deepcopy(tests)
    else:
        tests_2 = copy.deepcopy(listik)
        try:
            strace_command = [f"{file_name}"]
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

def get_err_stats():
    with err_det_lock:
        total_errors = sum(details["count"] for details in err_det.values())
        unique_errors = len(err_det)
        
        error_types = {}
        crash_count = 0
        sanit_count = 0
        
        for code, details in err_det.items():
            error_type = details.get("error_type", "unknown")
            
            if error_type not in error_types:
                error_types[error_type] = 0
            error_types[error_type] += details["count"]
            
            if details.get("is_crash", False):
                crash_count += details["count"]
                
            if code < -100 and code >= -110:
                sanit_count += details["count"]
                
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
            "sanitizer_count": sanit_count,
            "error_details": err_det,
            "error_by_mutator": err_by_mut
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
            
            sanit_info = check_sanit(stderr)
            
            error_info = cat_error(returncode, stderr, stdout)
            
            if sanit_info["detected"]:
                error_info["type"] = "sanitizer"
                error_info["sanitizer_output"] = stderr
                error_info["sanitizer_details"] = sanit_info["details"]
                error_info["sanitizer_type"] = sanit_info["type"]
                error_info["is_crash"] = True
                
                filik.write(f"\n[SANITIZER DETECTED] {sanit_info['type']}: {sanit_info['details']}\n")
                filik.write(f"Test: {tests_2}\nMutation: {mut_type}\n\n")
                
            is_crash = log_error(error_info, tests_2, mut_type, 0)
            
            if is_crash or returncode == -11 or returncode == -8 or sanit_info["detected"]:
                tests_sorting(sig_segv, queue_seg_fault, tests_2, stdout, stderr, filik, 0, read_count, num, mut_type, is_interesting, returncode)
            else:
                tests_sorting(no_err, queue_no_error, tests_2, stdout, stderr, filik, 1, read_count, num, mut_type, is_interesting, returncode)
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
        
        executed, total, coverage = get_cov(file_name, tests_2)
        
        sanit_info = check_sanit(stderr)
        
        error_info = cat_error(returncode, stderr, stdout)
        
        if sanit_info["detected"]:
            error_info["type"] = "sanitizer"
            error_info["sanitizer_output"] = stderr
            error_info["sanitizer_details"] = sanit_info["details"]
            error_info["sanitizer_type"] = sanit_info["type"]
            error_info["is_crash"] = True
            
            filik.write(f"\n[SANITIZER DETECTED] {sanit_info['type']}: {sanit_info['details']}\n")
            filik.write(f"Test: {tests_2}\nMutation: {mut_type}\nCoverage: {coverage}%\n\n")
            
        is_crash = log_error(error_info, tests_2, mut_type, coverage)
        
        if is_crash or returncode == -11 or returncode == -8 or sanit_info["detected"]:
            tests_sorting(sig_segv, queue_seg_fault, tests_2, stdout, stderr, filik, 0, read_count, num, mut_type, is_interesting, returncode)
        else:
            tests_sorting(no_err, queue_no_error, tests_2, stdout, stderr, filik, 1, read_count, num, mut_type, is_interesting, returncode)
        
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
        
        sanit_info = check_sanit(stderr)
        
        error_info = cat_error(returncode, stderr, stdout)
        
        if sanit_info["detected"]:
            error_info["type"] = "sanitizer"
            error_info["sanitizer_output"] = stderr
            error_info["sanitizer_details"] = sanit_info["details"]
            error_info["sanitizer_type"] = sanit_info["type"]
            error_info["is_crash"] = True
            
            filik.write(f"\n[SANITIZER DETECTED] {sanit_info['type']}: {sanit_info['details']}\n")
            filik.write(f"Test: {tests_2}\nMutation: {mut_type}\n\n")
            
        is_crash = log_error(error_info, tests_2, mut_type, 0)
        new_output = True
        if len(no_err) > 0:
            for item in no_err:
                if item[3] == stdout:
                    new_output = False
                    break
        
        if is_crash or returncode < 0 or sanit_info["detected"]:
            tests_sorting(sig_segv, queue_seg_fault, tests_2, stdout, stderr, filik, 0, read_count, num, mut_type, is_interesting, returncode)
        elif new_output:
            tests_sorting(no_err, queue_no_error, tests_2, stdout, stderr, filik, 1, read_count, num, mut_type, is_interesting, returncode)
        
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

def compile_cov(source_file, binary_name):
    try:
        if config.TARGET_LANGUAGE == "go":
            compile_cmd = f"go build -race -o {binary_name} {source_file}"
        else:
            compile_cmd = f"gcc -fprofile-arcs -ftest-coverage {source_file} -o {binary_name}"
        process = subprocess.run(compile_cmd, shell=True, check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def reset_cov(binary_name):
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
        
        total_stmts = 0
        covered_stmts = 0
        
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            count = int(parts[-2])
            statements = int(parts[-1])
            total_stmts += statements
            if count > 0:
                covered_stmts += statements
        
        coverage = (covered_stmts / total_stmts * 100) if total_stmts > 0 else 0.0
        return covered_stmts, total_stmts, coverage
    except:
        return 0, 0, 0.0

def get_line_cov(gcov_file):
    if not os.path.exists(gcov_file):
        return 0, 0, 0.0
    
    try:
        with open(gcov_file, 'r') as f:
            lines = f.readlines()
        
        total_lines = 0
        exec_lines = 0
        
        for line in lines:
            parts = line.split(':', 2)
            if len(parts) < 3:
                continue
                
            exec_count = parts[0].strip()
            source_line = parts[2].strip()
            if not source_line or source_line.startswith('//'):
                continue
                
            if exec_count != '-':
                total_lines += 1
                if exec_count != '#####' and exec_count != '0':
                    exec_lines += 1
        
        if total_lines > 0:
            coverage = exec_lines / total_lines * 100
        else:
            coverage = 0.0
        return exec_lines, total_lines, coverage
    except:
        return 0, 0, 0.0

def get_func_cov(gcov_file):
    if not os.path.exists(gcov_file):
        return 0, 0, 0.0
    
    try:
        with open(gcov_file, 'r') as f:
            lines = f.readlines()
        
        total_funcs = 0
        exec_funcs = 0
        current_function = None
        
        for line in lines:
            if 'function' in line:
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    total_funcs += 1
                    exec_count = parts[0].strip()
                    if exec_count != '#####' and exec_count != '0':
                        exec_funcs += 1
        
        if total_funcs > 0:
            coverage = exec_funcs / total_funcs * 100
        else:
            coverage = 0.0
        return exec_funcs, total_funcs, coverage
    except:
        return 0, 0, 0.0

def get_branch_cov(gcov_file):
    if not os.path.exists(gcov_file):
        return 0, 0, 0.0
    
    try:
        with open(gcov_file, 'r') as f:
            lines = f.readlines()
        
        total_branches = 0
        exec_branches = 0
        
        for line in lines:
            if 'branch' in line:
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    total_branches += 1
                    exec_count = parts[0].strip()
                    if exec_count != '#####' and exec_count != '0':
                        exec_branches += 1
        
        if total_branches > 0:
            coverage = exec_branches / total_branches * 100
        else:
            coverage = 0.0
        return exec_branches, total_branches, coverage
    except:
        return 0, 0, 0.0

def get_cov(binary_path, input_data):
    global max_cov
    try:
        if isinstance(input_data, list):
            input_key = tuple(input_data)
        else:
            input_key = str(input_data)
        if input_key in cov_cache:
            return cov_cache[input_key]
            
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
        
            if need_compile:
                if config.TARGET_LANGUAGE == "go":
                    compile_cmd = f"go build -race -o {binary_base} {source_base}"
                else:
                    compile_cmd = f"gcc -fprofile-arcs -ftest-coverage {source_base} -o {binary_base}"
                subprocess.run(compile_cmd, shell=True, check=True, cwd=temp_dir)
        
            for gcda_file in [f for f in os.listdir(temp_dir) if f.endswith('.gcda') or f.endswith('.coverprofile')]:
                try:
                    os.unlink(os.path.join(temp_dir, gcda_file))
                except:
                    pass
        
            if isinstance(input_data, list):
                input_str = "\n".join(str(x) for x in input_data) + "\n"
            else:
                input_str = str(input_data) + "\n"
                
            cover_file = os.path.join(temp_dir, f"coverage_{thread_name}.coverprofile")
            binary_abs = os.path.join(temp_dir, binary_base)
            cmd = [binary_abs]
            if config.TARGET_LANGUAGE == "go":
                cmd = ["go", "run", "-race", "-coverprofile", cover_file, source_base]
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=temp_dir
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
                        
                        if coverage > max_cov:
                            max_cov = coverage
                            timestamp = datetime.datetime.now().time().strftime("%H-%M-%S-%f")
                            output_filename = f"cov-{coverage}_time-{timestamp}_{source_base}.coverprofile"
                            output_gcov = os.path.join(gcov_output_dir, output_filename)
                            with open(cover_file, 'r') as src_f, open(output_gcov, 'w') as dst_f:
                                dst_f.write(src_f.read())
                            
                        result = (executed, total, coverage)
                        cov_cache[input_key] = result
                        return result
            else:
                subprocess.run(
                    ["gcov", source_base],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                    cwd=temp_dir
                )

                gcov_file = os.path.join(temp_dir, f"{source_base}.gcov")
                if os.path.exists(gcov_file):
                    executed, total, coverage = get_line_cov(gcov_file)
                    
                    if total > 0:
                        coverage = round(coverage, 2)
                        
                        if coverage > max_cov:
                            max_cov = coverage
                            timestamp = datetime.datetime.now().time().strftime("%H-%M-%S-%f")
                            output_filename = f"cov-{coverage}_time-{timestamp}_{source_base}.gcov"
                            output_gcov = os.path.join(gcov_output_dir, output_filename)
                            with open(gcov_file, 'r') as src_f, open(output_gcov, 'w') as dst_f:
                                dst_f.write(src_f.read())
                            
                        result = (executed, total, coverage)
                        cov_cache[input_key] = result
                        return result
            
            result = (0, 1, 0.0)
            cov_cache[input_key] = result
            return result
            
        finally:
            pass
            
    except Exception as e:
        return 0, 1, 0.0

def parse_gcov_output(source_file):
    gcov_file = f"{os.path.basename(source_file)}.gcov"
    if not os.path.exists(gcov_file):
        return 0.0
    
    exec_lines = 0
    total_lines = 0
    
    with open(gcov_file, 'r') as f:
        for line in f:
            if line.strip().startswith('-') or line.strip().startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) > 1 and parts[0].strip().isdigit():
                exec_lines += 1
            total_lines += 1
    
    if total_lines > 0:
        coverage = (exec_lines / total_lines) * 100
    else:
        coverage = 0.0
    return coverage

def cat_error(returncode, stderr, stdout):
    error_info = {
        "code": returncode,
        "type": "unknown",
        "is_crash": False
    }
    
    sanit_info = check_sanit(stderr)
    if sanit_info["detected"]:
        if sanit_info["type"] == "AddressSanitizer":
            error_info["code"] = -101
        elif sanit_info["type"] == "UndefinedBehaviorSanitizer":
            error_info["code"] = -102
        elif sanit_info["type"] == "ThreadSanitizer":
            error_info["code"] = -103  
        elif sanit_info["type"] == "MemorySanitizer":
            error_info["code"] = -104
        elif sanit_info["type"] == "LeakSanitizer":
            error_info["code"] = -105
        elif sanit_info["type"] == "GoRaceDetector":
            error_info["code"] = -106
        elif sanit_info["type"] == "GoPanic":
            error_info["code"] = -107
        
        error_info["type"] = "sanitizer"
        error_info["sanitizer_type"] = sanit_info["type"]
        error_info["details"] = sanit_info["details"]
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
    with err_det_lock:
        error_code = error_info["code"]
        error_type = error_info["type"]
        
        if error_code not in err_det:
            err_det[error_code] = {
                "count": 0,
                "description": get_err_desc(error_code),
                "first_seen": datetime.datetime.now().strftime("%H:%M:%S"),
                "examples": [],
                "error_type": error_type,
                "is_crash": error_info.get("is_crash", False)
            }
        
        err_det[error_code]["count"] += 1
        
        with err_lock:
            if mut_type in err_counts:
                err_counts[mut_type] += 1
        
        if mut_type not in err_by_mut:
            err_by_mut[mut_type] = {}
        if error_code not in err_by_mut[mut_type]:
            err_by_mut[mut_type][error_code] = 0
        err_by_mut[mut_type][error_code] += 1
        
        if len(err_det[error_code]["examples"]) < 5:
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
            
            err_det[error_code]["examples"].append(example)
    
    return error_info["is_crash"]


def upd_mut_sucs(mut_type, cov_up, new_crash):
    with mut_sucs_lock:
        if mut_type in mut_sucs:
            mut_sucs[mut_type]["total"] += 1
            if cov_up:
                mut_sucs[mut_type]["new_coverage"] += 1
            if new_crash:
                mut_sucs[mut_type]["new_crash"] += 1


def add_corpus(test_input):
    with corpus_lock:
        if isinstance(test_input, list):
            key = tuple(test_input)
        else:
            key = test_input
        for existing in corpus:
            if isinstance(existing, list):
                existing_key = tuple(existing)
            else:
                existing_key = existing
            if existing_key == key:
                return False
        corpus.append(copy.deepcopy(test_input))
        return True


def get_corpus():
    with corpus_lock:
        if corpus:
            idx = randint(0, len(corpus) - 1)
            return copy.deepcopy(corpus[idx])
    return None


def rec_exec_time(elapsed):
    global adapt_timeout
    with exec_times_lock:
        exec_times.append(elapsed)
        if len(exec_times) > MAX_EXEC_TIMES:
            del exec_times[:len(exec_times) - MAX_EXEC_TIMES]
        if len(exec_times) >= 20:
            sorted_times = sorted(exec_times)
            median = sorted_times[len(sorted_times) // 2]
            adapt_timeout = max(
                ADAPTIVE_TIMEOUT_MIN,
                median * ADAPTIVE_TIMEOUT_MULT
            )


def get_timeout():
    with exec_times_lock:
        if adapt_timeout is not None:
            return adapt_timeout
    return 0.5 if config.FAST_MODE else 5.0


def minimize(file_name_path, test_input, expected_returncode):
    if isinstance(test_input, list):
        minimized = list(test_input)
        for i in range(len(minimized)):
            original = minimized[i]
            if len(original) <= 1:
                continue
            lo, hi = 0, len(original)
            while lo < hi - 1:
                mid = (lo + hi) // 2
                candidate = list(minimized)
                candidate[i] = original[:mid]
                try:
                    _, rc, _, _ = testing2(file_name_path, candidate)
                    if rc == expected_returncode:
                        hi = mid
                    else:
                        lo = mid
                except Exception:
                    lo = mid
            minimized[i] = original[:hi]
        return minimized
    else:
        if len(test_input) <= 1:
            return test_input
        lo, hi = 0, len(test_input)
        while lo < hi - 1:
            mid = (lo + hi) // 2
            candidate = test_input[:mid]
            try:
                _, rc, _, _ = testing2(file_name_path, candidate)
                if rc == expected_returncode:
                    hi = mid
                else:
                    lo = mid
            except Exception:
                lo = mid
        return test_input[:hi]
