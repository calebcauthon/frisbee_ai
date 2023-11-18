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
    tracker_name = flask.request.args.get('tracker_name', default=None, type=str)

    if (tracker_name == 'all' or tracker_name == 'null'):
        tracker_name = None

    filtered_frames = []
    object_count = 0
    indexes = range(start, len(annotation_data['frames']), skip)
    for i in indexes:
        frame = annotation_data['frames'][i]
        if tracker_name:
            frame['objects'] = [obj for obj in frame['objects'] if obj['tracker_name'] == tracker_name]
        object_count += len(frame['objects'])
        if object_count > total_objects:
            print(f"break because object_count: {object_count} > total_objects: {total_objects}")
            break
        
        if len(frame['objects']) > 0:
            filtered_frames.append(frame)
    annotation_data['frames'] = filtered_frames
    return flask.render_template('annotation_data.html', data=annotation_data, query_params=flask.request.args)
    