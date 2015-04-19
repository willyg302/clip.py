import clip
import sys


class Stream(object):
	def __init__(self, f):
		self._f = f

	def write(self, message):
		self._f(message)


def stream_a(message):
	sys.stdout.write('From stream A: {}'.format(message))

def stream_b(message):
	sys.stdout.write('From stream B: {}'.format(message))


app1 = clip.App(stdout=Stream(stream_a), name='app1')
app2 = clip.App(stdout=Stream(stream_b), name='app2')

clip.echo('App 1 via name', app='app1')
clip.echo('App 2 via name', app='app2')

app1.echo('App 1 directly')
app2.echo('App 2 directly')

clip.echo('Broadcast!')
