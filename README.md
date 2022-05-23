# Image_Analysis

Copyright (c) UChicago Argonne, LLC. All rights reserved.

A lightweight option to view, map, and convert X-ray diffraction (XRD) scan datasets. 

## About

![Examples of Gridding and Mapping Features](https://github.com/henryjsmith12/Image_Analysis/blob/base/screenshots/README_About.png)

Image_Analysis provides users with two features for visualizing experiment data: mapping and gridding. The "Gridding" tab (left) gives users the ability to convert and analyze sets of scan images as 3D datasets in reciprocal space. The "Mapping" tab (right) allows users to view raw scan data and create reciprocal space maps for individual images. 

### Built With

* [`PyQt5`](https://github.com/baoboa/pyqt5) (General GUI Framework)
* [`pyqtgraph`](https://github.com/pyqtgraph/pyqtgraph) (Plotting Framework)
* [`xrayutilities`](https://github.com/dkriegner/xrayutilities) (RSM Conversions)
* [`rsMap3D`](https://github.com/AdvancedPhotonSource/rsMap3D) (RSM Gridding)

See [`environment.yml`](https://github.com/henryjsmith12/Image_Analysis/blob/master/environment.yml) for a full list of dependencies.

## Getting Started

### Requirements

* Python 3.7+
* Anaconda

### Installation

Currently, Image_Analysis can only be used with a conda virtual environment from Anaconda. To install and prepare the program for use, open Command Prompt/Terminal to enter the following commands:

1. Clone the repository.

```
git clone https://github.com/henryjsmith12/Image_Analysis
```

2. The next task is to create/activate the conda virtual environment. Change directories into the Image_Analysis project directory.

```
cd Image_Analysis
```

3. Create the conda environment. This virtual environment will contain all of the necessary dependencies to run Image_Analysis. The name of the environment can be changed in the [`environment.yml`](https://github.com/henryjsmith12/Image_Analysis/blob/master/environment.yml) file.

```
conda env create -f environment.yml
```

4. Activate the conda environment. 

```
conda activate image_analysis_venv
```

5. With the virtual environment activated, the program is now ready to run. The command below will run Image_Analysis.

```
python image_analysis.py
```

## Usage

## Roadmap

## License

## Author

Henry Smith - Co-op Student Technical at Argonne National Laboratory

## Support

* Report issues on the [Github issue tracker](https://github.com/henryjsmith12/Image_Analysis/issues).
* Email the author at smithh@anl.gov
