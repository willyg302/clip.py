## Echo

clip provides a `clip.echo()` function that prints to your app's out/err streams instead of the system standard out/err. It is recommended that you use this instead of the regular Python `print()` function whenever possible, especially if your app has custom streams.

### Parameters

- `message`: The message to echo.
- `err=False`: Whether this is an error message.

## Exit

`clip.exit()` raises a `ClipExit` exception, optionally printing a message beforehand. This is especially useful for short-circuiting the execution of your app, such as when displaying a version string:

```python
app = clip.App()

def print_version(value):
	clip.exit('Version 0.0.0')

@app.main()
@clip.flag('--version', callback=print_version, hidden=True)
def f():
	clip.echo('This should not be called')
```

### Parameters

- `message=None`: An optional message to print before exiting. Note that this message is also passed onward to the underlying `ClipExit`.
- `err=False`: Whether this exit is occuring because of an error.

## Confirmation Prompt

Use `clip.confirm()` to prompt the user for confirmation. It returns a boolean value indicating the user's response:

```python
if clip.confirm('Do you want to continue?'):
	clip.echo('Launching missiles...')
```

You can also abort immediately if the user enters a negative response (this will raise a `ClipExit` with an error status):

```python
clip.confirm('Do you want to continue?', abort=True)
```

When embedding an app, you can specify the function to use to prompt users for input. See the [Embedding](embedding.md) section for more details.

### Parameters

- `prompt`: A string representing the prompt to display to the user.
- `default=None`: A default value for the prompt if the user simply presses Enter. Must be one of `'yes'`, `'no'`, or `None`. If `None`, then input is required from the user.
- `show_default=True`: Whether to display the prompt defaults.
- `abort=False`: Whether to abort upon a negative response.
- `input_function=None`: The function to use to prompt users for input, defaults to Python's standard `input()` or `raw_input()`.
