from random import *
import config

fileik = open(config.dict_name, 'rb').read().decode().split('\r\n')
flag, trewq  = 0, 0

def xor(ret):
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
        g = ret[i]
        ret[i] = chr(ord(g) ^ new_letter)
    return ret

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

def rand_length_change(min_length, ret):
    newline = ''
    Del_or_add = randint(0, 1)
    Quantity_new_symbols = randint(0, min_length)
    for i in range(Quantity_new_symbols):
            if len(ret) == min_length-1:
                break
            j = randint(65, 122)
            newline += chr(j)
            if i < len(ret):
                ret[i] = chr(ord(ret[i]) ^ ord(chr(j)))
                if ord(ret[i]) < 33 or ord(ret[i]) > 126:
                    ret[i] = chr(randint(33, 126))
    if Del_or_add == 0 or Del_or_add == 2:
        if Quantity_new_symbols >= len(ret):
            return ret[:min_length-1]
        else:
            return ret[:len(ret) - Quantity_new_symbols-1]
    else:
        ret += newline[:min_length-1]
        return ret

def rand_change_symbol(ret):
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

def mutate(buf, min_length, new_dict2, new_dict):
    if len(new_dict) == 0 and trewq == 0:
        for i in fileik:
            if i.startswith(buf.lower()) == True:
                if list(buf)[0].lower() != list(buf)[0]:
                    i = list(i)
                    i[0] = i[0].upper()
                    new_dict.append(''.join(i))
                else:
                    new_dict.append(i)
            elif buf in i:
                new_dict2.append(i)
    Norm_or_rand = randint(0, 2)
    if Norm_or_rand == 0:
        global flag
        try:
            ret_1, flag = dict_test(min_length, new_dict2, new_dict)
        except:
            flag = 1
    if Norm_or_rand == 1 or Norm_or_rand == 2 or flag == 1:
        ret = list(buf)
        ret_1 = list(buf)
        choose = randint(0, 2)
        if choose == 0:
            try:
                ret_1 = rand_change_symbol(ret)
            except:
                choose = randint(1, 2)
        if choose == 1:
            try:
                ret_1 = rand_length_change(min_length, ret)
            except:
                choose = 2
        if choose == 2:
            try:
                ret_1 = xor(ret)
            except:
                pass
    return ''.join(ret_1)

