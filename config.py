import copy
global FUZZ, file_name, args, output_file, dict_name

FUZZ = "qW3r7y_A5d_4sD_1234567890" 
FUZZING_TYPE = "White" # Black/White/Gray

#Path to target file
file_name = './Test_examples/cov_test'

#Fuzzing arguments
args = ['1', '1']

#White Box
source_file = "./Test_examples/cov_test.c"

#Black Box
TARGET_HOST = "localhost"
TARGET_PORT = 1337
TIMEOUT = 5

#Results saving
output_file = 'output.txt'
dict_name = 'dict.txt'
Corpus_dir = "out"