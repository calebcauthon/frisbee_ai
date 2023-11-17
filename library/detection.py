import json
import os
from PIL import Image

def predict(path, deps):
  command = f"inference infer {path} --api-key pH2eX46dBGLw2Gh1ofek --project-id frisbee-5d4co --model-version 5"
  process = os.popen(command)
  output = process.read()
  result = output.split('\n')
  count = 0
  for line in result:
    if line and not line.startswith("Running"):
      count += 1
      if count > 10:
        raise Exception("Error: More than 10 iterations in the loop.")
      return json.loads(line.replace("'", '"'))

def predict_frame(frame, deps):
  im = Image.fromarray(frame)
  im.save("tmp.jpeg")
  results = predict("tmp.jpeg", deps)
  os.remove("tmp.jpeg")
  return results
