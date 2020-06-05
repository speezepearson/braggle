from braggle import *

if __name__ == '__main__':
    print(open(__file__).read())
    serve(GUI(Text("Hello world!")))
