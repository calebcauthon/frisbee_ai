from types import SimpleNamespace

def annotations_route(dependencies, filename):
    logging = dependencies.logging
    flask = dependencies.flask
    stats = dependencies.stats

    annotation_filename = f'{filename}_annotation_data.json'
    annotation_data = logging.get_annotation_data(annotation_filename)
    if (annotation_data == {}):
        return annotation_data

    skip = flask.request.args.get('skip', default=100, type=int)
    start = flask.request.args.get('start', default=1, type=int)
    total_objects = flask.request.args.get('total_objects', default=100, type=int)
    name_filter = flask.request.args.get('name_filter', default=None, type=str)
    double_only = flask.request.args.get('double_only', default=False, type=str) == 'true'
    tracker_id_filter = flask.request.args.get('tracker_id_filter', default=None, type=str)
    distance_anomoly_threshold = flask.request.args.get('distance_anomoly_threshold', default=0, type=int)

    print(["flask args", {
        "skip": skip,
        "start": start,
        "total_objects": total_objects,
        "name_filter": name_filter,
        "double_only": double_only,
        "tracker_id_filter": tracker_id_filter,
        "distance_anomoly_threshold": distance_anomoly_threshold
    }])

    if (name_filter == 'all' or name_filter == 'null'):
        name_filter = None

    if (tracker_id_filter == 'all' or tracker_id_filter == 'null'):
        tracker_id_filter = None
    else:
        tracker_id_filter = int(tracker_id_filter)

    if (distance_anomoly_threshold is not None):
        distance_anomoly_threshold = int(distance_anomoly_threshold)
        tracker_names = set(obj['tracker_name'] for frame in annotation_data['frames'] for obj in frame['objects'])
        for name in tracker_names:
            stats.get_distance_travelled(name, annotation_data['frames'])

    filtered_frames = []
    object_count = 0
    indexes = range(start, len(annotation_data['frames']), skip)
    for i in indexes:
        frame = annotation_data['frames'][i]
        copy = frame.copy()
        frame = copy
        if name_filter:
            frame['objects'] = [obj for obj in frame['objects'] if obj['tracker_name'] == name_filter]
        if tracker_id_filter:
            frame['objects'] = [obj for obj in frame['objects'] if obj['tracker_id'] == tracker_id_filter]
        if distance_anomoly_threshold:
            frame['objects'] = [obj for obj in frame['objects'] if obj.get('distance_travelled', 0) > distance_anomoly_threshold] 

            

        include_frame = True
        if len(frame['objects']) > 0:
            if double_only:
                if len(frame['objects']) > 1:
                    include_frame = True
            else:
              include_frame
        else:
            include_frame = False

        if include_frame: 
            object_count += len(frame['objects'])
            if distance_anomoly_threshold:
                tracker_names = [obj['tracker_name'] for obj in frame['objects']]
                print(f"looking backwards for any {tracker_names}")
                for j in range(i - 1, -1, -1):
                    last_frame = annotation_data['frames'][j]
                    last_frame_objects = [obj for obj in last_frame['objects'] if obj['tracker_name'] in tracker_names]
                    if last_frame_objects:
                        print(f"FOund tracker names {tracker_names} in last frame #{last_frame['frame_number']}")
                        last_frame['objects'] = last_frame_objects
                        filtered_frames.append(last_frame)
                        break
                    else:
                        tracker_names_in_last_frame = [obj['tracker_name'] for obj in last_frame['objects']]
                        print(f"Did not find tracker names {tracker_names} in last frame #{last_frame['frame_number']} which had tracker names {tracker_names_in_last_frame}")

            filtered_frames.append(frame)

        if object_count > total_objects:
            print(f"break because object_count: {object_count} > total_objects: {total_objects}")
            break

    annotation_data['frames'] = filtered_frames
    return flask.render_template('annotation_data.html', data=annotation_data, query_params=flask.request.args)
    