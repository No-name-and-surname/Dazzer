# Dazzer

Hi there, Dazzer is Fuzzer :) 

![Image alt](https://github.com/No-name-and-surname/imagere/raw/main/pixil-frame-0 (7).png)


## Instaling

So, closer to the point, to install Dazzer you should run a few simple commands:

```
   git clone git@github.com:No-name-and-surname/Dazzer.git
   cd Dazzer
```

## Get started

Firstly, you should pay attention to  `config.py`  file.
It contains five variables: 
   * FUZZ - constant variable, which one should be inserted in place of the element specifically that you want to fuzz separately from other elements in the initially specified test. (args) 
   * args - a list there should be inserted initial test input. ❗IMPORTANT❗ if you'll set less or more input data than the program requires, the fuzzer won't work.
   * file_name - here should be inserted the name of programm you want fuzz. By default it is  `Test_examples/trees`. (one of the test programms)
   * output_file - a file in which the results are saved after the program is execute. By default it is  `output.txt`, but you can create your own file.
   * dict_name - by default it is equal to the pre-downloaded dictionary. But you can download yours and change it.
After you've finished previous part, you should just run:

```
   python3 main.py
```
