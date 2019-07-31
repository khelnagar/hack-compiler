class VMWriter:
	"""
	VMWriter is the engine for VM code generating.

	It provides an interface API for the compilation engine to use during compile time.
	"""

	def __init__(self):
		self.output_vm = []

	def get_vm_text(self):
		return self.output_vm

	def write_push(self, segment, index):
		string = f'push {segment} {index}\n'
		self.output_vm.append(string)

	def write_pop(self, segment, index):
		string = f'pop {segment} {index}\n'
		self.output_vm.append(string)

	def write_arithmatic(self, command):
		op_dict = {
			'+': 'add',
			'-': 'sub',
			'*': 'call Math.multiply 2',
			'/': 'call Math.divide 2',
			'=': 'eq',
			'>': 'gt',
			'<': 'lt',
			'&': 'and',
			'|': 'or',
			'~': 'not'
		}

		# if not specified, so op is negate
		command = op_dict.get(command, 'neg')
		string = f'{command}\n'
		self.output_vm.append(string)
		
	def write_label(self, label):
		string = f'label {label}\n'
		self.output_vm.append(string)

	def write_goto(self, label):
		string = f'goto {label}\n'
		self.output_vm.append(string)

	def write_if(self, label):
		string = f'if-goto {label}\n'
		self.output_vm.append(string)

	def write_while(self, label):
		self.output_vm.append()

	def write_call(self, name, n_args):
		string = f'call {name} {n_args}\n'
		self.output_vm.append(string)

	def write_function(self, name, n_locals):
		string = f'function {name} {n_locals}\n'
		self.output_vm.append(string)
	
	def write_return(self, label):
		string = f'{label}\n'
		self.output_vm.append(string)