from random import randint, choice
import config
import main
import random
import threading

fileik = open(config.dict_name, 'rb').read().decode().split('\r\n')
flag, trewq  = 0, 0
flag = 0

mutation_cache = {}
MAX_CACHE_SIZE = 10000

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

def update_mutation_success(mut_type, coverage_increased, new_crash):
    with mutation_success_lock:
        if mut_type in mutation_success:
            mutation_success[mut_type]["total"] += 1
            if coverage_increased:
                mutation_success[mut_type]["new_coverage"] += 1
            if new_crash:
                mutation_success[mut_type]["new_crash"] += 1

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

def dict_test(min_length, new_dict2, new_dict):
    flag = 0
    if len(new_dict) > 0:
        index_in_nd = randint(0, len(new_dict) - 1)
        ret = list(new_dict[index_in_nd])
        if len(ret) >= min_length-1:
            flag = 1
        new_dict.remove(new_dict[index_in_nd])
        return ret, flag
    else:
        index_in_nd2 = randint(0, len(new_dict2) - 1)
        ret = list(new_dict2[index_in_nd2])
        if len(ret) >= min_length-1:
            flag = 1
        new_dict2.remove(new_dict2[index_in_nd2])
        return ret, flag

def dict_test_via_rand(min_length, new_dict2, new_dict):
    flag = 0
    if len(new_dict) > 0:
        index_in_nd = randint(0, len(new_dict) - 1)
        ret = list(new_dict[index_in_nd])
        if len(ret) >= min_length-1:
            flag = 1
        new_dict.remove(new_dict[index_in_nd])
        return rand_length_change(min_length, ret), flag
    else:
        index_in_nd2 = randint(0, len(new_dict2) - 1)
        ret = list(new_dict2[index_in_nd2])
        if len(ret) >= min_length-1:
            flag = 1
        new_dict2.remove(new_dict2[index_in_nd2])
        return rand_length_change(min_length, ret), flag
    
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

def get_mutation_probabilities():
    with mutator_error_lock:
        probabilities = {}
        total_errors = sum(mutator_error_counts.values())
        
        if total_errors > 0:
            for mut in mutator_error_counts:
                probabilities[mut] = mutator_error_counts[mut] / total_errors
        
        total_prob = sum(probabilities.values())
        if total_prob > 0:
            for mut in probabilities:
                probabilities[mut] = (probabilities[mut] / total_prob) * 100
        
        return probabilities

def mutate(buf, min_length, new_dict2=None, new_dict=None):
    mutation_probs = get_mutation_probabilities()
    
    mutation_types = list(mutation_probs.keys())
    weights = list(mutation_probs.values())
    
    if not mutation_types:
        mutation_types = ["interesting", "ch_symb", "length_ch", "xor"]
        weights = [25, 25, 25, 25]  # Default weights if no data
    
    mut_type = random.choices(mutation_types, weights=weights, k=1)[0]
    
    cache_key = (str(buf), min_length)
    if cache_key in mutation_cache:
        return mutation_cache[cache_key]
    
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
        if len(mutation_cache) >= MAX_CACHE_SIZE:
            for k in list(mutation_cache.keys())[:1000]:
                del mutation_cache[k]
        mutation_cache[cache_key] = result
        return result

    if isinstance(ret, list):
        result = ''.join(ret)
    elif isinstance(ret, str):
        result = ret
    else:
        result = str(ret)
    
    if len(mutation_cache) >= MAX_CACHE_SIZE:
        for k in list(mutation_cache.keys())[:1000]:
            del mutation_cache[k]
    mutation_cache[cache_key] = (result, mut_type)
    
    return result, mut_type