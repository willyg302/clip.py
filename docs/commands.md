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

```
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

```
$ python f.py -h
f

Usage: f {{options}}

Options:
  -h, --help  Show this help message and exit

So long and thanks for all the fish!
```

### `inherits=None`

In clip commands can be nested indefinitely, so it only makes sense that commands can also inherit parameters from their *parents*. This concept is covered in the [Inheriting Parameters](inheriting-parameters.md) section.
