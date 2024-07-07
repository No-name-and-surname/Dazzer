from random import *
import config

fileik = open(config.dict_name, 'rb').read().decode().split('\r\n')
flag, trewq  = 0, 0
def init(seed):
    random.seed(seed)


def deinit():
    pass

def mutate(buf, m_l, new_dict2, new_dict):
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
    Norm_or_rand = randint(0, 1)
    if Norm_or_rand == 0:
        global flag
        try:
            if len(new_dict) > 0:
                index_in_nd = randint(0, len(new_dict) - 1)
                ret = list(new_dict[index_in_nd])
                if len(ret) >= m_l-1:
                    flag = 1
                new_dict.remove(new_dict[index_in_nd])
            else:
                index_in_nd2 = randint(0, len(new_dict2) - 1)
                ret = list(new_dict2[index_in_nd2])
                if len(ret) >= m_l-1:
                    flag = 1
                new_dict2.remove(new_dict2[index_in_nd2])
        except:
            flag = 1
    if Norm_or_rand == 1 or flag == 1:
        ret = list(buf)
        Index_to_insert_random_symbol = randint(0, len(ret) - 1)
        newline = ''
        Up = randint(65, 90)
        Low = randint(97, 122)
        Up_or_low_case = randint(0, 1)
        Quantity_new_symbols = randint(0, m_l)
        Del_or_add = randint(0, 1)
        
        if Up_or_low_case == 0:
            new_letter = chr(Up)
        else:
            new_letter = chr(Low)
        ret[Index_to_insert_random_symbol] = new_letter
        for i in range(Quantity_new_symbols):
            if len(ret) == m_l-1:
                break
            j = randint(65, 122)
            newline += chr(j)
            if i < len(ret):
                ret[i] = chr(ord(ret[i]) ^ ord(chr(j)))
                if ord(ret[i]) < 33 or ord(ret[i]) > 126:
                    ret[i] = chr(randint(33, 126))
        if Del_or_add == 0:
            if Quantity_new_symbols >= len(ret):
                ret += newline[:m_l-1]
            else:
                ret = ret[:m_l-1]
        else:
            ret += newline[:m_l-1]
    return ''.join(ret)

