A command is the basic building block of a clip application. You can create a command out of a regular function in one of two ways:

1. By specifying it as the main function of an app

        @app.main()
        def f():
            pass

2. By specifying it as a subcommand of another command

        @some_command.subcommand()
        def f():
            pass

This section will look at the ways that you can customize your commands via decorator keyword arguments.

## Keyword Arguments

### `default=None`

A string specifying the default input to use when no input is given by the user. For example:

```python
@app.main(default='x --num 19')
def f():
	pass

@f.subcommand(default='-h')
@clip.opt('--num', type=int, required=True)
def x(num):
	clip.echo('I was invoked with the number {}!'.format(num))
```

Produces:

```diff
$ python f.py x --num 5
I was invoked with the number 5!
$ python f.py x
f x

Usage: x {{options}}

Options:
  -h, --help   Show this help message and exit
  --num [int]  
$ python f.py
I was invoked with the number 19!
```

As you can see, `default` is especially good for specifying default subcommands to run, or printing the help text when no input is entered.

### `description=None`

A command's description is printed out in help message screens. For example:

```python
@app.main(description='This thing does awesome stuff!')
def f():
	pass

@f.subcommand(description='This is a sweet subcommand!')
def sub():
	pass
```

Produces the following:

```diff
$ python f.py -h
f: This thing does awesome stuff!

Usage: f {{options}} {{subcommand}}

Options:
  -h, --help  Show this help message and exit

Subcommands:
  sub  This is a sweet subcommand!
$ python f.py sub -h
f sub: This is a sweet subcommand!

Usage: sub {{options}}

Options:
  -h, --help  Show this help message and exit
```

### `epilogue=None`

Text printed at the very end of the command's help screen. For example:

```python
@app.main(epilogue='So long and thanks for all the fish!')
def f():
	pass
```

Produces:

```diff
$ python f.py -h
f

Usage: f {{options}}

Options:
  -h, --help  Show this help message and exit

So long and thanks for all the fish!
```

### `inherits=None`

In clip commands can be nested indefinitely, so it only makes sense that commands can also inherit parameters from their *parents*. This concept is covered in the [Inheriting Parameters](inheriting-parameters.md) section.

### `tree_view=None`

Pass the name of a Flag that, if called, will display a recursive tree view of the command and all its subcommands. For example:

```python
@app.main(tree_view='-t')
@clip.flag('-t', '--tree', hidden=True)
def w():
    pass

@w.subcommand()
def x():
    pass

@x.subcommand()
def y():
    pass

@y.subcommand()
def z():
    pass
```

Produces:

```diff
$ python f.py --tree
w
  x
    y
      z
```

This is particularly useful for a brief overview of a large program with many commands. Note that you should not use the given flag for anything except a placeholder to invoke the tree view, as many of its attributes will be overridden.
