import sys, os
from tokenizer import JackTokenizer
from compilation_engine import CompilationEngine



def parse_file(file):
	tokenizer = JackTokenizer(file)
	c_engine = CompilationEngine(tokenizer)
	with open(file.split('.')[0] + '_.vm', 'w') as f:
		for line in c_engine.vm_writer.get_vm_text():
			f.write(line)

path = sys.argv[1]

if os.path.isfile(path) and path.endswith('.jack'):
	parse_file(path)
elif os.path.isdir(path):
	for file_name in os.listdir(path):
		if file_name.endswith('.jack'):
			parse_file(os.path.join(path, file_name))
else:
	raise IOError('Wrong path provided')



