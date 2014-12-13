import clip

from tornado import ioloop, web
from sockjs.tornado import SockJSConnection, SockJSRouter


class Stream(object):
	def __init__(self, f):
		self._f = f

	def write(self, message):
		self._f(message)


class Todo(object):
	def __init__(self, item):
		self._item = item
		self._completed = False

	def complete(self):
		self._completed = True

	def get_str(self):
		return '<span class="completed">{}</span>'.format(self._item) if self._completed else self._item


class IndexHandler(web.RequestHandler):
	def get(self):
		self.render('index.html')


class TodoConnection(SockJSConnection):

	def on_open(self, info):
		self._todos = []
		self._app = clip.App(stdout=Stream(self.on_out), stderr=Stream(self.on_err))

		@self._app.main()
		def todo():
			pass

		@todo.subcommand()
		@clip.arg('desc', nargs=-1, required=True)
		def add(desc):
			desc = ' '.join(desc)
			self._todos.append(Todo(desc))
			clip.echo('Added "{}" to the list of todos'.format(desc))

		@todo.subcommand()
		@clip.arg('index', type=int, required=True)
		def remove(index):
			try:
				removed = self._todos.pop(index - 1)
				clip.echo('Removed todo "{}"'.format(removed._item))
			except IndexError:
				clip.exit('Invalid todo index given', True)

		@todo.subcommand()
		@clip.arg('index', type=int, required=True)
		def complete(index):
			try:
				completed = self._todos[index - 1]
				completed.complete()
				clip.echo('Marked todo "{}" as completed'.format(completed._item))
			except IndexError:
				clip.exit('Invalid todo index given', True)

		@todo.subcommand(name='list')
		@clip.flag('-a', '--active')
		def list_todos(active):
			l = [e for e in self._todos if not e._completed] if active else self._todos
			clip.echo('\n'.join(['{}. {}'.format(i + 1, e.get_str()) for i, e in enumerate(l)]))

	def on_message(self, message):
		try:
			self._app.run(message)
		except clip.ClipExit:
			pass

	def on_out(self, message):
		self.send(message)

	def on_err(self, message):
		self.send('<span class="error">{}</span>'.format(message))


if __name__ == '__main__':
	TodoRouter = SockJSRouter(TodoConnection, '/todo')
	web.Application(
		[(r'/', IndexHandler)] + TodoRouter.urls
	).listen(8080)
	ioloop.IOLoop.instance().start()
