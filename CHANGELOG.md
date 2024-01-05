# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to [Semantic Versioning](http://semver.org/).

- [ ] Add h5folder that will read all hdf5 files in a folder
- [ ] Add ability to read patches using h5folder
- [ ] Catch exception when reading bad legend

## 0.2.0 - 2023-11-02

### Added
- Added geospatial information to HDF5 file
- Added save_image method to save image to file
- Added dependency on rasterio
- h5create is now a program that will convert a folder of images to a hdf5 files 

### Removed
- Removed dependency on opencv

## 0.1.0 - 2023-10-11

Initial release of h5image
