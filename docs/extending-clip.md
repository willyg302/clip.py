This section will show you how to extend clip to support your own CLI needs. We will be adding a new parameter type: a "choice" option! This option is a single value that must be chosen from a list of valid values.

> **NOTE**: It might be tempting to submit pull requests for your awesome extensions to be included in clip core, but one of clip's goals is to be "lean and mean". Instead, we prefer to **make it easy to write extensions**. Thus, if you run into any stumbling blocks while writing your own extensions, please submit an issue or pull request describing the issue! We'll try to iron it out quickly.

Now that we've gotten that out of the way, it's time to get started.

## Making the `Choice` Class

Our first task is to actually create the class describing our new parameter type. First, some boilerplate:

```python
class Choice(clip.Option):
	'''A special option that must be chosen from a list of valid values.

	The default value will be the first item of the list.
	'''

	def __init__(self, param_decls, **attrs):
		# @TODO
		clip.Option.__init__(self, param_decls, **attrs)

	def consume(self, tokens):
		# @TODO
		return tokens
```

Since this is an option, we inherit from `clip.Option` and call its `__init__` method in our own constructor. We'll also have some interesting custom logic for consuming tokens, so we'll be overriding the `consume()` method. This must necessarily return the modified `tokens` array, so for now we just return it unmodified.

### Initializing

Before diving into code, let's take a step back and think about the logic of a choice. We know we want to have the value of the parameter be one of a list of provided valid values; this means that we must add a custom attribute (let's call it `choices`) that is a list. We must also handle the `default` case -- here, we will say that the first item of the list is the default. Furthermore, the user's choice will consist of a single value, so `nargs` *must* be 1.

When writing extensions, you must consider not only possible user errors but possible mistakes that programmers could make while using your extensions. So, what could go wrong here? A number of things, really:

- Someone could forget to specify `choices`
- `choices` could be something other than a list
- `choices` could be an empty list

Alright, so let's turn this into code!

```python
try:
	self._choices = attrs.pop('choices')
except KeyError:
	raise AttributeError('You must specify the choices to select from')
if not isinstance(self._choices, list) or len(self._choices) == 0:
	raise AttributeError('"choices" must be a nonempty list of valid values')
attrs['nargs'] = 1
attrs['default'] = self._choices[0]
```

Dump that into your `__init__` function *before* the call to the parent constructor, and you'll be good to go.

### Consuming

We now turn our attention to the task of consuming a token. This is actually much simpler; we check to see if the given value is a valid choice, and if it is we consume it. Otherwise, we raise a nice error describing the problem to the user. Here's what that looks like:

```python
tokens.pop(0)  # Pop the choice from the tokens array
selected = tokens.pop(0)
if selected not in self._choices:
	clip.exit('Error: "{}" is not a valid choice (choose from {}).'.format(selected, ', '.join(self._choices)), True)
clip.Parameter.post_consume(self, selected)
```

Remember that the first token in `tokens` is the parameter declaration itself (in the case of an option), so we have to pop that first. The next token is our user's selection.

### The Decorator

To turn our custom class into a decorator, we need only call a single function:

```python
def choice(*param_decls, **attrs):
	return clip._make_param(Choice, param_decls, **attrs)
```

Be careful with the arguments here: the first argument to `_make_param` is the name of the class to wrap, and the second is the **packed** `param_decls` (note the absence of the `*`). You pass the `**attrs` through normally.

### The Final Code

If you've been following along, you should have this:

```python
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
```

And that's it! Now it's time to actually use our new parameter type.

## The Sorting Program

For lack of something better to do, we'll create a program that lets the user select a sorting algorithm to use and then does absolutely nothing with that choice. Here's what it looks like:

```python
@app.main()
@choice('-t', '--type', name='sort_type', choices=['quicksort', 'bubblesort', 'mergesort'])
def sort(sort_type):
	clip.echo('You selected {}'.format(sort_type))
```

And the functionality:

```
$ python sort.py 
You selected quicksort
$ python sort.py -t spaghettisort
Error: "spaghettisort" is not a valid choice (choose from quicksort, bubblesort, mergesort).
$ python sort.py -t mergesort
You selected mergesort
```
