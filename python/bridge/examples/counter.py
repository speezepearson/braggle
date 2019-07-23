from bridge import *

text = Text('0')
def increment(n):
    text.text = str(int(text.text) + n)

serve(GUI(Container([
    Button('-', callback=(lambda: increment(-1))),
    Text(' '), text, Text(' '),
    Button('+', callback=(lambda: increment(1))),
])))
