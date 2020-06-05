A browser-GUI library, optimized for making simple GUIs simple to write.

```
pip install -e python/

python -c 'from braggle import *; serve(GUI(Text("Hello world!")))'

python -m braggle.examples.counter
python -m braggle.examples.tour
```

# TODO
- add `/static/...` paths to the server so it can serve up supplementary assets like images
- ^ that should unlock something schnazzy like a Matplotlib image-manipulator
