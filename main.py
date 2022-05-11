from core.PyNect import PyNect

# Kinect for Windows v2 / Kinect for Xbox 360
# Depth range:     from 0.5m to 4.5m
# Color stream:    1920×1080
# Depth stream:    512×424
# Infrared stream: 512×424
# Field of view:   h=70°, v=60°
# Audio stream:    4-mic array
# USB:             3.0

if __name__ == "__main__":
    # create main application
    app = PyNect()
    # start the mainloop
    app.mainloop()
