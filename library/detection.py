import json
import os
from PIL import Image
import requests
from inference.models.utils import get_roboflow_model
import cv2

def predict(path, deps):
  version_5 = "frisbee-5d4co/5"
  version_13 = "frisbee-5d4co/13"
  detector_version_4 = "frisbee-detector-rkuwm/4"
  detector_version_5 = "frisbee-detector-rkuwm/5"
  detector_version_6 = "frisbee-detector-rkuwm/6"
  model = get_roboflow_model(
      model_id=version_5,
      api_key="pH2eX46dBGLw2Gh1ofek",
  )
  run = deps["run"]
  
  frame_number = deps["status"]["frame_data"]["index"]
  # you can also infer on local images by passing a file path,
  # a PIL image, or a numpy array
  results = model.infer(
    image=path,
    confidence=0.10,
    iou_threshold=0.1
  )

  run["detection_count"].add(f"{len(results[0])}")

  
  predictions = []
  for raw_prediction in results[0]:
    prediction = {
      "xyxy": raw_prediction[:4],
      "confidence": raw_prediction[4],
      "confidence2": raw_prediction[5],
      "class": "n/a",
      "class_id": raw_prediction[6],
      "x": (raw_prediction[0] + raw_prediction[2]) / 2,
      "y": (raw_prediction[1] + raw_prediction[3]) / 2,
      "width": raw_prediction[2] - raw_prediction[0],
      "height": raw_prediction[3] - raw_prediction[1],
    }
    predictions.append(prediction)

  return {
    "predictions": predictions
  }

def predict_http_to_docker(jpeg, deps):
  image_url = "http://localhost:5000/static/tmp/" + jpeg
  project_id = "frisbee-5d4co"
  model_version = "10"
  confidence = 0.2
  api_key = "pH2eX46dBGLw2Gh1ofek"
  task = "object_detection"
  iou_thresh = 0.5

  infer_payload = {
      "model_id": f"{project_id}/{model_version}",
      "image": {
          "type": "url",
          "value": image_url,
      },
      "confidence": confidence,
      "iou_threshold": iou_thresh,
      "api_key": api_key,
  }
  print(f"payload: {infer_payload}")
  res = requests.post(
      f"http://localhost:9001/infer/{task}",
      json=infer_payload,
  )
  print(res)

  predictions = res.json()
  print(predictions)

def predict_CLI(path, deps):
  command = f"inference infer {path} --api-key pH2eX46dBGLw2Gh1ofek --project-id frisbee-5d4co --model-version 5"
  process = os.popen(command)
  output = process.read()
  print(f"output: {output}")
  result = output.split('\n')
  count = 0
  for line in result:
    if line and not line.startswith("Running"):
      count += 1
      if count > 10:
        raise Exception("Error: More than 10 iterations in the loop.")
      return json.loads(line.replace("'", '"'))

def predict_frame(frame, deps):
  frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
  im = Image.fromarray(frame)
  path = "tmp.jpeg"
  im.save(path)

  frame_number = deps["status"]["current_frame"]["index"]

  results = predict("tmp.jpeg", deps)
  os.remove(path)

  results["image"] = {
      "width": frame.shape[1],
      "height": frame.shape[0]
  }
  return results
