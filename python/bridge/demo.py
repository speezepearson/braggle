import asyncio
from pathlib import Path
from bridge import List, Text, Button, TextField, GUI

client_html = Path(__file__).absolute().parent.parent.parent / 'elm-client' / 'index.html'

t = Text('foo')
def callback():
    t.text = t.text + '!'
b = Button(text='click', callback=callback)

def callback2(s):
    t2.text = s
t2 = Text('')
tf = TextField(callback=callback2)
GUI(
    loop=asyncio.get_event_loop(),
    root=List([t, b, t2, tf]),
).run(client_html=client_html)
