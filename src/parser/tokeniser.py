FILEPATH = '..\\..\\examples\\box_height\\obj\\box2.obj'

def tokeniser(obj_input):
	#take input and put in array of dict tokens

	current = 0
	token = {'type':'type', 'value':'value'}
	tokens = []

	#print obj_input

	while current < len(obj_input) - 1:

		char = obj_input[current]

		# letters
		if char.isalpha():

			value_str = ''

			while char.isalpha():
				value_str += char
				current += 1
				char = obj_input[current]

			token['type'] = 'name'
			token['value'] = value_str

			tokens.append(token.copy())

			continue

		# numbers
		if char in '0123456789./':

			value_str = ''

			while char in '0123456789./':
				value_str += char
				current += 1
				print current
				char = obj_input[current]

			token['type'] = 'number'
			token['value'] = value_str
			
			tokens.append(token.copy())

			continue

		# whitespace
		if char == ' ':
			current += 1

		# kind of an else for random chars
		current += 1

	return tokens

def parser(tokens):
	# Take array of tokens and make it in to an AST
	current = 0

	token = tokens[current]


def get_obj():

	obj_input = []

	with open(FILEPATH) as f:
		while True:
			c = f.read(1)
			if not c:
				break
			obj_input.append(c)

	#print obj_input
	return obj_input


if __name__ == '__main__':
	# tokeniser([1,1,1,1,1,1])
	obj_input = get_obj()

	tokens = tokeniser(obj_input)
	
	for i, a in enumerate(tokens):
		print tokens[i]

	parser(tokens)