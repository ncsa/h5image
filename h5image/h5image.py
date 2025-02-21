import json

import affine
import h5py
import numpy as np
import rasterio

import math
import os
import os.path
import logging


class H5Image:
    """Class to read and write images to HDF5 file"""

    # initialize the class
    def __init__(self, h5file, mode='r', compression="lzf", patch_size=256, patch_border=3):
        """
        Create a new H5Image object. The patches in the file are assumed to be square and will
        be cropped to the patch size. The patch border is used to add a border around the patch,
        the tile size is the patch size minus the border. The image will be split in tiles based
        on the tile size. Any area outside of the image will be filled with 0.
        If the file is opened as read-only, no images can be added to the file and the patch size,
        border and compression are ignored.
        :param h5file: filename on disk
        :param mode: set to 'r' for read-only, 'w' for write, 'a' for append
        :param compression: compression type, None for no compression
        :param patch_size: size of patch, used to crop image and calculate good patches
        :param patch_border: border around patch, used to crop image and calculate good patches
        """
        self.h5file = h5file
        self.mode = mode
        if mode == 'w':
            if os.path.exists(h5file):
                self.h5f = h5py.File(h5file, mode)
                self.compression = self.h5f['/'].attrs.get('compression', compression.encode('utf-8')).decode('utf-8')
                if self.compression != compression:
                    logging.warning(f"compression mismatch, file: {self.compression}, parameter: {compression}, using file value")
                self.patch_size = self.h5f['/'].attrs.get('patch_size', patch_size)
                if self.patch_size != patch_size:
                    logging.warning(f"patch_size mismatch, file: {self.patch_size}, parameter: {patch_size}, using file value")
                self.patch_border = self.h5f['/'].attrs.get('patch_border', patch_border)
                if self.patch_border != patch_border:
                    logging.warning(f"patch_border mismatch, file: {self.patch_border}, parameter: {patch_border}, using file value")
            else:
                self.h5f = h5py.File(h5file, mode)
                self.h5f['/'].attrs.create('compression', compression, dtype=f'S{len(compression)}')
                self.h5f['/'].attrs.create('patch_size', patch_size, dtype=np.uint16)
                self.h5f['/'].attrs.create('patch_border', patch_border, dtype=np.uint16)
                self.compression = compression
                self.patch_size = patch_size
                self.patch_border = patch_border                
        else:
            if not os.path.exists(h5file):
                logging.error(f"File not found: {h5file}")
            self.h5f = h5py.File(h5file, mode)
            self.compression = self.h5f['/'].attrs.get('compression', compression.encode('utf-8')).decode('utf-8')
            if self.compression != compression:
                logging.warning(f"compression mismatch, file: {self.compression}, parameter: {compression}, using file value")
            self.patch_size = self.h5f['/'].attrs.get('patch_size', patch_size)
            if self.patch_size != patch_size:
                logging.warning(f"patch_size mismatch, file: {self.patch_size}, parameter: {patch_size}, using file value")
            self.patch_border = self.h5f['/'].attrs.get('patch_border', patch_border)
            if self.patch_border != patch_border:
                logging.warning(f"patch_border mismatch, file: {self.patch_border}, parameter: {patch_border}, using file value")
        self.tile_size = self.patch_size - (2 * self.patch_border)

    # close the file
    def close(self):
        """
        Close the file
        """
        self.h5f.close()

    def __str__(self):
        """
        String representation of the object
        :return: string representation
        """
        return f"H5Image(filename={self.h5file}, mode={self.mode}, patch_size={self.patch_size}, patch_border={self.patch_border}, tile_size={self.tile_size}, #maps={len(self.get_maps())})"

    # crop image
    def _crop_image(self, dset, x, y):
        """
        Helper function to crop an image.
        :param dset: the hdf5 dataset to crop
        :param x: upper left x coordinate
        :param y: upper left y coordinate
        :return: cropped image as numpy array
        """
        if x < 0 or x > dset.shape[0]:
            logging.error(f"Invalid x coordinate {x}")
            return None
        if y < 0 or y > dset.shape[1]:
            logging.error(f"Invalid y coordinate {y}")
            return None
        dst_x1 = dst_y1 = 0
        src_x1 = (x*self.tile_size) - self.patch_border
        if src_x1 < 0:
            dst_x1 = -src_x1
            src_x1 = 0
        src_x2 = (x*self.tile_size) + self.tile_size + self.patch_border
        if src_x2 > dset.shape[0]:
            src_x2 = dset.shape[0]
        src_y1 = (y*self.tile_size) - self.patch_border
        if src_y1 < 0:
            dst_y1 = -src_y1
            src_y1 = 0
        src_y2 = (y*self.tile_size) + self.tile_size + self.patch_border
        if src_y2 > dset.shape[1]:
            src_y2 = dset.shape[1]
        dst_x2 = dst_x1 + src_x2 - src_x1
        dst_y2 = dst_y1 + src_y2 - src_y1
        src = np.s_[src_x1:src_x2, src_y1:src_y2]
        dst = np.s_[dst_x1:dst_x2, dst_y1:dst_y2]
        if len(dset.shape) == 3 and dset.shape[2] == 3:
            rgb = np.zeros((self.patch_size, self.patch_size, 3), dtype=np.uint8)
        else:
            rgb = np.zeros((self.patch_size, self.patch_size), dtype=np.uint8)
        try:
            dset.read_direct(rgb, src, dst)
        except TypeError as e:
            logging.warn(f"{src_x1}, {src_x2}, {src_y1}, {src_y2}, {dst_x1}, {dst_x2}, {dst_y1}, {dst_y2}")
            logging.error(f"Error reading {dset.name} : {e}")
        return rgb

    def _add_image(self, filename, name, group):
        """
        Helper function to add an image to the file
        :param filename: image on disk
        :param name: name of image in hdf5 file
        :param group: parent folder of image
        :return: dataset of image loaded (numpy array)
        """
        if not os.path.exists(filename):
            print("File not found", filename)
            return None
        with rasterio.open(filename) as src:
            image = src.read()
            if len(image.shape) == 3:
                if image.shape[0] == 1:
                    image = image[0]
                elif image.shape[0] == 3:
                    image = image.transpose(1, 2, 0)
            dset = group.create_dataset(name=name, data=image, shape=image.shape, compression=self.compression)
            dset.attrs.create('CLASS', 'IMAGE', dtype='S6')
            dset.attrs.create('IMAGE_VERSION', '1.2', dtype='S4')
            dset.attrs.create('INTERLACE_MODE', 'INTERLACE_PIXEL', dtype='S16')
            dset.attrs.create('IMAGE_MINMAXRANGE', [0, 255], dtype=np.uint8)
            if len(image.shape) == 3 and image.shape[2] == 3:
                dset.attrs.create('IMAGE_SUBCLASS', 'IMAGE_TRUECOLOR', dtype='S16')
            elif len(image.shape) == 2 or image.shape[2] == 1:
                dset.attrs.create('IMAGE_SUBCLASS', 'IMAGE_GRAYSCALE', dtype='S15')
            else:
                raise Exception("Unknown image type")
            if src.profile.get('crs'):
                txt = src.profile['crs'].to_string()
                dset.attrs.create('CRS', txt, dtype=f'S{len(txt)}')
            if src.profile.get('transform'):
                txt = affine.dumpsw(src.profile['transform'])
                dset.attrs.create('TRANSFORM', txt, dtype=f'S{len(txt)}')
            return dset
        return None

    def add_layer(self, mapname, layername, filename):
        """
        Add a layer to the map. The layer is assumed to be a tiff file.
        :param mapname: the name of the map
        :param layername: the name of the layer
        :param filename: the tiff file to load
        """
        # make sure file is writeable
        if self.mode == 'r':
            raise Exception("Cannot add layer to read-only file")

        # check image file exists
        if not os.path.exists(filename):
            raise Exception("Image file not found")

        # get the map and compute the number of patches
        dset = self.get_layer(mapname, "map")
        w = math.ceil(dset.shape[0] / self.tile_size)
        h = math.ceil(dset.shape[1] / self.tile_size)

        # load the image and add it to the group
        group = self.h5f[mapname]
        all_patches = json.loads(group.attrs.get('patches', '{}'))
        layers_patch = json.loads(group.attrs.get('layers_patch', {}))
        patches = []
        dset = self._add_image(filename, layername, group)
        if dset:
            for x in range(w):
                for y in range(h):
                    rgb = self._crop_image(dset, x, y)
                    if np.average(rgb, axis=(0, 1)) > 0:
                        patches.append((x, y))
                        layers_patch.setdefault(f"{x}_{y}", []).append(layername)
            dset.attrs.update({'patches': json.dumps(patches)})
            all_patches[layername] = patches
        else:
            raise ValueError("Error loading layer {filename}")

        # update the group
        valid_patches = [[int(k.split('_')[0]), int(k.split('_')[1])] for k in layers_patch.keys()]
        if valid_patches:
            r1 = min(valid_patches, key=lambda value: int(value[0]))[0]
            r2 = max(valid_patches, key=lambda value: int(value[0]))[0]
            c1 = min(valid_patches, key=lambda value: int(value[1]))[1]
            c2 = max(valid_patches, key=lambda value: int(value[1]))[1]
            group.attrs.update({'corners': [[r1, c1], [r2, c2]]})
        group.attrs.update({'patches': json.dumps(all_patches)})
        group.attrs.update({'layers_patch': json.dumps(layers_patch)})
        group.attrs.update({'valid_patches': json.dumps(valid_patches)})

    # add an image to the file
    def add_image(self, filename, folder="", mapname=""):
        """
        Add a set of images to the file. The filenname is assumed to be json and is
        used to load all images with the same prefix. The map is assumed to have the
        same prefix as the json file (but ending with .tif). The json file lists all
        layers that are added as well. The json file is attached to the group.
        :param filename: the json file to load
        :param folder: directory where to find the json file
        :param mapname: the name of the map, if empty the name of the json file is used
        """
        # make sure file is writeable
        if self.mode == 'r':
            raise Exception("Cannot add image to read-only file")

        # check json file
        if not filename.endswith(".json"):
            raise Exception("Need to pass json file")
        jsonfile = os.path.join(folder, filename)
        if not os.path.exists(jsonfile):
            raise Exception("File not found")
        prefix = jsonfile.replace(".json", "")
        if mapname == "":
            mapname = os.path.basename(prefix)

        # check image file exists
        tiffile = f"{prefix}.tif"
        if not os.path.exists(tiffile):
            tiffile = f"{prefix}.tiff"
        if not os.path.exists(tiffile):
            raise Exception("Image file not found")

        # load json
        json_data = json.load(open(jsonfile))
        if 'shapes' not in json_data or len(json_data['shapes']) == 0:
            raise Exception("No shapes found")

        # create the group
        group = self.h5f.create_group(mapname)
        group.attrs.update({'json': json.dumps(json_data)})

        # load image
        dset = self._add_image(tiffile, "map", group)
        w = math.ceil(dset.shape[0] / self.tile_size)
        h = math.ceil(dset.shape[1] / self.tile_size)

        # loop through shapes
        all_patches = {}
        layers_patch = {}
        for shape in json_data['shapes']:
            label = shape['label']
            patches = []
            try:
                dset = self._add_image(f"{prefix}_{label}.tif", label, group)
                if dset:
                    for x in range(w):
                        for y in range(h):
                            rgb = self._crop_image(dset, x, y)
                            if np.average(rgb, axis=(0, 1)) > 0:
                                patches.append((x, y))
                                layers_patch.setdefault(f"{x}_{y}", []).append(label)
                    dset.attrs.update({'patches': json.dumps(patches)})
                    all_patches[label] = patches
            except ValueError as e:
                logging.warning(f"Error loading {label} : {e}")
        valid_patches = [[int(k.split('_')[0]), int(k.split('_')[1])] for k in layers_patch.keys()]
        if valid_patches:
            r1 = min(valid_patches, key=lambda value: int(value[0]))[0]
            r2 = max(valid_patches, key=lambda value: int(value[0]))[0]
            c1 = min(valid_patches, key=lambda value: int(value[1]))[1]
            c2 = max(valid_patches, key=lambda value: int(value[1]))[1]
            group.attrs.update({'corners': [[r1, c1], [r2, c2]]})
        group.attrs.update({'patches': json.dumps(all_patches)})
        group.attrs.update({'layers_patch': json.dumps(layers_patch)})
        group.attrs.update({'valid_patches': json.dumps(valid_patches)})

    def save_image(self, mapname, destination, layer=None):
        """
        Save the image to disk. The image is saved as a tiff file, if no layer is given
        it will write all layers for the map, and the json file to the destination, otherwise
        it will just write the layer.
        :param mapname: the name of the map
        :param destination: the destination directory
        :param layer: the name of the layer, if empty all layers are written
        """
        if not os.path.exists(destination):
            os.makedirs(destination)
        if layer is None:
            self.save_image(mapname, destination, "map")
            json_data = json.loads(self.h5f[mapname].attrs['json'])
            json.dump(json_data, open(os.path.join(destination, f"{mapname}.json"), "w"), indent=2)
            for layer in self.get_layers(mapname):
                self.save_image(mapname, destination, layer)
        else:
            dset = self.h5f[mapname][layer]
            if dset.ndim == 3:
                image = dset[...].transpose(2, 0, 1)  # rasterio expects bands first
            else:
                image = np.array(dset[...], ndmin=3)
            if layer == "map":
                filename = os.path.join(destination, f"{mapname}.tif")
            else:
                filename = os.path.join(destination, f"{mapname}_{layer}.tif")
            rasterio.open(filename, 'w', driver='GTiff', compress='lzw',
                          height=image.shape[1], width=image.shape[2], count=image.shape[0], dtype=image.dtype,
                          crs=self.get_crs(mapname, layer), transform=self.get_transform(mapname, layer)).write(image)

    # get list of all maps
    def get_maps(self):
        """
        Returns a list of all maps in the file.
        :return: list of map names
        """
        return list(self.h5f.keys())

    # get map by index
    def get_map(self, mapname):
        """
        Returns the map as a numpy array.
        :param mapname: the name of the map
        :return: image as numpy array
        """
        return self.h5f[mapname]['map']

    # return map size
    def get_map_size(self, mapname):
        """
        Returns the size of the map.
        :param mapname: the name of the map
        :return: size of the map
        """
        return self.h5f[mapname]['map'].shape

    def get_crs(self, mapname, layer='map'):
        """
        Returns the crs of the layer (defaults to the map).
        :param mapname: the name of the map
        :param layer: the name of the layer, defaults to the map
        :return: crs of the map
        """
        if 'CRS' in self.h5f[mapname][layer].attrs:
            return rasterio.CRS.from_string(self.h5f[mapname][layer].attrs['CRS'].decode('utf-8'))
        return None

    def get_transform(self, mapname, layer='map'):
        """
        Returns the transform of the layer (defaults to the map).
        :param mapname: the name of the map
        :param layer: the name of the layer, defaults to the map
        :return: transform of the map
        """
        if 'TRANSFORM' in self.h5f[mapname][layer].attrs:
            return affine.loadsw(self.h5f[mapname][layer].attrs['TRANSFORM'].decode('utf-8'))
        return None

    def get_map_corners(self, mapname):
        """
        Returns the bounds of the map.
        :param mapname: the name of the map
        :return: bounds of the map
        """
        return list(self.h5f[mapname].attrs['corners'])

    # get list of all layers for map
    def get_layers(self, mapname):
        """
        Returns a list of all layers for a map.
        :param mapname: the name of the map
        :return: list of layer names
        """
        layers = list(self.h5f[mapname].keys())
        layers.remove('map')
        return layers

    def get_layer(self, mapname, layer):
        """
        Returns the layer as a numpy array.
        :param mapname: the name of the map
        :param layer: the name of the layer
        :return: image as numpy array
        """
        return self.h5f[mapname][layer]

    def get_patches(self, mapname, by_location=False):
        """
        Returns a list of all patches for a map. The patches are grouped by layer. If by_location is
        False it returns a dict of layers, each with a list of patches (as arrays). If by location
        the result will be a dict of patches (col-row) , each with a list of layers.
        patches for a map
        :param mapname: the name of the map
        :param by_location: if True, return a dictionary with locations as keys and layers as values
        :return: list of patches
        """
        if by_location:
            return json.loads(self.h5f[mapname].attrs['layers_patch'])
        else:
            return json.loads(self.h5f[mapname].attrs['patches'])

    def get_valid_patches(self, mapname):
        """
        Returns a list of all valid patches for a map. A valid patch is a patch that has
        at least one layer with a value > 0.
        :param mapname: the name of the map
        :return: list of valid patches
        """
        return json.loads(self.h5f[mapname].attrs['valid_patches'])

    def get_patches_for_layer(self, mapname, layer):
        """
        Returns a list of all patches for a layer.
        :param mapname: the name of the map
        :param layer: the name of the layer
        :return: list of patches
        """
        return json.loads(self.h5f[mapname][layer].attrs['patches'])

    def get_layers_for_patch(self, mapname, row, col):
        """
        Returns a list of all layers for a patch.
        :param mapname: the name of the map
        :param row: the row of the patch
        :param col: the column of the patch
        :return: list of layers
        """
        return json.loads(self.h5f[mapname].attrs['layers_patch']).get(f"{row}_{col}", [])

    # get legend from map
    def get_legend(self, mapname, layer):
        """
        Returns the cropped image of the legend in the map.
        :param mapname: the name of the map
        :param layer: the name of the layer
        :return: cropped image of legend
        """
        json_data = json.loads(self.h5f[mapname].attrs['json'])
        for shape in json_data['shapes']:
            if shape['label'] == layer:
                points = shape['points']
                y, x = zip(*points)
                x1 = int(min(x))
                x2 = int(max(x))
                y1 = int(min(y))
                y2 = int(max(y))
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                # points in array are floats
                src = np.s_[int(x1):int(x2), int(y1):int(y2)]
                dset = self.h5f[mapname]['map']
                if len(dset.shape) == 3 and dset.shape[2] == 3:
                    rgb = np.zeros((w, h, 3), dtype=np.uint8)
                else:
                    rgb = np.zeros((w, h), dtype=np.uint8)
                try:
                    dset.read_direct(rgb, src)
                except TypeError as e:
                    logging.warn(f"{x1}, {x2}, {y1}, {y2}")
                    logging.error(f"Error reading legend {dset.name} : {e}")
                return rgb
        return None

    # get patch by index
    # row and col are 0 based
    def get_patch(self, row, col, mapname, layer="map"):
        """
        Returns the cropped image of the patch.
        :param row: the row of the patch
        :param col: the column of the patch
        :param mapname: the name of the map
        :param layer: the name of the layer
        :return: cropped image of patch as a numpy array
        """
        if row < 0 or col < 0:
            raise Exception("Invalid index")
        return self._crop_image(self.h5f[mapname][layer], row, col)
