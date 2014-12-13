import clip


class Choice(clip.Option):
	'''A special option that must be chosen from a list of valid values.

	The default value will be the first item of the list.
	'''

	def __init__(self, param_decls, **attrs):
		try:
			self._choices = attrs.pop('choices')
		except KeyError:
			raise AttributeError('You must specify the choices to select from')
		if not isinstance(self._choices, list) or len(self._choices) == 0:
			raise AttributeError('"choices" must be a nonempty list of valid values')
		attrs['nargs'] = 1
		attrs['default'] = self._choices[0]
		clip.Option.__init__(self, param_decls, **attrs)

	def consume(self, tokens):
		tokens.pop(0)  # Pop the choice from the tokens array
		selected = tokens.pop(0)
		if selected not in self._choices:
			clip.exit('Error: "{}" is not a valid choice (choose from {}).'.format(selected, ', '.join(self._choices)), True)
		clip.Parameter.post_consume(self, selected)
		return tokens


def choice(*param_decls, **attrs):
	return clip._make_param(Choice, param_decls, **attrs)


app = clip.App()

@app.main()
@choice('-t', '--type', name='sort_type', choices=['quicksort', 'bubblesort', 'mergesort'])
def sort(sort_type):
	clip.echo('You selected {}'.format(sort_type))

if __name__ == '__main__':
	try:
		app.run()
	except clip.ClipExit:
		pass
