from braggle import *

def main() -> None:
    text = Text('0')
    def increment(n):
        text.text = str(int(text.text) + n)

    serve(GUI(
        Button('-', callback=(lambda: increment(-1))),
        Text(' '), text, Text(' '),
        Button('+', callback=(lambda: increment(1))),
    ))

if __name__ == '__main__':
    print(open(__file__).read())
    main()
