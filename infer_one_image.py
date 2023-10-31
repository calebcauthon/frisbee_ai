from PIL import Image, ImageDraw
from roboflow import Roboflow

VERSION = 1
rf = Roboflow(api_key="pH2eX46dBGLw2Gh1ofek")
project = rf.workspace().project("frisbee-5d4co")
model = project.version(VERSION).model

# infer on a local image
results = model.predict("/mnt/c/Users/caleb/Downloads/frames/frame507.jpg", confidence=40, overlap=30).json()
predictions = results["predictions"]

image_path = "/mnt/c/Users/caleb/Downloads/frames/frame507.jpg"
image = Image.open(image_path)
draw = ImageDraw.Draw(image)

for bounding_box in predictions:
    x1 = bounding_box['x'] - bounding_box['width'] / 2
    x2 = bounding_box['x'] + bounding_box['width'] / 2
    y1 = bounding_box['y'] - bounding_box['height'] / 2
    y2 = bounding_box['y'] + bounding_box['height'] / 2
    box = (x1, x2, y1, y2)
    
    draw.rectangle([(x1, y1), (x2, y2)], outline="red")

image.save("prediction.jpg")


# visualize your prediction
# model.predict("your_image.jpg", confidence=40, overlap=30).save("prediction.jpg")

# infer on an image hosted elsewhere
# print(model.predict("URL_OF_YOUR_IMAGE", hosted=True, confidence=40, overlap=30).json())