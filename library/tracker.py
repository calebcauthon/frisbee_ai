def add_tracker_name(new_name, tracker_names):
    if new_name not in tracker_names:
        tracker_names[new_name] = []
    return tracker_names

def change_name(old_name, new_name, tracker_map):
    for key, value in list(tracker_map.items()):
        if key == old_name:
            tracker_map[new_name] = tracker_map.pop(old_name)
    return tracker_map

def change_tracking_id_on_all_frames(frames, old_tracking_id, new_tracking_id):
    for frame in frames:
        for obj in frame["objects"]:
            if obj["tracker_id"] == old_tracking_id:
                obj["tracker_id"] = new_tracking_id



    print("\033[92mtest_change_tracking_id_on_all_frames() passed\033[0m")

def move_tracking_id_to_another_name(tracking_id, new_name, tracker_map):
# tracker map example:
#  map = "tracker_names": {
#    "Ava22": [
#      6
#    ],
#    "Dizzle3": [
#      57,
#      60
#    ]
#  }
# move_tracking_id_to_another_name(57, "Ava22", map)
# RESULT
#  map = "tracker_names": {
#    "Ava22": [
#      6,
#      57,
#    ],
#    "Dizzle3": [
#      60
#    ]
#  }
    for key, value in list(tracker_map.items()):
        if tracking_id in value:
            value.remove(tracking_id)
            if new_name in tracker_map:
                tracker_map[new_name].append(tracking_id)
            else:
                tracker_map[new_name] = [tracking_id]
    return tracker_map

def test_add_tracker_name():
    tracker_map = {
        "Ava22": [6],
        "Dizzle3": [57, 60]
    }
    result = add_tracker_name("NewName", tracker_map)
    assert result == {
        "Ava22": [6],
        "Dizzle3": [57, 60],
        "NewName": []
    }

    print("\033[92mtest_add_tracker_name() passed\033[0m")

def test_change_name():
    tracker_map = {
        "Ava22": [6],
        "Dizzle3": [57, 60]
    }
    result = change_name("Ava22", "NewName", tracker_map)
    assert result == {
        "NewName": [6],
        "Dizzle3": [57, 60]
    }

    print("\033[92mtest_change_name() passed\033[0m")

def test_move_tracking_id_to_new_name():
    tracker_map = {
        "Ava22": [6],
        "Dizzle3": [57, 60]
    }
    result = move_tracking_id_to_another_name(57, "NewName", tracker_map)
    assert result == {
        "Ava22": [6],
        "Dizzle3": [60],
        "NewName": [57]
    }

    print("\033[92mtest_move_tracking_id_to_new_name() passed\033[0m")

def test_move_tracking_id_to_another_name():
    tracker_map = {
        "Ava22": [6],
        "Dizzle3": [57, 60]
    }
    result = move_tracking_id_to_another_name(57, "Ava22", tracker_map)
    assert result == {
        "Ava22": [6, 57],
        "Dizzle3": [60]
    }

    print("\033[92mtest_move_tracking_id_to_another_name() passed\033[0m")

def test_change_tracking_id_on_all_frames():
    frames = [
        {
            "objects": [
                {
                    "tracker_id": 1
                },
                {
                    "tracker_id": 2
                }
            ]
        },
        {
            "objects": [
                {
                    "tracker_id": 1
                },
                {
                    "tracker_id": 2
                }
            ]
        }
    ]
    change_tracking_id_on_all_frames(frames, 1, 3)
    assert frames == [
        {
            "objects": [
                {
                    "tracker_id": 3
                },
                {
                    "tracker_id": 2
                }
            ]
        },
        {
            "objects": [
                {
                    "tracker_id": 3
                },
                {
                    "tracker_id": 2
                }
            ]
        }
    ]

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_move_tracking_id_to_another_name()
        test_move_tracking_id_to_new_name()
        test_change_tracking_id_on_all_frames()
        test_change_name()
