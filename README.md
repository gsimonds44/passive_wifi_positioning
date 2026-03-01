# passive_wifi_positioning

## Purpose:

This system develops a model for predicting the location of a human occupant within an indoor environment using only the measured signal strength of nearby wifi networks. The core assumption is that in dense network environments (such as large residential buildings), human movement alters the propagation patterns of microwave-frequency signals emitted by distributed access points. Consequently, a single stationary receiver can passively infer meaningful information about such movements by analyzing changes in the relative signal strengths of the surrounding networks.<br><br>



## Prerequisites:

**Location** - This test was conducted in a dense environment of wifi networks, in a residential block of Lower Manhattan. Nearly 100 independent networks could be detected and measured.

**Hardware** - A single laptop serves as the signal strength measuring device using its built-in wireless network adapter. It is located centrally within the test space to ensure balanced radio-frequency influence from all areas. An iPhone is carried by the test subject during data collection and is used to send live data to the laptop regarding the subject's location within the test space, which is used to label the sampled network data. 

**space_image.png (contained in iPhone application folder)** - Detailed measurements of the test space are collected and documented at scale in this image, which is used for data collection/labeling and visualizing results.

**target_list.csv (contained in iPhone application folder)** - Data collection points are defined in image coordinates (space_image.png) and are saved as a list in this file. Points are distributed in a square grid within the human-traversable areas of the test space. In this case, 750 points are defined. 


**NOTES:** 

-Core iPhone application files are included in this repository, but the full app project folder was omitted for simplicity. The application can easily be built in Xcode by importing the included files. Bluetooth permissions must be requested in the info.plist.<br><br>



## Data Collection:

1) With the laptop placed in a fixed location within the test space, "build_masterlist.py" is run to create a reference list of available wifi networks. For each network, the SSID and channel are appended to a single string, then hashed to produce a privacy-preserving fingerprint. A list of fingerprints is saved to "network_masterlist.csv".

2) The iPhone application "positionTracker", and the script "collect_data.py" are run simultaneously. The iPhone pairs with the laptop over bluetooth and is ready to begin sending position labels.

3) After the python terminal prints "ready", the subject stands in the position within the test space indicated by the large red dot on the "positionTracker" app, then the button "Capture Position" is tapped, triggering the following exchange:
    
    -The app sends the position coordinates to the laptop, and the "Capture Position" button will be temporarily deactivated.
   
    -Upon receiving the coordinates, the laptop will take a snapshot of the current network environment, and save a file with the RSSI signal strength for all relevant networks.
   
    -The network snapshot may take several seconds to complete in some cases. During this time, the subject does not move from the target position.
   
    -Once complete, the laptop will send an acknowledgment to the app, which will automatically advance the target position and reactivate the "Capture Position" button.

5) Step 3 is repeated for all target positions. In case of any issues, data points may be overwritten or skipped using the arrow buttons on the app.

   
<img width="236" height="511" alt="App Screenshot" src="https://github.com/user-attachments/assets/a01b05c6-c7fb-4970-96fb-c49febdf1c73" /><br>
*Figure 1 - PositionTracker App - Data Collection Process*

**NOTES:**

-Duplicate networks or other problematic networks were blacklisted from the data collection process within the source code of "build_masterlist.py".

-Any network not in "network_masterlist.csv" is ignored by the data collection process.

-Both the laptop and iPhone were disconnected from any wifi networks, and any mobile hotspots were switched off.

-Efforts were made to avoid any manipulation of objects (furniture/doors/windows) within the test space throughout the collection process to avoid introducing noise sources to the signal prorogation patterns.

-All collected data is stored in a subfolder "recorded_data" as a separate csv file for each recorded position. The naming format for the files is NN_XX_YY.csv, where NN is the sample number, and (XX,YY) are the target coordinates in cm as measured from the top left corner of the image/space. Each row in the csv file lists all of the network hashes from the master list, and the 2nd column contains the signal strength measured from 1-100, or "unavailable" if the network was not detected in the snapshot.<br><br>



## Evaluation:

1) The script "model.py" pulls all labeled training data from the "recorded_data" folder, and randomly samples 85% of the data to train a k-NN regression model. The remaining 15% of the data is used to test the accuracy of the model. Running the script prints the mean and median prediction error for the test data and a plot is generated showing the magnitude and direction of the model errors within the test space.

2) The script "network_vis.py" generates a 2D plot of the signal strength for specific networks within the test space to visualize propagation patterns that the model learns. Arrow keys are used to switch between networks.<br><br>



## Results:

When trained on 85% of the data (approximately 637 points), and with a variety of random seeds for the test/train split, the median error is found to be in the range of 16-17 centimeters, with a mean in the range of 20-35 centimeters. Errors of such small magnitude are particularly impressive because it is nearly indistinguishable from the irreducible error of the labeling process, which requires the test subject to position themselves in a target location indicated on an image of the floor-plan.

**NOTES:**

-A variety of machine learning architectures were tested, including a neural network, SVM, random forest, kNN and ensemble methods. kNN was found to perform best, likely due to the highly localized structure of the signal strength topology. As a result, the training data must be fully distributed across the test space. Areas which lack training data cannot produce meaningful predictions, due to a lack of global structure.



<img width="320" height="640" alt="Figure_1" src="https://github.com/user-attachments/assets/9794a8ec-4ea9-47d5-b647-d0908ef59bce" /><br>
*Figure 2 - Test Accuracy - circular error probable: 16.29 cm, mean: 20.09 cm*




<img width="160" height="320" alt="Figure_2" src="https://github.com/user-attachments/assets/167daf5c-d942-4660-a301-81ddea6ae8a6" />
<img width="160" height="320" alt="Figure_3" src="https://github.com/user-attachments/assets/e3510f93-717e-4913-bc64-f14a21d6b517" />
<img width="160" height="320" alt="Figure_4" src="https://github.com/user-attachments/assets/8827cf62-4420-4ccc-a29d-9b446ecc3912" />
<img width="160" height="320" alt="Figure_5" src="https://github.com/user-attachments/assets/1d418727-72b9-4bcd-8fb1-1fe637362018" /><br>
*Figure 3 - Signal Strength Mapping of Networks*<br>
