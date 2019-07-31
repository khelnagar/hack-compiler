class SymbolTable:
	"""
	It provides a container to save identifiers such as local variables in a subroutine
	table, and field & static variables in a class level table.

	For each identifier saved, a running index as the identifier appears is associated.

	This interface provides an API for the compilation engine to use during compile time.

	name - type  - kind     - index
	p1   - Point - local    - 0
	p2   - Point - local    - 1
	x    - int   - argument	- 0
	"""
	
	def __init__(self, name):
		self.class_name = name
		self.class_level = {}
		self.subroutine_level = {}
	
	def st_class_name(self):
		return self.class_name

	def start_subroutine(self):
		# resets the subroutine table
		self.subroutine_level = {}
		
	def new_index(self, kind):
		if kind in ['field', 'static']:
			s_table = self.class_level
		else:
			s_table = self.subroutine_level

		kind_entries = list(filter(lambda obj: obj['kind'] == kind, s_table.values()))
		return len(kind_entries)

	def index_of(self, name):
		class_level_lookup = self.class_level.get(name, None)
		index_lookup = self.subroutine_level.get(name, class_level_lookup)
		return index_lookup.get('index')

	def type_of(self, name):
		"""
		returns the type of the identifier which can be one of the following
		int, char, boolean, or a class type such as Point.
		"""

		class_level_lookup = self.class_level.get(name, None)
		type_lookup = self.subroutine_level.get(name, class_level_lookup)
		
		return type_lookup.get('type') if type_lookup else None

	def kind_of(self, name):
		"""
		returns one of the following local, argument, static, field or None
		in case of subroutine name or a class name.
		"""

		class_level_lookup = self.class_level.get(name, None)
		kind_lookup = self.subroutine_level.get(name, class_level_lookup)
		
		return kind_lookup.get('kind') if kind_lookup else None

	def define_identifier(self, name, _type, kind):
		"""
		index starts at 0 so length of existing identifiers should be the 
		index of the new identifier.
		len() == 0 >> first index is 0
		len() == 1 >> second index is 1
		"""
		
		if kind in ['field', 'static']:
			s_table = self.class_level
		else:
			s_table = self.subroutine_level		

		index = self.new_index(kind)
		s_table[name] = {
			'type': _type, 'kind': kind, 'index': index 
		}