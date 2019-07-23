from bridge import *
from bridge.async_server import serve

t = Text('foo')
def callback():
    t.text = t.text + '!'
b = Button(text='click', callback=callback)

def callback2(s):
    t2.text = s
t2 = Text('')
tf = TextField(callback=callback2)

serve(GUI(List([t, b, t2, tf])))
