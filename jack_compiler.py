import sys, os
from tokenizer import JackTokenizer
from compilation_engine import CompilationEngine



"""

Jack compiler accepts either a path to a Jack program file example.jack 
or a directory containing as many as Jack files.

Ex terminal command to run the compiler:
"python jack_compiler.py Square"

where Square is the path to the jack files relative
to the root of script jack_compiler.py

the output is a .vm file with path path\\to\\file_compiled.vm 

"""

def parse_file(file):
	tokenizer = JackTokenizer(file)
	c_engine = CompilationEngine(tokenizer)
	with open(file.split('.')[0] + '_compiled.vm', 'w') as f:
		for line in c_engine.vm_writer.get_vm_text():
			f.write(line)

# the jack file path is passed as a command line argument   
path = sys.argv[1]

if os.path.isfile(path) and path.endswith('.jack'):
	parse_file(path)
elif os.path.isdir(path):
	for file_name in os.listdir(path):
		if file_name.endswith('.jack'):
			parse_file(os.path.join(path, file_name))
else:
	raise IOError('Wrong path provided')



