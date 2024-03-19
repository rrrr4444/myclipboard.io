import os
from PIL import Image


items = os.listdir()

if not "output" in items:
    os.mkdir("output")

imgs = [item for item in items if item.endswith(".png")]

def process(filename, size):
    # Get rid of alpha transparency
    img = Image.open(filename)
    img = img.convert("RGB")
    img = img.resize(size)
    img.save(os.path.join(("output"), filename))


for filename in imgs:
    size = None
    # Pre X iPhones
    if filename.startswith("5"):
        process(filename, (1242, 2208))
    # Post X iPhones
    elif filename.startswith("6"):
        process(filename, (1242, 2688))
    # iPads
    elif filename.startswith("12"):
        process(filename, (2048, 2732))
