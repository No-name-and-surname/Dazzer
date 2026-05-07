from random import randint, choice
import config
import random
import threading
import difflib

filik = open(config.dict_name, 'rb').read().decode().split('\r\n')
filik = [w for w in filik if w.strip()]
flag, trewq  = 0, 0
flag = 0

mut_cache = {}
MAX_CACHE = 10000

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

def upd_mut_sucs(mut_type, cov_up, new_crash):
    with mut_sucs_lock:
        if mut_type in mut_sucs:
            mut_sucs[mut_type]["total"] += 1
            if cov_up:
                mut_sucs[mut_type]["new_coverage"] += 1
            if new_crash:
                mut_sucs[mut_type]["new_crash"] += 1

def xor(ret):
    try:
        Up = randint(33, 90)
        Low = randint(97, 122)
        Strange = randint(122, 137)
        Up_or_low_case = randint(0, 3)
        if Up_or_low_case == 0:
            new_letter = Up
        elif Up_or_low_case == 1:
            new_letter = Low
        elif Up_or_low_case == 2 or Up_or_low_case == 3:
            new_letter = Strange
        
        for i in range(len(ret)):
            if len(ret[i]) == 1:
                g = ret[i]
                ret[i] = chr(ord(g) ^ new_letter)
            else:
                ret[i] = chr(Up ^ new_letter)
        return ret
    except:
        return ret + chr(randint(97, 122))

def rand_length_change(min_length, ret):
    newline = ''
    Del_or_add = randint(0, 1)
    Quantity_new_symbols = randint(0, min_length)
    for i in range(Quantity_new_symbols):
            if len(ret) == min_length-1:
                break
            j = randint(65, 122)
            newline += chr(j)
            try:
                if i < len(ret):
                    ret[i] = chr(ord(ret[i]) ^ ord(chr(j)))
                    if ord(ret[i]) < 33 or ord(ret[i]) > 126:
                        ret[i] = chr(randint(33, 126))
            except:
                continue
    if Del_or_add == 0 or Del_or_add == 2:
        if Quantity_new_symbols >= len(ret):
            return ret[:min_length-1]
        else:
            return ret[:len(ret) - Quantity_new_symbols-1]
    else:
        ret += newline[:min_length-1]
        return ret

def rand_change_symbol(ret):
    try:
        Index_to_insert_random_symbol = randint(0, len(ret) - 1)
        Up = randint(33, 90)
        Low = randint(97, 122)
        Strange = randint(122, 137)
        Up_or_low_case = randint(0, 3)
        if Up_or_low_case == 0:
            new_letter = chr(Up)
        elif Up_or_low_case == 1:
            new_letter = chr(Low)
        elif Up_or_low_case == 2 or Up_or_low_case == 3:
            new_letter = chr(Strange)
            ret[Index_to_insert_random_symbol] = new_letter
            return ret
    except:
        return list(ret)

def interesting_values():
    interesting = [
        '0', '1', '-1', 
        '127', '128', '129',
        '255', '256', '257',
        '32767', '32768', '32769',
        '65535', '65536', '65537',
        '-128', '-129', '-32768',
        '2147483647', '-2147483648',
        '4294967295', '4294967296',
        '9223372036854775807',
        '-9223372036854775808'
    ]
    return choice(interesting)

def dict_replace(buf):
    if isinstance(buf, str):
        buf_str = buf
    else:
        buf_str = ''.join(buf)
    if not filik:
        return buf_str

    strategy = randint(0, 2)

    if strategy == 0:
        close_ones = difflib.get_close_matches(buf_str, filik, n=5, cutoff=0.4)
        if close_ones:
            return choice(close_ones)

    if strategy <= 1:
        if len(buf_str) >= 2:
            matching = [w for w in filik if buf_str[:2].lower() == w[:2].lower()]
        else:
            matching = []
        if matching:
            return choice(matching)

    return choice(filik)

def get_probs():
    with err_lock:
        probs = {}
        total_err = sum(err_counts.values())
        
        if total_err > 0:
            for mut in err_counts:
                probs[mut] = err_counts[mut] / total_err
        
        total_prob = sum(probs.values())
        if total_prob > 0:
            for mut in probs:
                probs[mut] = (probs[mut] / total_prob) * 100
        
        return probs

def mutate(buf, min_length, new_dict2=None, new_dict=None):
    m_probs = get_probs()
    
    m_types = list(m_probs.keys())
    weights = list(m_probs.values())
    
    if not m_types:
        m_types = ["interesting", "ch_symb", "length_ch", "xor", "dict"]
        weights = [20, 20, 20, 20, 20]
    
    mut_type = random.choices(m_types, weights=weights, k=1)[0]
    
    cache_key = (str(buf), min_length)
    if cache_key in mut_cache:
        return mut_cache[cache_key]
    
    if new_dict2 is None: 
        new_dict2 = []
    if new_dict is None:
        new_dict = []
    
    ret = list(buf)

    if mut_type == "ch_symb":
        ret = rand_change_symbol(ret)
    elif mut_type == "length_ch":
        ret = rand_length_change(min_length, ret)
    elif mut_type == "xor":
        ret = xor(ret)
    elif mut_type == "interesting":
        result = interesting_values(), mut_type
        if len(mut_cache) >= MAX_CACHE:
            for k in list(mut_cache.keys())[:1000]:
                del mut_cache[k]
        mut_cache[cache_key] = result
        return result
    elif mut_type == "dict":
        dict_res = dict_replace(buf)
        result = (dict_res, mut_type)
        if len(mut_cache) >= MAX_CACHE:
            for k in list(mut_cache.keys())[:1000]:
                del mut_cache[k]
        mut_cache[cache_key] = result
        return result

    if isinstance(ret, list):
        result = ''.join(ret)
    elif isinstance(ret, str):
        result = ret
    else:
        result = str(ret)
    
    if len(mut_cache) >= MAX_CACHE:
        for k in list(mut_cache.keys())[:1000]:
            del mut_cache[k]
    mut_cache[cache_key] = (result, mut_type)
    
    return result, mut_type
