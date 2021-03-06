# Air drums


## Goal

The goal is to build air drums that are realistic as much as possible.

A usual 30 FPS web camera will be used for motion tracking.

The drums will be controlled by drum sticks with colored heads and colored spots on your feet.


## Playing
Python 3.6 or higher is required.
Play the air drums by running `play_drums.py`. To quit the application press `q`.


### Settings
Settings file can be passed as parameter `-s=relative_path_to_settings_file`.
If not specified, the default settings `settings/drum_set_basic.yaml` is used.

### Calibration
At first calibrate your drum sticks. Reset color by pressing `r`. Put the colored
head of your drum stick to the circle (make the circle larger or smaller by `l/s`)
and press `c`. Then press `n` to proceed to the next calibration point.
Go through all calibration points. Then calibrate the
second drum stick. The calibration can be quited by `q`.


## Plans for the next versions
- Add automatic tracker calibration.
- Improve tracker for fast movements.
- Calibrate the position of percussion by playing them virtually in the air.
- Play the sound when the drum stick changed the acceleration and is close to the percussion.
- Add better and more percussion sounds (as submodule).
- Add image with drum scene on the output instead of the video stream.
- Create GUI using Kivy.
