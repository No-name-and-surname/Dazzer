import copy
global FUZZ, file_name, args, output_file, dict_name

FUZZ = "qW3r7y_A5d_4sD_1234567890" 
g = copy.deepcopy(FUZZ)
args = ['asd', '1', '1']
file_name = 'Test_examples/calc'
output_file = 'output.txt'
dict_name = 'dict.txt'
SEG_FAULT = False
ANOTHER = True