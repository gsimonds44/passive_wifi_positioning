import os
import numpy as np
import csv
import matplotlib.pyplot as plt

"""
This script generates a 2D plot of the signal strength for specific networks within the test space to visualize propagation patterns that the model learns. 
Arrow keys are used to switch between heatmap visuals for each of the networks. Dark purple dots indicate a network could not be detected in a specific location.
"""


folder_path = "recorded_data"

# image and scale
IMG_PATH = "space_image_targets.png"
CM_PER_PX = 1.5   # image is 1.5 cm per pixel
CELL_CM = 10.0       # data grid spacing


# data loading
inputs, outputs_xy = [], []

for filename in os.listdir(folder_path):
    parts = filename.split("_")
    x_value = float(parts[1])
    y_value = float(parts[2].split(".")[0])

    file_path = os.path.join(folder_path, filename)

    col = []
    with open(file_path, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            try:
                val = float(row[1]) # second column
            except:
                val = 0.0 # 'unavailable' gets 0
            col.append(val)

    col = np.array(col, dtype=np.float32)

    inputs.append(col)
    outputs_xy.append([x_value, y_value])

# convert lists to arrays
inputs = np.array(inputs, dtype=np.float32)              # (n_samples, n_features)
outputs_xy = np.array(outputs_xy, dtype=np.float32)      # (n_samples, 2)

xs = outputs_xy[:, 0]
ys = outputs_xy[:, 1]

n_samples, n_networks = inputs.shape
current_net = 0

# figure and axes with correctly scaled image
img = plt.imread(IMG_PATH)
img_h_px, img_w_px = img.shape[0], img.shape[1]
width_cm  = img_w_px * CM_PER_PX
height_cm = img_h_px * CM_PER_PX

fig, ax = plt.subplots(figsize=(5, 10), dpi=96)

# show image
ax.imshow(img,origin="upper",extent=[0, width_cm, height_cm, 0])  # [xmin, xmax, ymax, ymin]
ax.set_xlim(0, width_cm)
ax.set_ylim(height_cm, 0)  # y downward 

# scatter overlay in cm 
sc = ax.scatter(xs, ys, c=inputs[:, current_net], cmap="viridis", s=50)
cb = plt.colorbar(sc, ax=ax)
cb.set_label("Signal strength (0-100)")

ax.set_title(f"Network {current_net}")
ax.set_xlabel("cm (x)")
ax.set_ylabel("cm (y)")
ax.set_aspect("equal")

# scroll through networks with left and right arrow keys
def update_heatmap():
    sc.set_array(inputs[:, current_net])
    ax.set_title(f"Network {current_net}")
    fig.canvas.draw_idle()

def on_key(event):
    global current_net
    if event.key == "right":
        current_net = (current_net + 1) % n_networks
        update_heatmap()
    elif event.key == "left":
        current_net = (current_net - 1) % n_networks
        update_heatmap()

fig.canvas.mpl_connect("key_press_event", on_key)

plt.tight_layout()
plt.show()
