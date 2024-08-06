# Dazzer

Hi there, Dazzer is Fuzzer :) 

![Image alt](https://github.com/No-name-and-surname/imagere/raw/main/pix.png)

## How does it actually work?

As I've already written -  Dazzer is Fuzzer
So it's goal is to find as much bugs/vulns as it can.
Actually Dazzer can automatically determine the number of parameters that are required as input to the program using static analysis of the file as it executes and finding reading functions.
After it found how many inputs does programm need, it will start to calibrate and mutate inputs. 

Mutation includes such techniques as: random symbol changes, random length changes (by adding new symbols or just cutting some of them), 
replacement by close inputs in dict, random words from dict, and some mixed techniques.

And if we talk about calibrator, it can: find changes between program outputs on different tests and, based on the result, decide what to do with the inputs next (for example, if we received a segmentation fault, it will track the length of the input and will no longer send outputs of the same or longer length, which will allow the fuzzer to more productively search for other vulnerabilities),
also the determination of the amount of input data is determined precisely in it. So it's like fuzzer's brain.

The biggest advantage of Dazzer, is that it can be configured as it would be convenient for the user using `config.py` that will be reviewed later. 
If you are not sure if you understand how it would work or just want to test it, where are some test programms for which it can be run. (These programms are in Test_examples folder)

Here are some screens of it's work:

![Image alt](https://github.com/No-name-and-surname/imagere/raw/main/Screenshot%20from%202024-07-30%2014-47-07.png)

![Image alt](https://github.com/No-name-and-surname/imagere/raw/main/Screenshot%20from%202024-07-30%2014-45-17.png)


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
   * SEG_FAULT - by default it is set to *False*. If you change it to *True*, Dazzer will use the mutator function to generate tests to find a segmentation fault as often as other functions. If you leave the flag set to False, then the fuzzer will use       the mutator functions less to generate tests to find the segmentation fault.
After you've finished previous part, you should just run:

```
   python3 main.py
```
Then just follow the instructions
After Dazzer finish you should look into output_file

Some results:

![Image alt](https://github.com/No-name-and-surname/imagere/raw/main/Screenshot%20from%202024-07-30%2014-53-03.png)

## 
