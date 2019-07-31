from symbol_table import SymbolTable
from vm_writer import VMWriter



class CompilationEngine:
	"""
	The input is a JackTokenizer object containing stream of tokens broken according 
	to the Jack compiler specification.

	It does syntax analysis using a recursive routine calls on the tokens generated 
	to output VM code as first step in a two-tier compilation method.

	Second step (not relevant here) is to take the generated VM code to be translated 
	into assembly instruction according to the Hack computer architecture.
	"""

	IF_COUNTER = 0
	WHILE_COUNTER = 0
	OUTPUT_XML = []

	def __init__(self, tokenizer):
		self.tokenizer = tokenizer
		self.symbol_table = None
		self.vm_writer = None
		self.var_count = 0 # used for the object memory allocation
		self.compile_class()
	
	def __del__(self):
		CompilationEngine.IF_COUNTER = 0
		CompilationEngine.WHILE_COUNTER = 0
		CompilationEngine.OUTPUT_XML = []
		
	def if_label(self, case):
		label = f'if_{case}{CompilationEngine.IF_COUNTER}'.upper()
		return label

	def while_label(self, case):
		label = f'while_{case}{CompilationEngine.WHILE_COUNTER}'.upper()
		return label
	
	def segment(self, term):
		segment_switcher = {
			'field': 'this',
		}

		if term.isdigit():
			term_segment, term_index = 'constant', term
		elif term == 'this':
			term_segment, term_index = 'pointer', 0
		elif term == 'null':
			term_segment, term_index = 'constant', 0
		elif term == 'false':
			term_segment, term_index = 'constant', 0
		else:
			term_segment = self.symbol_table.kind_of(term)
			term_index = self.symbol_table.index_of(term)
		
		return segment_switcher.get(term_segment, term_segment), term_index
	
	def eat(self, string):
		if string != self.tokenizer.current_token():
			raise ValueError(f'Unexpected token {string}')
		else:
			self.tokenizer.advance()
	
	def is_class_obj(self, fun_call):
		"""
		fun_call can be foo.bar() or Foo.bar()
		
		if type of foo is found in symbol table	with type not int, char, or boolean so it's 
		an object declared with a class type - ex: var Point foo; >> returns True
		
		if type of Foo is None(not in symbol table) ex: Main.main so it's a class or OS call 
		>> returns False
		"""
		
		return self.symbol_table.type_of(fun_call) not in ['int', 'char', 'boolean', None]


	def compile_parameterList(self):
		# if there are params passed to the subroutineDec
		if self.tokenizer.current_token() != ')':
			# add rest of subroutine parameters
			ident_kind = 'argument'
			ident_type = self.tokenizer.current_token()
			self.eat(ident_type) # type
			ident_name = self.tokenizer.current_token()
			self.symbol_table.define_identifier(
					ident_name,
					ident_type,
					ident_kind
				)
			self.eat(ident_name) # varName

			# check if more declarations to go
			while self.tokenizer.current_token() == ',':
				self.eat(',')
				ident_type = self.tokenizer.current_token()
				self.eat(ident_type) # type
				ident_name = self.tokenizer.current_token()
				# add to subroutine symbol_table
				self.symbol_table.define_identifier(
					ident_name,
					ident_type,
					ident_kind
				)
				self.eat(ident_name) # varName
		
	def compile_varDec(self):
		# n_vars needed for function declaration in vm 
		# ex: function Main.main 3
		n_vars = 0
		while self.tokenizer.current_token() == 'var':
			n_vars += 1
			self.eat('var')

			# add var declarations to subroutine symbol_table
			ident_kind = 'local'
			ident_type = self.tokenizer.current_token()
			self.eat(ident_type) # type
			ident_name = self.tokenizer.current_token()
			self.symbol_table.define_identifier(
					ident_name,
					ident_type,
					ident_kind
				)
			self.eat(ident_name) # varName

			while self.tokenizer.current_token() == ',':
				self.eat(',')
				ident_name = self.tokenizer.current_token()
				self.symbol_table.define_identifier(
					ident_name,
					ident_type,
					ident_kind
				)
				self.eat(ident_name) # varName

				n_vars += 1

			self.eat(';')
		
		return n_vars

	def compile_expressionList(self):
		n_args = 0
		# if there are args passed to the subroutineCall
		if self.tokenizer.current_token() != ')':
			n_args = 1
			self.compile_expression()
			while self.tokenizer.current_token() == ',':
				self.eat(',')
				self.compile_expression()
				n_args += 1

		return n_args

	def compile_term(self):
		if self.tokenizer.current_token() == '(': # (expression)
			self.eat('(')
			self.compile_expression()
			self.eat(')')
		elif self.tokenizer.current_token() in ['-', '~']: # unaryOp 
			op = self.tokenizer.current_token() 
			self.eat(op) # unaryOp
			self.compile_term()
			self.vm_writer.write_arithmatic(op if op == '~' else 'neg')
		else:
			term = self.tokenizer.current_token() # foo
			if term == 'true':
				self.vm_writer.write_push('constant', 0)
				self.vm_writer.write_arithmatic('~')
			elif term in ['false', 'null'] or term.isdigit() or self.symbol_table.kind_of(term):
				term_segment, term_index = self.segment(term)
				self.vm_writer.write_push(term_segment, term_index)
			elif self.tokenizer.token_type() == 'STRING_CONST':
				self.vm_writer.write_push('constant', len(term))
				self.vm_writer.write_call('String.new', 1)
				for ch in term:
					# ord(ch) gets the ASCII code for each character
					self.vm_writer.write_push('constant', ord(ch))
					self.vm_writer.write_call('String.appendChar', 2)
			self.eat(term)

			if self.tokenizer.current_token() == '[': # foo[expression]
				self.eat('[')
				self.compile_expression()
				self.vm_writer.write_arithmatic('+')
				self.eat(']')
				self.vm_writer.write_pop('pointer', 1)
				self.vm_writer.write_push('that', 0)
			elif self.tokenizer.current_token() == '(': # foo(expressionList)
				self.eat('(')
				# function cannot be called directly unless it resides in 
				# its own class so, pass the current object as first argument
				self.vm_writer.write_push('pointer', 0)
				term = f'{self.symbol_table.st_class_name()}.{term}'
				this_increment = 1
				n_args = self.compile_expressionList() + this_increment
				self.vm_writer.write_call(term, n_args)
				self.eat(')')
			elif self.tokenizer.current_token() == '.': # foo.bar(expressionList)
				self.eat('.')
				this_increment = 0
				other_term = self.tokenizer.current_token()
				if self.is_class_obj(term):
					# obtain the class of the object for the call
					class_type = self.symbol_table.type_of(term)
					term = f'{class_type}.{other_term}'
					this_increment = 1
				else:
					# OS class or function call
					term += f'.{other_term}'
				self.eat(other_term)
				self.eat('(')
				n_args = self.compile_expressionList() + this_increment
				self.vm_writer.write_call(term, n_args)
				self.eat(')')

	def compile_expression(self):
		self.compile_term()
		while self.tokenizer.current_token() in ['+', '-', '*', '/', '&', '|', '<', '>', '=']:
			op = self.tokenizer.current_token() # op
			self.eat(op)
			self.compile_term()
			self.vm_writer.write_arithmatic(op)
	
	def compile_let(self):
		self.eat('let')
		var = self.tokenizer.current_token() # foo
		self.eat(var)
		# looking ahead one more step LL(2)
		symbol = self.tokenizer.current_token() 
		if self.tokenizer.current_token() == '[':
			# array manipulation
			var_segment, var_index = self.segment(var)	
			self.vm_writer.write_push(var_segment, var_index)
			self.eat('[')
			self.compile_expression()
			self.vm_writer.write_arithmatic('+')
			self.eat(']')
		elif self.tokenizer.current_token() == '(':
			self.eat('(')
			self.compile_expressionList()
			self.eat(')')
		elif self.tokenizer.current_token() == '.':
			self.eat('.')
			self.eat(self.tokenizer.current_token())
			self.eat('(')
			self.compile_expressionList()
			self.eat(')')
		self.eat('=')
		self.compile_expression()

		if symbol == '[':
			self.vm_writer.write_pop('temp', 0)
			self.vm_writer.write_pop('pointer', 1)
			self.vm_writer.write_push('temp', 0)
			self.vm_writer.write_pop('that', 0)
		else:
			var_segment, var_index = self.segment(var)
			self.vm_writer.write_pop(var_segment, var_index)

		self.eat(';')

	def compile_if(self):
		self.eat('if')
		self.eat('(')
		self.compile_expression()

		label_true = self.if_label('true')
		label_false = self.if_label('false')
		label_end = self.if_label('end')
		
		# increment the if statement label counter in current scope
		CompilationEngine.IF_COUNTER += 1
		
		self.vm_writer.write_if(label_true) # if true, jump to if
		# if not true, go to else
		self.vm_writer.write_goto(label_false)
		self.eat(')')
		self.eat('{')
		self.vm_writer.write_label(label_true)
		self.compile_statements()
		self.vm_writer.write_label(label_false)
		self.eat('}')
		if self.tokenizer.current_token() == 'else':
			self.eat('else')
			self.eat('{')
			self.vm_writer.write_goto(label_end)
			self.compile_statements()
			self.eat('}')
			self.vm_writer.write_label(label_end)

	def compile_while(self):
		self.eat('while')
		self.eat('(')
		
		label_exp = self.while_label('exp')
		label_end = self.while_label('end')
		
		# increment the while statement label counter in current scope
		CompilationEngine.WHILE_COUNTER += 1
		
		self.vm_writer.write_label(label_exp)
		self.compile_expression()
		self.vm_writer.write_arithmatic('~')
		self.vm_writer.write_if(label_end)
		self.eat(')')
		self.eat('{')
		self.compile_statements()
		self.vm_writer.write_goto(label_exp)
		self.vm_writer.write_label(label_end)
		self.eat('}')

	def compile_do(self):
		self.eat('do')
		callee = self.tokenizer.current_token()
		self.eat(callee)
		this_increment = 0
		if self.tokenizer.current_token() == '(': # foo(expressionList)
			# method cannot be called directly unless it resides in its 
			# own class, so pass the current object as first argument
			self.vm_writer.write_push('pointer', 0)
			callee = f'{self.symbol_table.st_class_name()}.{callee}'
			this_increment = 1
		else: # foo.bar(expressionList)
			self.eat('.')
			other_callee = self.tokenizer.current_token()
			# if object declared, pass the object as first argument
			if self.is_class_obj(callee):
				callee_segment, callee_index = self.segment(callee)
				self.vm_writer.write_push(callee_segment, callee_index)
				# obtain the class of the object for the call
				class_type = self.symbol_table.type_of(callee)
				callee = f'{class_type}.{other_callee}'
				this_increment = 1
			else:
				# OS class or function call
				callee += f'.{other_callee}'
			self.eat(other_callee)

		self.eat('(')
		n_args = self.compile_expressionList() + this_increment			
		self.vm_writer.write_call(callee, n_args)
		self.vm_writer.write_pop('temp', 0)
		self.eat(')')
		self.eat(';')

	def compile_return(self):
		self.eat('return')
		term = self.tokenizer.current_token()
		if term != ';':
			self.compile_expression()
			if term == 'this':
				term_segment, term_index = self.segment(term)
				self.vm_writer.write_push(term_segment, term_index)
			self.vm_writer.write_return('return')
		else:
			self.vm_writer.write_push('constant', 0)
			self.vm_writer.write_return('return')
		self.eat(';')

	def compile_statements(self):
		while self.tokenizer.current_token() in ['let', 'if', 'while', 'do', 'return']:
			statement_method = f'compile_{self.tokenizer.current_token()}'
			_compile_method = getattr(self, statement_method)
			_compile_method()

	def compile_subroutineBody(self):
		self.compile_varDec()
		self.compile_statements()

	def compile_subroutineDec(self):
		while self.tokenizer.current_token() in ['constructor', 'function', 'method']:
			# reset a new subroutine table
			self.symbol_table.start_subroutine()
			
			# reset the if & while statements label counter
			CompilationEngine.IF_COUNTER = 0
			CompilationEngine.WHILE_COUNTER = 0
			
			subroutine = self.tokenizer.current_token() # 'constructor', 'function', 'method'
			# for every new method subroutine 'this' is passed as first arg
			if subroutine == 'method':
				self.symbol_table.subroutine_level['this'] = {
					'type': self.symbol_table.class_name, 'kind': 'argument', 'index': 0 
				}
			
			self.eat(subroutine)
			subroutine_type = self.tokenizer.current_token() # type
			# this number should reflect the named var declarations
			# in each subroutine.. and I do not know how to get this number
			# before even entring the compile_subroutineBody() routine!
			n_locals = 0
			self.eat(subroutine_type)
			subroutine_name = self.tokenizer.current_token()
			name = f'{self.symbol_table.st_class_name()}.{subroutine_name}' # name
			self.vm_writer.write_function(name, n_locals)
			self.eat(subroutine_name)
			self.eat('(')
			self.compile_parameterList() # subroutine args
			
			# create space in memory for the object
			if subroutine == 'constructor':
				self.vm_writer.write_push('constant', self.var_count)
				self.vm_writer.write_call('Memory.alloc', 1)
				self.vm_writer.write_pop('pointer', 0)
			elif subroutine == 'method':
				self.vm_writer.write_push('argument', 0)
				self.vm_writer.write_pop('pointer', 0)

			self.eat(')')
			self.eat('{')
			self.compile_subroutineBody() # subroutine body
			self.eat('}')

	def compile_classVarDec(self):
		n_class_var = 1
		ident_kind = self.tokenizer.current_token()
		self.eat(ident_kind) # static|field
		ident_type = self.tokenizer.current_token()
		self.eat(ident_type) # type
		ident_name = self.tokenizer.current_token()
		self.symbol_table.define_identifier(
				ident_name,
				ident_type,
				ident_kind
			)
		self.eat(ident_name) # varName

		# check if more declarations to go
		while self.tokenizer.current_token() == ',':
			self.eat(',')
			ident_name = self.tokenizer.current_token()
			self.symbol_table.define_identifier(
				ident_name,
				ident_type,
				ident_kind
			)
			self.eat(ident_name) # varName

			n_class_var += 1

		self.eat(';')
		
		# we need memory only for object fields
		if ident_kind == 'static':
			n_class_var = 0
		
		return n_class_var

	def compile_class(self):
		self.tokenizer.advance()
		self.eat('class')

		class_name = self.tokenizer.current_token()

		# create a new symbol table and vm writer
		self.symbol_table = SymbolTable(class_name)
		self.vm_writer = VMWriter()
		
		self.eat(class_name)
		self.eat('{')
		while self.tokenizer.current_token() in ['static', 'field']:
			n_class_var = self.compile_classVarDec()
			self.var_count += n_class_var
		self.compile_subroutineDec()
		self.eat('}')