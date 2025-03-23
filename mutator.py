from random import randint, choice
import config
import main

fileik = open(config.dict_name, 'rb').read().decode().split('\r\n')
flag, trewq  = 0, 0
flag = 0

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

def mutate(buf, min_length, new_dict2, new_dict):
    mutation_types = ["length_ch", "ch_symb", "xor", "interesting"]
    mut_type = choice(mutation_types)
    ret = list(buf)

    if mut_type == "ch_symb":
        ret = rand_change_symbol(ret)
    elif mut_type == "length_ch":
        ret = rand_length_change(min_length, ret)
    elif mut_type == "xor":
        ret = xor(ret)
    elif mut_type == "interesting":
        return interesting_values(), mut_type

    if isinstance(ret, list):
        result = ''.join(ret)
    elif isinstance(ret, str):
        result = ret
    else:
        result = str(ret)
        
    return result, mut_type