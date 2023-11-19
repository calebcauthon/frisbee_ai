import cv2
def get_total_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    return total_frames

def get_stats(annotation_data):
    players = annotation_data["tracker_names"].keys()
    
    box_score = []
    for player in players:
        frames = get_player_frames(player, annotation_data)
        frame_count = len(frames)
        time_on_screen = frame_count / 25
        distance_travelled = round(get_distance_travelled(player, frames))
        box_score.append({
            "name": player,
            "team": "home",
            "frame_count": frame_count,
            "time_on_screen": f"{time_on_screen}s",
            "distance": f"{distance_travelled} ft",
            "points": 0,
            "assists": 0,
            "rebounds": 0,
            "steals": 0,
            "blocks": 0,
            "turnovers": 0,
            "fouls": 0
        })
    return {
      "players": players,
      "box_score": box_score
    }

def get_frames_with_distance_travelled(frames):
  last_frame = None
  frames_with_distance = []
  for frame in frames:
      if not frame["objects"]:
          continue
      
      for current_object in frame["objects"]:
          current_position = current_object["field_position"]
          if last_frame is not None:
              for prev_object in last_frame["objects"]:
                  if prev_object["tracker_name"] == current_object["tracker_name"]:
                      prev_position = prev_object["field_position"]
                      distance = ((current_position[0] - prev_position[0])**2 + (current_position[1] - prev_position[1])**2)**0.5
                      current_object["distance_travelled"] = distance
      frames_with_distance.append(frame)

      last_frame = frame

  return frames_with_distance

def get_distance_travelled(name, frames):
  frames = exclude_other_players(name, frames)
  frames = get_frames_with_distance_travelled(frames)
  total_distance = 0
  for frame in frames:
    for obj in frame["objects"]:
        if ("distance_travelled" in obj):
            total_distance += obj["distance_travelled"]

  return total_distance

def exclude_other_players(name, frames):
    filtered_frames = []
    for frame in frames:
        filtered_objects = [obj for obj in frame["objects"] if obj["tracker_name"] == name]
        frame_copy = frame.copy()
        frame_copy["objects"] = filtered_objects
        filtered_frames.append(frame_copy)
    return filtered_frames

def get_player_frames(name, annotation_data):
    player_frames = []
    for frame in annotation_data["frames"]:
        if any(obj["tracker_name"] == name for obj in frame["objects"]):
            player_frames.append(frame)

    return player_frames

def test_get_distance_travelled():
    test_cases = [
        {
            "field_positions": [(0, 0), (0, 1)],
            "expected": 1
        },
        {
            "field_positions": [(1, 0), (0, 1)],
            "expected": 1.4142135623730951
        },
    ]
    
    for index, test_case in enumerate(test_cases):
        frames = [{"frame_number": i, "objects": [{"field_position": pos, "tracker_name": "Isabella"}]} for i, pos in enumerate(test_case["field_positions"])]
        result = get_distance_travelled("Isabella", frames)
        expected = test_case["expected"]
        assert result == expected, f"Expected {expected}, but got {result}"
        print (f"\033[92mtest_get_distance_travelled() passed {index + 1} of {len(test_cases)} \033[0m")

def test_get_distance_travelled_with_missing_frame():
    frame1 = {"frame_number": 0, "objects": [{"field_position": (0, 0), "tracker_name": "Isabella"}]}
    frame2 = {"frame_number": 1, "objects": [{"field_position": (0, 1), "tracker_name": "OTHER"}]}
    frame3 = {"frame_number": 2, "objects": [{"field_position": (0, 2), "tracker_name": "Isabella"}]}
    
    frames = [frame1, frame2, frame3]

    result = get_distance_travelled("Isabella", frames)
    expected = 2
    assert result == expected, f"Expected {expected}, but got {result}"
    print (f"\033[92mtest_get_distance_travelled_with_missing_frame() passed\033[0m")

def test_get_distance_travelled_with_extra_frame():
    test_cases = [
        {
            "field_positions": [(0, 0), (0, 1)],
            "expected": 1
        },
        {
            "field_positions": [(1, 0), (0, 1)],
            "expected": 1.4142135623730951
        },
    ]
    
    for index, test_case in enumerate(test_cases):
        frames = [{"frame_number": i, "objects": [{"field_position": pos, "tracker_name": "Isabella"}]} for i, pos in enumerate(test_case["field_positions"])]

        extra_frame = {"frame_number": 1, "objects": [{"field_position": (0.5, 0.5), "tracker_name": "SOMEONE ELSE"}]}
        frames.insert(1, extra_frame)

        result = get_distance_travelled("Isabella", frames)
        expected = test_case["expected"]
        assert result == expected, f"Expected {expected}, but got {result}"
        print (f"\033[92mtest_get_distance_travelled_with_extra_frame() passed {index + 1} of {len(test_cases)} \033[0m")

