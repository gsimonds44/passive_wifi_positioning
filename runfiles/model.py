import os
import numpy as np
import csv
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsRegressor

"""
This script pulls all labeled training data from the "recorded_data" folder, and randomly samples 85% of the data to train a k-NN regression model. 
The remaining 15% of the data is used to test the accuracy of the model. 
Circular error probable (the radius of a circle containing 50% of the guesses) and the mean error for the test data are printed.
A plot is generated showing the magnitude and direction of the model errors within the test space.
"""


folder_path = "recorded_data"
test_split_size = 0.15

# room bounds (cm) 
X_MIN, X_MAX = 0.0, 348.0
Y_MIN, Y_MAX = 0.0, 1046.0

# image overlay config
IMG_PATH = "space_image_targets.png"
CM_PER_PX = 1.5              # 1.5 cm per pixel
PX_PER_CM = 1.0 / CM_PER_PX  # pixels per cm

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

# train/test split
X_train, X_test, y_train, y_test = train_test_split(
    inputs, outputs_xy, test_size=test_split_size, random_state=46, shuffle=True # 46 is awesome
)

# kNN 
knn = KNeighborsRegressor(n_neighbors=5, weights='distance', metric='manhattan')
knn_pipe = make_pipeline(StandardScaler(), knn)
knn_pipe.fit(X_train, y_train)
pred_knn = knn_pipe.predict(X_test)

# clamp predictions directly
pred_knn[:, 0] = np.clip(pred_knn[:, 0], X_MIN, X_MAX)
pred_knn[:, 1] = np.clip(pred_knn[:, 1], Y_MIN, Y_MAX)

# distance error in cm
err_knn = np.sqrt(((pred_knn - y_test) ** 2).sum(axis=1))

print(f"circular error probable: {np.median(err_knn):.2f} cm, mean: {np.mean(err_knn):.2f} cm")

# prepare data for overlay
actual_xs_cm = y_test[:, 0].astype(float)
actual_ys_cm = y_test[:, 1].astype(float)
predicted_xs_cm = pred_knn[:, 0].astype(float)
predicted_ys_cm = pred_knn[:, 1].astype(float)

# convert cm to pixels
actual_xs_px = actual_xs_cm * PX_PER_CM
actual_ys_px = actual_ys_cm * PX_PER_CM
predicted_xs_px = predicted_xs_cm * PX_PER_CM
predicted_ys_px = predicted_ys_cm * PX_PER_CM

errors = err_knn.reshape(-1, 1)
error_norm = (errors - errors.min()) / (errors.max() - errors.min() + 1e-12)  # [0,1]


# plot arrows on the image
img = plt.imread(IMG_PATH)
img_h, img_w = img.shape[0], img.shape[1]

fig, ax = plt.subplots(figsize=(5, 10), dpi=96)

# show image
ax.imshow(img, origin='upper')
ax.set_xlim(0, img_w)
ax.set_ylim(img_h, 0)  # y increases downward

# draw arrows in pixel coordinates
for i in range(len(actual_xs_px)):
    dx_px = predicted_xs_px[i] - actual_xs_px[i]
    dy_px = predicted_ys_px[i] - actual_ys_px[i]
    color = plt.cm.jet(error_norm[i][0])

    ax.arrow(
        actual_xs_px[i], actual_ys_px[i], dx_px, dy_px,
        head_width=3, head_length=4, fc=color, ec=color,
        length_includes_head=True
    )

ax.set_title("Test Results")
# scale axis labels (px to cm)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda val, pos: f"{val * CM_PER_PX:.0f}"))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda val, pos: f"{val * CM_PER_PX:.0f}"))
ax.set_xlabel("cm (x)")
ax.set_ylabel("cm (y)")
ax.set_aspect('equal')


plt.tight_layout()
plt.show()
