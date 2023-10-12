import math
from concurrent.futures import ThreadPoolExecutor

from h5image import H5Image
import os
import time
import random
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import json

plot = True

######################################################################
## CREATE/OPEN FILE
######################################################################
# os.unlink("CA_Sage.hdf5")
if not os.path.exists("hdf/256/CA_Sage.hdf5"):
    t = time.time()
    h5i = H5Image("hdf/256/CA_Sage.hdf5", "w")
    print("open", time.time()-t)
    t = time.time()
    h5i.add_image("CA_Sage.json", folder="./data")
    print("create", time.time()-t)
else:
    t = time.time()
    h5i = H5Image("hdf/256/CA_Sage.hdf5", "r")
    print("open", time.time()-t)

######################################################################
## SHOW CORNER PATCHES
######################################################################
bounds = h5i.get_map_corners('CA_Sage')
fig = plt.figure(figsize=(10, 10))
idx = 1
for r in [bounds[0][0], bounds[1][0]]:
    for c in [bounds[0][1], bounds[1][1]]:
        rgb = h5i.get_patch(r, c, 'CA_Sage')
        fig.add_subplot(2, 2, idx)
        plt.imshow(rgb)
        plt.title(f'row {r}, col {c}')
        plt.axis('off')
        idx += 1
fig.show()

# ######################################################################
# ## DISPLAY FILE INFO
# ######################################################################
print(h5i)

# ######################################################################
# ## MAP INFO
# ######################################################################
maps = h5i.get_maps()
print(len(maps))
map = random.choice(maps)
layers = h5i.get_layers(map)
print(map, len(layers))

# ######################################################################
# ## PLOT MAP
# ######################################################################
t = time.time()
rgb = h5i.get_map(map)
print(map, rgb.shape)
if plot:
    plt.imshow(rgb)
    plt.title('full map')
    plt.axis('off')
    plt.show()
print("map", time.time() - t)
#
# ######################################################################
# ## PLOT PATCH
# ######################################################################
patches = h5i.get_patches(map, True)
sorted_patches = {k: v for k, v in sorted(patches.items(), key=lambda item: len(item[1]), reverse=True)}
loc, loc_layers = next(iter(sorted_patches.items()))
row = int(loc.split("_")[0])
col = int(loc.split("_")[1])
print(f"Biggest number of layers ({len(loc_layers)}) for {map} is at ( {row}, {col})")

if plot:
    total = 2 * len(loc_layers)
    fig = plt.figure(figsize=(10, 20))
    idx = 1
    size = math.ceil(math.sqrt(total)/2) * 2
    print(size)

t = time.time()
rgb = h5i.get_patch(row, col, map)
if plot:
    fig.add_subplot(1, 2, 1)
    plt.imshow(rgb)
    plt.title('map')
    plt.axis('off')
    idx += 1
print("patch", time.time() - t)

t = time.time()
if plot:
    fig.add_subplot(1, 2, 1)

for layer in layers:
    rgb = h5i.get_patch(row, col, map, layer=layer)
    if np.average(rgb, axis=(0, 1)) > 0:
        if plot:
            fig.add_subplot(size, size, idx)
            plt.imshow(rgb, cmap=mpl.colormaps['plasma'])
            plt.title(layer)
            plt.axis('off')
            idx += 1
        rgb = h5i.get_legend(map, layer)
        if plot:
            fig.add_subplot(size, size, idx)
            plt.imshow(rgb)
            plt.title("legend")
            plt.axis('off')
            idx += 1
if plot:
    print(idx)
    fig.show()
print("patches", time.time() - t)


# ######################################################################
# ## SPEED TEST
# ######################################################################
def compute(count):
    for i in range(int(2000/count)):
        map = random.choice(maps)
        bounds = h5i.get_map_size(map)
        patches = h5i.get_patches(map, by_location=True)
        patch = random.choice(list(patches.keys()))
        row = int(patch.split("_")[0])
        col = int(patch.split("_")[1])
        layer = random.choice(patches.get(patch))
        h5i.get_patch(row, col, map)
        h5i.get_patch(row, col, map, layer)
        try:
            h5i.get_legend(map, layer)
        except:
            print(f"Error loading legend {layer} for {map}")

t = time.time()
with ThreadPoolExecutor(max_workers=16) as executor:
    future = executor.submit(compute, 16)
    future.result()
print("loop", time.time()-t)
