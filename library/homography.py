import cv2
import numpy as np


def convert_to_birds_eye(new_image_point, deps):
  field_in_image = deps["homography_points"]["calibration"]["video_known_points"]
  field_real_scale = deps["homography_points"]["calibration"]["field_known_points"]
  #field_real_scale = [(0,30), (78, 30), (52, 109), (30, 109)]
  # Coordinates in the image (pixel values)
  x_values = [x for x, y in field_in_image]
  y_values = [y for x, y in field_in_image]
  image_points = np.array([
      [x_values[0], y_values[0]],  # Point 1
      [x_values[1], y_values[1]],  # Point 2
      [x_values[2], y_values[2]],  # Point 3
      [x_values[3], y_values[3]]   # Point 4
  ], dtype="float32")

  # Corresponding coordinates on the field (real world units)
  x_values_real = [x for x, y in field_real_scale]
  y_values_real = [y for x, y in field_real_scale]
  field_points = np.array([
      [x_values_real[0], y_values_real[0]],  # Corresponding point 1
      [x_values_real[1], y_values_real[1]],  # Corresponding point 2
      [x_values_real[2], y_values_real[2]],  # Corresponding point 3
      [x_values_real[3], y_values_real[3]]   # Corresponding point 4
  ], dtype="float32")

  # Calculate the homography matrix
  homography_matrix, status = cv2.findHomography(image_points, field_points)

  # Now, to map a new point from image to field coordinates
  new_image_point = np.array([new_image_point])
  new_image_point = new_image_point.reshape(1, 1, 2).astype(np.float32)

  # Apply the homography matrix
  new_field_point = cv2.perspectiveTransform(new_image_point, homography_matrix)

  return new_field_point
