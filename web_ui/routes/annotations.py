from types import SimpleNamespace

def annotations_route(dependencies, filename):
    logging = dependencies.logging
    flask = dependencies.flask

    annotation_data = logging.get_annotation_data(filename)
    if (annotation_data == {}):
        return annotation_data

    skip = flask.request.args.get('skip', default=100, type=int)
    start = flask.request.args.get('start', default=1, type=int)
    total_objects = flask.request.args.get('total_objects', default=100, type=int)
    name_filter = flask.request.args.get('name_filter', default=None, type=str)
    double_only = flask.request.args.get('double_only', default=False, type=str) == 'true'
    tracker_id_filter = flask.request.args.get('tracker_id_filter', default=None, type=str)

    print(["flask args", {
        "skip": skip,
        "start": start,
        "total_objects": total_objects,
        "name_filter": name_filter,
        "double_only": double_only,
        "tracker_id_filter": tracker_id_filter
    }])

    if (name_filter == 'all' or name_filter == 'null'):
        name_filter = None

    if (tracker_id_filter == 'all' or tracker_id_filter == 'null'):
        tracker_id_filter = None
    else:
        tracker_id_filter = int(tracker_id_filter)

    filtered_frames = []
    object_count = 0
    indexes = range(start, len(annotation_data['frames']), skip)
    for i in indexes:
        frame = annotation_data['frames'][i]
        if name_filter:
            frame['objects'] = [obj for obj in frame['objects'] if obj['tracker_name'] == name_filter]
        if tracker_id_filter:
            frame['objects'] = [obj for obj in frame['objects'] if obj['tracker_id'] == tracker_id_filter]

        if len(frame['objects']) > 0:
            if double_only:
                if len(frame['objects']) > 1:
                    filtered_frames.append(frame)
                    object_count += len(frame['objects'])
            else:
              filtered_frames.append(frame)
              object_count += len(frame['objects'])

        if object_count > total_objects:
            print(f"break because object_count: {object_count} > total_objects: {total_objects}")
            break

    annotation_data['frames'] = filtered_frames
    return flask.render_template('annotation_data.html', data=annotation_data, query_params=flask.request.args)
    