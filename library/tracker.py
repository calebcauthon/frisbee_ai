def split_tracker_id(tracker_id, frame_number, tracker_names, frames):
    new_id = max([id for ids in tracker_names.values() for id in ids]) + 1
    for frame in frames:
        if frame["frame_number"] >= frame_number:
            for obj in frame["objects"]:
                if obj["tracker_id"] == tracker_id:
                    obj["tracker_id"] = new_id
    for name, ids in tracker_names.items():
        if tracker_id in ids:
            ids.append(new_id)

def remove_tracker_name(name, tracker_names, frames):
    ids = tracker_names.get(name, [])
    for frame in frames:
        for obj in frame["objects"]:
            if obj["tracker_id"] in ids:
                print(f"Tracker still used, not removing. Tracker ID {obj['tracker_id']} used in frame {frame['frame_number']} for tracker name {name}")
                return tracker_names

    if name in tracker_names:
        del tracker_names[name]
    return tracker_names

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
    print (f"move_tracking_id_to_another_name({tracking_id}, {new_name})")
    print(["tracker_map", tracker_map])
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

def test_remove_tracker_removes_name():
    tracker_map = {
        "Ava22": [],
        "Dizzle3": [57, 60]
    }
    result = remove_tracker_name("Ava22", tracker_map, [])
    assert result == {
        "Dizzle3": [57, 60]
    }

    print("\033[92mtest_remove_tracker_removes_name() passed\033[0m")

def test_dont_remove_if_tracker_still_used():
    tracker_map = {
        "Ava22": [6],
        "Dizzle3": [57, 60]
    }
    frames = [
        {
            "frame_number": 1,
            "objects": [
                {
                    "tracker_id": 6
                }
            ]
        }
    ]
    result = remove_tracker_name("Ava22", tracker_map, frames)
    assert result == {
        "Ava22": [6],
        "Dizzle3": [57, 60]
    }

    print("\033[92mtest_dont_remove_if_tracker_still_used() passed\033[0m")

def test_split_tracker_id():
    frames = [
        {
            "frame_number": 1,
            "objects": [
                {
                    "tracker_id": 1
                }
            ]
        },
        {
            "frame_number": 2,
            "objects": [
                {
                    "tracker_id": 1
                }
            ]
        },
        {
            "frame_number": 3,
            "objects": [
                {
                    "tracker_id": 1
                }
            ]
        }
    ]
    tracker_names = {"Tracker1": [1]}
    split_tracker_id(1, 2, tracker_names, frames)
    assert frames[0]["objects"][0]["tracker_id"] == 1
    new_id = frames[1]["objects"][0]["tracker_id"]
    assert new_id != 1
    assert frames[2]["objects"][0]["tracker_id"] == new_id
    assert 1 in tracker_names["Tracker1"]

    print("\033[92mtest_split_tracker_id() passed\033[0m")



if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_move_tracking_id_to_another_name()
        test_move_tracking_id_to_new_name()
        test_change_tracking_id_on_all_frames()
        test_change_name()
        test_remove_tracker_removes_name()
        test_dont_remove_if_tracker_still_used()
        test_split_tracker_id()
