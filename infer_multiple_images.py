from PIL import Image, ImageDraw
from roboflow import Roboflow

VERSION = 1
rf = Roboflow(api_key="pH2eX46dBGLw2Gh1ofek")
project = rf.workspace().project("frisbee-5d4co")
model = project.version(VERSION).model

for i in range(2, 507):
    image_path = f"/mnt/c/Users/caleb/Downloads/frames/frame{i:03}.jpg"
    results = model.predict(image_path, confidence=40, overlap=30).json()
    predictions = results["predictions"]
    
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    for bounding_box in predictions:
        x1 = bounding_box['x'] - bounding_box['width'] / 2
        x2 = bounding_box['x'] + bounding_box['width'] / 2
        y1 = bounding_box['y'] - bounding_box['height'] / 2
        y2 = bounding_box['y'] + bounding_box['height'] / 2
        box = (x1, x2, y1, y2)
        
        draw.rectangle([(x1, y1), (x2, y2)], outline="red")

    image.save(f"sequence/prediction{i:03}.jpg")
