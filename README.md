# h5image

This package provides standard functions for interacting with HDF5 files as
part of the CriticalMAAS project.

This package will create HDF5 files with the following structure:

- group : all data associated with a single map
    - `json` : the raw json file used to create the map and layers
    - `map` : the actual map image
        - `data` : the actual bytes of the image
        - `corners` : the corners of the map where layers have data
        - `patches` : for each layer (key) a list of patches as a tuple (x, y)
        - `layers_patch` : for each patch (key is x_y) a list of layers
        - `valid_patche`  : a list of locations across all layers as a tuple (x, y)
    - `<layer>` : a layer of the map, the name of the layer is the name of file
        - `data` : the actual layer data
        - `patches` : a list of patches as a tuple (x, y) for this specific layer

Installation
------------

Install using pip:

```
pip install h5image
```

To convert a folder of images to a HDF5 file use the `h5create` program.

Quickstart example
------------------

The following code will create a new HDF5 file with a map and a layer, find the
patch with most layers, and load the map and the layers at that patch.

```python
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from h5image import H5Image

# create map file
map = "CA_Sage"
h5i = H5Image(f"{map}.hdf5", "w")
h5i.add_image(f"{map}.json", folder="./data")

# get biggest patch
patches = h5i.get_patches(map, True)
sorted_patches = {k: v for k, v in sorted(patches.items(), key=lambda item: len(item[1]), reverse=True)}
loc, loc_layers = next(iter(sorted_patches.items()))
row = int(loc.split("_")[0])
col = int(loc.split("_")[1])
print(f"Biggest number of layers ({len(loc_layers)}) for {map} is at ( {row}, {col})")

# plot map
rgb = h5i.get_patch(row, col, map)
plt.imshow(rgb)
plt.title('map')
plt.axis('off')
plt.show()

# plot layers and legend
for layer in loc_layers:
    rgb = h5i.get_patch(row, col, map, layer=layer)
    plt.imshow(rgb, cmap=plt.colormaps['plasma'])
    plt.title(layer)
    plt.axis('off')
    plt.show()

    rgb = h5i.get_legend(map, layer)
    plt.imshow(rgb)
    plt.title("legend")
    plt.axis('off')
    plt.show()

# saving image as geotiff
# can also use h5i.save_image(map, 'map')
dset = h5i.get_map(map)
if dset.ndim == 3:
    image = dset[...].transpose(2, 0, 1)  # rasterio expects bands first
else:
    image = np.array(dset[...], ndmin=3)
rasterio.open(f"{map}.tif", 'w', driver='GTiff', compress='lzw',
              height=image.shape[1], width=image.shape[2], count=image.shape[0], dtype=image.dtype,
              crs=h5i.get_crs(map, layer), transform=h5i.get_transform(map, layer)).write(image)

# close file
h5i.close()
```
