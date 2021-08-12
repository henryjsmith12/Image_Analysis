# Image_Analysis

Copyright (c) UChicago Argonne, LLC. All rights reserved.

A lightweight option for viewing scan data. Image Analysis allows users to view raw .tiff image files or data converted to HKL by loading SPEC and XML configuration files. This project is built with a [`PyQt5`](https://github.com/baoboa/pyqt5) framework for the GUI and [`pyqtgraph`](https://github.com/pyqtgraph/pyqtgraph) for the plots. The data is converted with [`rsMap3D`](https://github.com/AdvancedPhotonSource/rsMap3D) and [`xrayutilities`](https://github.com/dkriegner/xrayutilities).

## Requirements

* Python 3.7+
* PyQt5 5.10+
* pyqtgraph 

A full list of requirements can be found in [`requirements.txt`](https://github.com/henryjsmith12/Image_Analysis/blob/master/requirements.txt).


## Installation

To install and prepare the program, open Command Prompt/Terminal to enter the following commands. Currently, the only way to access the Image_Analysis repository is with the `git clone` command.  Clone the repository with the command below:

```
git clone https://github.com/henryjsmith12/Image_Analysis
```

The next task is to install the Python libraries that Image_Analysis uses. Change directories into the project directory.

```
cd Image_Analysis
```

Activate the virtual environment. 

```
source venv/bin/activate
```

Install the proper Python libraries. A full list of the project's dependencies can be found in [`requirements.txt`](https://github.com/henryjsmith12/Image_Analysis/blob/master/requirements.txt).

```
pip install -r requirements.txt
```

The program is now ready to use.

## Getting Started

Run the program by using the command below:

```
python image_analysis.py
```

The program's user interface should look like this on startup:

![Image Analysis GUI on Startup](https://github.com/henryjsmith12/Image_Analysis/blob/master/Screenshots/startup_gui.jpg)

## Author

Henry Smith - Co-op Student Technical at Argonne National Laboratory

## Support

* Report issues on the [Github issue tracker](https://github.com/henryjsmith12/Image_Analysis/issues).
* Email the author at smithh@anl.gov

