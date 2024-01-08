import argparse
import pathlib

import glob
import os.path
import time
from h5image import H5Image


def h5convert(input, output, patch=256, border=3):
    for file in glob.glob(f"{input}/*.json"):
        h5file = os.path.basename(file).replace('.json', '.hdf5')
        h5path = f"{output}/{patch}/{border}/{h5file}"
        os.makedirs(os.path.dirname(h5path), exist_ok=True)
        if not os.path.exists(h5path):
            h5i = H5Image(h5path, "w", patch_size=patch, patch_border=border)
            t = time.time()
            h5i.add_image(file)
            print(os.path.basename(file), time.time() - t)
            h5i.close()


def h5create():
    parser = argparse.ArgumentParser(description='Convert trainging data to HDF5 files.')
    parser.add_argument('--input', type=pathlib.Path, default='data',
                        help='input folder (default: data)')
    parser.add_argument('--output', type=pathlib.Path, default='hdf',
                        help='output folder (default: hdf)')
    parser.add_argument('--patch', type=int, default=256,
                        help='patch size (default: 256)')
    parser.add_argument('--border', type=int, default=3,
                        help='patch size (default: 3)')
    args = parser.parse_args()
    h5convert(args.input, args.output, args.patch, args.border)
