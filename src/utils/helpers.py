def get_available_coordinates(window) -> tuple[int, int]:
    geo = window.geometry()
    windowsize = {
        "x": geo.x(),
        "y": geo.y(),
        "width": geo.width(),
        "height": geo.height()
    } 

    screensize = {
        "width": window.screen().size().toTuple()[0],
        "hieght": window.screen().size().toTuple()[1]
    }

    dialog_width = 400
    dialog_x = None
    dialog_y = windowsize["y"] + 0

    distance_between_windows = - 200

    if (screensize["width"] - (windowsize["x"] + windowsize["width"]) < (dialog_width + distance_between_windows)):
        dialog_x = windowsize["x"] - (dialog_width + distance_between_windows)
    else:
        dialog_x = windowsize["x"] + windowsize["width"] + distance_between_windows

    return (dialog_x, dialog_y)
