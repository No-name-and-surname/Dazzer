import copy
global FUZZ, file_name, args, output_file, dict_name

FUZZ = "qW3r7y_A5d_4sD_1234567890" 
g = copy.deepcopy(FUZZ)
args = ['1', '1']
file_name = './Test_examples/cov_test'
source_file = "./Test_examples/cov_test.c" #if white type of fuzzing
output_file = 'output.txt'
dict_name = 'dict.txt'
FUZZING_TYPE = "Black" # Black/White/Gray
Corpus_dir = "out"
TARGET_HOST = "localhost"
TARGET_PORT = 1337
TIMEOUT = 5
