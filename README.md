# hack-compiler

This compiler is written in Python as part of the nand2tetris course projects.
https://www.coursera.org/learn/build-a-computer

It is a first of two steps two-tier compilation mechanism to compile Jack programming language down into binary codes. 

The compiler receives a high-level code written in Jack - a programmigng language specification developed for the course - then it translates the code to VM instructions.

Next these VM instructions either run on a virtual machine implementation or is translated down to assembly code by a VM translator. This should be the second step in the two-tier compilation mechanism.

Eventually, the assembly code is translated by the Hack assembler (github.com/khelnagar/hack-assembler) into binary code that runs on the Hack computer architecture developed during the course.

