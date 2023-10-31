import json
import cv2
import os

# Loop through each image
directory = '/mnt/c/Users/caleb/DEV/frisbee_ai/videos/womens_goalty/outputs/tracker_ids/'
for filename in os.listdir(directory):
    if filename.endswith(".jpg"):
        img_path = os.path.join(directory, filename)
        tracker_id = int(filename.split('_')[-1].split('.')[0])
    img = cv2.imread(img_path)
    cv2.imshow('Image', img)
    cv2.waitKey(2000)
    cv2.destroyAllWindows()

    # Ask the user for the name
    name = input("Enter the name: ")

    # Read in the json object
    with open('videos/womens_goalty/ids.json', 'r+') as file:
        data = json.load(file)
        # If the key already exists in the data, just add the tracker id to the array
        if name in data:
            data[name].append(tracker_id)
        else:
            data[name] = [tracker_id]
        # Write the updated data back to the file
        with open('videos/womens_goalty/ids.json', 'w') as file:
            json.dump(data, file)

    # Delete the file
    os.remove(img_path)

