import calibrator
import mutator
import config
import copy
from pwn import *
with open(config.output_file, 'w') as filik:
    print("Hi, i hope you've already read README, so good luck")
    sleep(1)
    sig_segvi, time_out, no_error, sig_fpe = calibrator.ret_globals()
    if config.FUZZ not in config.args:
        calibrator.calibrate(copy.deepcopy(config.args), filik)
        calibrator.results_asd()
    else:
        print('So here it is: ')
        calibrator.calibrate(copy.deepcopy(config.args), filik)

    print("Now, i want to mutate your input, are you ready? [Y/n]")
    if input() != 'no':
        sleep(0.5)
        if len(sig_segvi) != 0:
            for i in range(len(sig_segvi)):
                res = calibrator.seg_segv(i)
                print(res)
            print("Do you want to mutate your input more? [Y/n]")
            if input() != 'no':
                for _ in range(int(input('How many times you want to mutate data: '))):
                    for i in range(len(sig_segvi)):
                        f = chr(randint(97, 122))
                        try:
                            if len(res[i][3]) > 1:
                                for j in range(len(res[i][3])):
                                    nn = mutator.mutate(f, res[i][2])
                                    res[i][3][j] = nn
                                    calibrator.calibrate(res[i][3], filik)
                            else:
                                mm = mutator.mutate(f, res[i][2])
                                calibrator.calibrate([mm], filik)
                        except:
                            break
                    calibrator.results_asd()
        elif len(no_error) != 0 or len(sig_fpe) != 0:
            if len(no_error) != 0:
                for i in range(len(no_error)):
                    my_err = copy.deepcopy(no_error)
                    res = calibrator.no_error_try(i, my_err)
                calibrator.results_asd()
                print(no_error)
                print("Do you want to mutate your input more? [Y/n]")
                if input() != 'no':
                    for _ in range(int(input('How many times you want to mutate data: '))):
                        for i in range(len(my_err)):
                            if len(my_err[i][1]) > 1:
                                for j in range(len(my_err[i][1])):
                                    f = chr(randint(97, 122))
                                    nn = mutator.mutate(f, 100)
                                    my_err2 = copy.deepcopy(my_err)
                                    my_err2[i][1][j] = nn
                                    calibrator.calibrate(my_err2[i][1], filik)
                            else:
                                f = chr(randint(97, 122))
                                mm = mutator.mutate(f, 100)
                                calibrator.calibrate([mm], filik)
                calibrator.results_asd()
            else:
                for i in range(len(sig_fpe)):
                    sig_fpe_1 = copy.deepcopy(sig_fpe)
                    res = calibrator.no_error_try(i, sig_fpe_1)
                calibrator.results_asd()
                print(sig_fpe)
                print("Do you want to mutate your input more? [Y/n]")
                if input() != 'no':
                    for _ in range(int(input('How many times you want to mutate data: '))):
                        for i in range(len(sig_fpe_1)):
                            if len(sig_fpe_1[i][1]) > 1:
                                for j in range(len(sig_fpe_1[i][1])):
                                    f = chr(randint(97, 122))
                                    nn = mutator.mutate(f, 100)
                                    sig_fpe_2 = copy.deepcopy(sig_fpe_1)
                                    sig_fpe_2[i][1][j] = nn
                                    calibrator.calibrate(sig_fpe_2[i][1], filik)
                            else:
                                f = chr(randint(97, 122))
                                mm = mutator.mutate(f, 100)
                                calibrator.calibrate([mm], filik)
                calibrator.results_asd()

