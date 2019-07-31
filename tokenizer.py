import re
import collections



KEYWORDS = [
	'class', 'constructor', 'function', 'method', 'field', 'static',
	'var', 'int', 'char', 'boolean', 'void', 'true', 'false',
	'null', 'this', 'let', 'do', 'if', 'else', 'while', 'return'
]

SYMBOLS = [
	'{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*',
	'/', '&', '|', '<', '>', '=', '~'
]

def is_symbol(s):
	return s in SYMBOLS

def is_keyword(s):
	return s in KEYWORDS
	
def is_whitespace(s):
	return s.strip() == ''

def is_quote(s):
	return s == '"'

def is_slash(s):
	return s == '/'

def is_newline(s):
	return s == '\n'

def is_star(ch):
	return ch =='*'
	
def start_of_comment(ch, next_ch):
	return is_slash(ch) and (is_slash(next_ch) or is_star(next_ch))

def is_comment_line(line):
	line = line.strip()
	return line.startswith('/') or line.endswith('/') or line.startswith('*')  
	
def get_quoted_text(text):
	"""Returns the string including quotes"""

	# string_constant = ''
	# idx = text.find('"') + 1
	# while True:
	# 	if is_quote(text[idx]):
	# 		break
	# 	string_constant += text[idx]
	# 	idx += 1
	
	# using regex
	string_constant = re.search(r'".*"', text).group(0)

	return string_constant

def get_comment_length(text):
	"""
	Returns the end of comment, so the marcher can ignore and jump
	"""

	# comment_text = ''
	# idx = text.find('/') + 1
	
	# # comment with double slash
	# if is_slash(text[idx]):
	# 	comment_text += text[idx]
	# 	idx += 1

	# while True:
	# 	if is_slash(text[idx]) or is_newline(text[idx]):
	# 		break

	# 	comment_text += text[idx]
	# 	idx += 1

	# using regex
	comment_text = re.search(r'\/\*(.|\n)*?\*\/|\/\/.*\n', text).group(0)

	return len(comment_text)

class JackTokenizer:
	"""
	The input is a Jack program file written in Jack programming language.

	It breaks the input into a stream of tokens. It is then
	passed to a CompilationEngine class to do the complete parsing of
	jack program into its tokens. 

	It classifies the tokens into lexical categories such as KEYWORD, 
	SYMBOL, etc. These categories are defined in the compiler specification.
	"""
	
	CURRENT_TOKEN_INDEX = -1
	OUTPUT_TOKENS = []

	def __init__(self, input_file):
		self.input_file = input_file
		self.cur_token = None
		self.tokenize_input()
	
	def __del__(self):
		"""
		destructor method is called so that the class variables are reinitialized
		for any new instance created
		"""
		
		JackTokenizer.CURRENT_TOKEN_INDEX = -1
		JackTokenizer.OUTPUT_TOKENS = []
		
	def __getattr__(self, attr):
		err_msg = 'Invalid attribute for current token type.'
		token_type = self.token_type()

		assert (attr, token_type) in [
					('keyword', 'KEYWORD'),
					('symbol', 'SYMBOL'),
					('identifier', 'IDENTIFIER'),
					('intVal', 'INT_CONST'),
					('stringVal', 'STRING_CONST')
				], err_msg
		
		return token_type
	
	def get_token_text(self):
		return JackTokenizer.OUTPUT_TOKENS
	
	def add_to_tokens(self, token):
		JackTokenizer.OUTPUT_TOKENS.append(token)

	def tokenize_input(self):
		with open(self.input_file) as jack_file:
			jack_text = jack_file.read()

			# data structure representing a token
			TOKEN = collections.namedtuple('TOKEN', 'value type')

			i = 0
			current_token = ''
			while i < len(jack_text):
				"""while loop is used instead of for..loop because the index i is used
				to jump over text as needed
				"""
				ch = jack_text[i]

				# handling inline comments and comment blocks
				if is_slash(ch):
					# not to include the dividing slash
					next_ch = jack_text[i + 1]
					if start_of_comment(ch, next_ch):
						comment_length = get_comment_length(jack_text[i:])

						# jump after the end of comment
						i += comment_length
						continue

				# handling string constants
				if is_quote(ch):
					quoted_text = get_quoted_text(jack_text[i:])
					self.add_to_tokens(TOKEN(quoted_text[1:-1], 'STRING_CONST'))

					# jump after the end of quote
					i += len(quoted_text)
					
					# start looking for a new token
					current_token = ''
					continue

				# a boundry is hit, inspect current token
				if is_whitespace(ch) or is_symbol(ch):
					if is_keyword(current_token):
						self.add_to_tokens(TOKEN(current_token, 'KEYWORD'))
					elif current_token.isdigit():
						self.add_to_tokens(TOKEN(current_token, 'INT_CONST'))
					else:
						# not to count any block of whitespace as identifier 
						if not is_whitespace(current_token):
							self.add_to_tokens(TOKEN(current_token, 'IDENTIFIER'))

					# if the boundry is symbol, add it as token
					if is_symbol(ch):
						self.add_to_tokens(TOKEN(ch, 'SYMBOL'))

					# start looking for a new token
					current_token = ''
				else:
					# if no boundry, continue marching through text
					current_token += ch

				# go to next character
				i += 1

	def has_more_tokens(self):
		return JackTokenizer.CURRENT_TOKEN_INDEX < len(JackTokenizer.OUTPUT_TOKENS) - 1

	def advance(self):
		if self.has_more_tokens():
			JackTokenizer.CURRENT_TOKEN_INDEX += 1
			self.cur_token = JackTokenizer.OUTPUT_TOKENS[JackTokenizer.CURRENT_TOKEN_INDEX]
		else:
			JackTokenizer.CURRENT_TOKEN_INDEX += 1

	def current_token(self):
		return self.cur_token.value
		
	def token_type(self):
		return self.cur_token.type