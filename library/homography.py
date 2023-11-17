import cv2
import numpy as np

def get_yardage_points():
    return {
        "top_left": (0, 30),
        "top_right": (78, 30),
        "bottom_left": (30, 109),
        "bottom_right": (52, 109)
    }

def get_calibration_points(deps):
    points = get_homography_points()
    return {
        "video_known_points": [
          points["left_clear_cone"]["position_within_image"],
          points["right_clear_cone"]["position_within_image"],
          points["left_bucket"]["position_within_image"],
          points["right_bucket"]["position_within_image"]
       ],
       "field_known_points": [
          points["left_clear_cone"]["position_on_field"],
          points["right_clear_cone"]["position_on_field"],
          points["left_bucket"]["position_on_field"],
          points["right_bucket"]["position_on_field"]
       ]
    }

def get_homography_points():
    yardage_points = get_yardage_points()
    return {
        "left_clear_cone": {
            "position_within_image": (422, 153),
            "position_on_field": yardage_points["top_left"]
        },
        "right_clear_cone": {
            "position_within_image": (1176, 123),
            "position_on_field": yardage_points["top_right"]
        },
        "left_bucket": {
            "position_within_image": (693, 581),
            "position_on_field": yardage_points["bottom_left"]
        },
        "right_bucket": {
            "position_within_image": (1181, 567),
            "position_on_field": yardage_points["bottom_right"]
        },
    }

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
