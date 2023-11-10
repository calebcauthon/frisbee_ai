import json
import os
from PIL import Image

def predict(path, deps):
  command = f"inference infer {path} --api-key pH2eX46dBGLw2Gh1ofek --project-id frisbee-5d4co --model-version 4"
  result = os.popen(command).read().split('\n')
  for line in result:
    if line and not line.startswith("Running"):
      return json.loads(line.replace("'", '"'))

def predict_frame(frame, deps):
  im = Image.fromarray(frame)
  im.save("tmp.jpeg")
  results = predict("tmp.jpeg", deps)
  return results
