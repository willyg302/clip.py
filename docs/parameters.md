# Parameters

By themselves, commands don't really do anything. You leverage the real power of the command line by defining parameters for your app's commands.

There are a variety of parameter types (arguments, options, etc.), but they all share some common properties. When you define a parameter using a decorator, you pass it several required positional arguments followed by any number of optional keyword arguments, in Python referred to as `*args` and `**kwargs`, respectively.

In clip, the `*args` are known as *parameter declarations* and the `**kwargs` are called *parameter attributes*. Parameter declarations describe the parameter as it would be entered by users, and how you specify them depends on the parameter's type -- this will be covered a little further down. But first, let's look at some common parameter attributes.

## Common Attributes

### `name=None`

The name of the parameter. If not specified, a name will be inferred based on the parameter declarations based on the following rules:

- For an argument, the name is the single parameter declaration. For example, `@clip.arg('boo')` will be named `boo`.
- For an option with a long form, the name is the long form stripped of its leading dashes and with all dashes replaced by underscores. For example, `@clip.opt('--long-form')` will be named `long_form`.
- If an option has no long form, the name is the short form with its leading dash stripped. For example, `@clip.opt('-s')` will be named `s`.

However, sometimes you must explicitly specify the name. For example, `@clip.arg('list')` will have a name of `list`, but this masks the Python type of the same name. To remedy this, you could do the following:

```python
@app.main()
@clip.arg('list', name='list_arg')
def f(list_arg):
	return list(list_arg)
```

And things will work as expected.

### `nargs=1`

The number of tokens from the user's input that this parameter consumes. For `nargs=1`, the value of the parameter will be the consumed token. For `nargs` greater than 1, the value of the parameter will be a list of consumed tokens. To consume unlimited tokens, set `nargs=-1`. For example:

```python
@app.main()
@clip.arg('stuff', nargs=3)
def f(stuff):
	clip.echo('You entered: {}'.format(stuff))
```

Produces:

```
$ python f.py a
Error: Not enough arguments for "stuff".
$ python f.py a b
Error: Not enough arguments for "stuff".
$ python f.py a b c
You entered: ['a', 'b', 'c']
```

### `default=None`

The value for this parameter if none is given by the user. If `nargs` is greater than 1, this must be a list. For example:

```python
@app.main()
@clip.opt('--name', default='Joe')
def f(name):
	clip.echo('Hello {}!'.format(name))
```

Produces:

```
$ python f.py
Hello Joe!
$ python f.py --name Dave
Hello Dave!
```

You can also pass a function whose return value will become the parameter's value:

```python
def random_list():
	import random
	return random.sample(range(30), 3)

@app.main()
@clip.arg('random', nargs=3, default=random_list, type=int)
def f(random):
	clip.echo(random)
```

This will produce:

```
$ python f.py 1 2 3
[1, 2, 3]
$ python f.py 
[21, 28, 1]
$ python f.py 
[28, 26, 3]
```

Note that if you pass a function, it is impossible for clip to ensure that the return value conforms to your parameter's other attributes. You should therefore take special care to make sure that your program handles default values correctly in this case.

### `type=None`

A type to coerce the parameter's value into. If no type is provided, the type of the default value is used. If no default value is provided, the type is assumed to be a string. For example:

```python
@app.main()
@clip.arg('numbers', nargs=-1, default=[1, 2, 3])
def f(numbers):
	clip.echo(sum(numbers))
```

Produces:

```
$ python f.py 2 4 6 8 10
30
$ python f.py wuuutttt
Error: Invalid type given to "numbers", expected int
```

In the above example, we provided a *list* of numbers to `default` because `nargs` was greater than 1. However, the type was still inferred properly.

### `required=False`

If true, this parameter must appear in the user input. If it does not, an error will be raised. For example:

```python
@app.main()
@clip.flag('--needed', required=True)
def f(needed):
	clip.echo('Ahh, I needed that.')
```

Produces:

```
$ python f.py 
Error: Missing parameter "needed".
$ python f.py --needed
Ahh, I needed that.
```

Note that it normally doesn't make much sense to have required options, but the option is there should you require it (pun completely intended).

### `callback=None`

A function to invoke once this parameter has been matched in the input. It takes a single argument, the value of the parameter. For example:

```python
def shout(value):
	clip.echo(' '.join(value).upper())

@app.main()
@clip.arg('words', nargs=-1, callback=shout)
def f(words):
	pass
```

Produces:

```
$ python f.py i feel da powah!
I FEEL DA POWAH!
```

### `hidden=False`

If true, this parameter will not be passed to the owning command. This concept is best understood with an example:

```python
def print_version(value):
	clip.exit('Version 0.0.0')

@app.main()
@clip.flag('--version', callback=print_version, hidden=True)
def f():
	pass
```

Had we not set `hidden=True`, we would have had to write `def f(version)`, which doesn't make much sense. As you can see, `hidden` is especially useful for such things as version flags.

### `inherit_only=False`

Mark this parameter as only inheritable, meaning it is hidden to the owning command. See the [Inheriting Parameters](inheriting-parameters.md) section for more information on this attribute.

### `help=None`

Help text for this parameter. For example:

```python
@app.main()
@clip.flag('--panic', help='Don\'t do this')
def f(panic):
	pass
```

Produces:

```
$ python f.py -h
f

Usage: f {{options}}

Options:
  -h, --help  Show this help message and exit
  --panic     Don't do this
```

## Arguments

A positional parameter. An argument's parameter declaration is a single string corresponding to the name you want to give it:

```python
@app.main()
@clip.arg('penguinz')
def f(penguinz):
	pass
```

## Options

An optional parameter. An option's parameter declaration consists of up to two strings in a special format:

- An option's *long form* is prefixed with a double dash and is dash-delimited, e.g. `--long-form`
- An option's *short form* is a single letter prefixed with a dash, e.g. `-s`

For example, the following are all valid:

```python
@app.main()
@clip.opt('-a')
@clip.opt('--banana')
@clip.opt('-c', '--cantaloupe')
@clip.opt('--date-plum', '-d')
def f(a, banana, cantaloupe, date_plum):
	pass
```

By convention, the short form should just be the first letter of the long form, but this is not a requirement.

## Flags

A special kind of option that's true if it appears and false otherwise. Its parameter declarations are defined the same way as an option's would be.

Internally, a flag is implemented as an option that:

- Has `nargs=0` (it consumes no tokens from user input)
- Has `default=False` (it's false if it doesn't appear)