def test_get_distance_multiple_players():
    test_cases = [
        {
            "field_positions": {
                "Isabella": [(0, 0), (0, 1)],
                "SOMEONE ELSE": [(0, 0), (1, 0)]
            },
            "expected": {
                "Isabella": 1,
                "SOMEONE ELSE": 1
            }
        },
        {
            "field_positions": {
                "Isabella": [(1, 0), (0, 1)],
                "SOMEONE ELSE": [(0, 0), (1, 1)]
            },
            "expected": {
                "Isabella": 1.4142135623730951,
                "SOMEONE ELSE": 1.4142135623730951
            }
        },
    ]
    
    for index, test_case in enumerate(test_cases):
        frames = []
        for player, positions in test_case["field_positions"].items():
            player_frames = [{"frame_number": i, "objects": [{"field_position": pos, "tracker_name": player}]} for i, pos in enumerate(positions)]
            frames.extend(player_frames)

        for player, expected in test_case["expected"].items():
            result = get_distance_travelled(player, frames)
            assert result == expected, f"Expected {expected}, but got {result} for player {player}"
        print (f"\033[92mtest_get_distance_multiple_players() passed {index + 1} of {len(test_cases)} \033[0m")

def test_get_player_frames():
    annotation_data = {
        "frames": [
            {
                "objects": [
                    {
                        "tracker_name": "Ava22",
                        "tracker_id": 6
                    },
                    {
                        "tracker_name": "Dizzle3",
                        "tracker_id": 57
                    },
                    {
                        "tracker_name": "Dizzle3",
                        "tracker_id": 60
                    }
                ]
            },
            {
                "objects": [
                    {
                        "tracker_name": "Ava22",
                        "tracker_id": 6
                    },
                    {
                        "tracker_name": "Dizzle3",
                        "tracker_id": 57
                    },
                    {
                        "tracker_name": "Dizzle3",
                        "tracker_id": 60
                    }
                ]
            }
        ],
        "tracker_names": {
            "Ava22": [6],
            "Dizzle3": [57, 60]
        }
    }
    result = get_player_frames("Dizzle3", annotation_data)
    expected = [
        {
            "objects": [
                {
                    "tracker_name": "Ava22",
                    "tracker_id": 6
                },
                {
                    "tracker_name": "Dizzle3",
                    "tracker_id": 57
                },
                {
                    "tracker_name": "Dizzle3",
                    "tracker_id": 60
                }
            ]
        },
        {
            "objects": [
                {
                    "tracker_name": "Ava22",
                    "tracker_id": 6
                },
                {
                    "tracker_name": "Dizzle3",
                    "tracker_id": 57
                },
                {
                    "tracker_name": "Dizzle3",
                    "tracker_id": 60
                }
            ]
        }
    ]

    assert len(result) == len(expected), f"The count of actual and expected does not match, actual: {len(result)}, expected: {len(expected)}"
    for i in range(len(result)):
        assert result[i] == expected[i], f"Item {i} in result and expected does not match, result: {result[i]}, expected: {expected[i]}"

    print("\033[92mtest_get_player_frames() passed\033[0m")

def test_get_frames_with_distance_travelled():
    frame1 = {"frame_number": 0, "objects": [
        {"field_position": (0, 0), "tracker_name": "Isabella"}
    ]}
    frame2 = {"frame_number": 0, "objects": [
        {"field_position": (5, 0), "tracker_name": "Isabella"},
        {"field_position": (0, 5), "tracker_name": "Todd"}
    ]}
    frame3 = {"frame_number": 0, "objects": [
        {"field_position": (0, 15), "tracker_name": "Todd"}
    ]}

    frames = [frame1, frame2, frame3]

    get_frames_with_distance_travelled(frames)

    frame2_isabella_distance = frame2["objects"][0]["distance_travelled"]
    assert frame2_isabella_distance == 5, f"Expected 5, but got {frame2_isabella_distance}"

    frame3_todd_distance = frame3["objects"][0]["distance_travelled"]
    assert frame3_todd_distance == 10, f"Expected 10, but got {frame3_todd_distance}"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_get_player_frames()
        test_get_distance_travelled()
        test_get_distance_travelled_with_extra_frame()
        test_get_distance_multiple_players()
        test_get_distance_travelled_with_missing_frame()
        test_get_frames_with_distance_travelled()
