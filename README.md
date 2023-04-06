# fyp
new.py is main file which contains database connection,
GUI file main.window.ui,
modules.finalocr.py is a optical character recognition module which is imported in new.py,
obj.name is a class name file which contains "license plate",
yolov4-obj.cfg model configuration file contains the parameters for training,
yolov4-obj_final.weights is training weights which is binary file,
these two files are used to detect license plate and after that OCR is applied to the detected plate to extract numbers.
face detection is not included, i will remove those commands,
This program will run and open the laptop camera and scan car image and extract information of license plate which shows in the GUI,
 and also it contains log file which is entry and exit of cars , these information will be stored in database,
