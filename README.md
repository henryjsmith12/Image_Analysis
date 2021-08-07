# Image_Analysis

Copyright (c) UChicago Argonne, LLC. All rights reserved.

A lightweight option for viewing scan data. Image Analysis allows users to view raw .tiff image files or data converted to HKL by loading SPEC and XML configuration files. 

## Installation

To install and prepare the program, open Command Prompt/Terminal to enter the following commands. Currently, the only way to run Image_Analysis is with the `git clone` command.  Clone the repository with the command below:

```
git clone https://github.com/henryjsmith12/Image_Analysis
```

Change directories into the project directory.

```
cd Image_Analysis
```

Activate the virtual environment. 

```
source venv/bin/activate
```

Install the proper Python libraries. A full list of the project's dependencies and their versions can be found in `requirements.txt`.

```
pip install requirements.txt
```

The program is now ready to run.

## Getting Started

Run the program by using the command below:

```
python image_analysis.py
```

The program's user interface should look like this on startup:

![Image Analysis GUI on Startup](https://github.com/henryjsmith12/Image_Analysis/blob/master/Screenshots/startup_gui.jpg)

## Support

* Report issues on the [Github issue tracker](https://github.com/henryjsmith12/Image_Analysis/issues).
* Email the author at smithh@anl.gov

