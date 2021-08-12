.. restructured text format

About these example data files
----------------------------------

These files are examples of various
data files that may be read by **spec2nexus**.
They are used to test various components of the interface.


======================================  ==========  ==========================================================================
file						            type	    description
======================================  ==========  ==========================================================================
02_03_setup.dat                         SPEC scans  1-D scans, some have no data lines (data are stored in HDF5 file)
03_06_JanTest.dat                       SPEC scans  1-D scans, USAXS scans, Fly scans, #O+#o and #J+#j control lines
05_02_test.dat                          SPEC scans  1-D scans, USAXS scans, Fly scans, multiple #F control lines, multiple #S 1 control lines
33bm_spec.dat                           SPEC scans  1-D & 2-D scans (includes hklscan & hklmesh)
33id_spec.dat                           SPEC scans  1-D & 2-D scans (includes mesh & Escan scans & MCA data)
APS_spec_data.dat                       SPEC scans  1-D scans (ascan & uascan), includes lots of metadata and comments
CdOsO                                   SPEC scans  1-D scans (ascan), four #E (2, 3659, 3692, 3800) and two #S 1 (35, 3725)
CdSe                                    SPEC scans  1-D scans (ascan), problem with scan abort on lines 5918-9, in scan 92
compression.h5                          NeXus HDF5  2-D compressed image, also demonstrates problem to be resolved in code
Data_Q.h5                               NeXus HDF5  2-D image at /entry/data/{I,Q}, test file and variable-length strings
lmn40.spe                               SPEC scans  1-D & 2-D scans (hklmesh), two #E lines, has two header sections
mca_spectra_example.dat                 SPEC scans  1-D scans (cscan) with 4 MCA spectra in each scan (issue #55)
spec_from_spock.spc                     SPEC scans  no header section, uses "nan", from sardana
startup_1.spec                          SPEC scans  1-D scans with SCA spectra & UXML headers for RSM code
user6idd.dat                            SPEC scans  1-D scans, aborted scan, control lines:  #R #UB #UE #UX #UX1 #UX2 #X, 
                                                    non-default format in #X lines
usaxs-bluesky-specwritercallback.dat    SPEC scans  1-D scans, #MD control lines
writer_1_3.h5                           NeXus HDF5  1-D NeXus User Manual example
YSZ011_ALDITO_Fe2O3_planar_fired_1.spc  SPEC scans  1-D scans, text in #V metadata, also has #UIM control lines
======================================  ==========  ==========================================================================
