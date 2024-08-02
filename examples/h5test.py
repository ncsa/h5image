import math
from concurrent.futures import ThreadPoolExecutor

from h5image import H5Image
import os
import sys
import time
import random
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib as mpl
import numpy as np
import json

filename = "CA_Sage"
patch_size = 256
patch_border = 25

######################################################################
## CREATE/OPEN FILE
######################################################################
# if os.path.exists(f"hdf/{patch_size}/{patch_border}/{filename}.hdf5"):
#     os.unlink(f"hdf/{patch_size}/{patch_border}/{filename}.hdf5")
os.makedirs(os.path.dirname(f"hdf/{patch_size}/{patch_border}/{filename}.hdf5"), exist_ok=True)
if not os.path.exists(f"hdf/{patch_size}/{patch_border}/{filename}.hdf5"):
    t = time.time()
    h5i = H5Image(f"hdf/{patch_size}/{patch_border}/{filename}.hdf5", "w", patch_size=patch_size, patch_border=patch_border)
    print("open", time.time()-t)
    t = time.time()
    h5i.add_image(f"{filename}.json", folder="./data")
    print("create", time.time()-t)
else:
    t = time.time()
    h5i = H5Image(f"hdf/{patch_size}/{patch_border}/{filename}.hdf5", "r", patch_size=300, patch_border=99)
    print("open", time.time()-t)

######################################################################
## SHOW PATCHES
######################################################################
# fig = plt.figure(figsize=(10, 10))
# for r in range(0, 5):
#     for c in range(0, 5):
#         rgb = h5i.get_patch(r, c, 'CA_Sage')
#         ax = fig.add_subplot(5, 5, r*5+c+1)
#         plt.imshow(rgb)
#         plt.axis('off')
#         rect = patches.Rectangle((0, 0), h5i.patch_size-1, h5i.patch_size-1, linewidth=1, edgecolor='b', facecolor='none')
#         ax.add_patch(rect)
#         rect = patches.Rectangle((h5i.patch_border, h5i.patch_border), h5i.tile_size-1, h5i.tile_size-1, linewidth=1, edgecolor='r', facecolor='none')
#         ax.add_patch(rect)
# fig.show()

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
# fig = plt.figure(figsize=(10, 10))
# t = time.time()
# rgb = h5i.get_map(map)
# print(map, rgb.shape)
# plt.imshow(rgb)
# plt.title('full map')
# plt.axis('off')
# fig.show()

# print("map", time.time() - t)
#
# ######################################################################
# ## PLOT PATCH
# ######################################################################
fig = plt.figure(figsize=(10, 10))
patches = h5i.get_patches(map, True)
sorted_patches = {k: v for k, v in sorted(patches.items(), key=lambda item: len(item[1]), reverse=True)}
loc, loc_layers = next(iter(sorted_patches.items()))
row = int(loc.split("_")[0])
col = int(loc.split("_")[1])
print(f"Biggest number of layers ({len(loc_layers)}) for {map} is at ( {row}, {col})")

total = 2 * len(loc_layers)
fig = plt.figure(figsize=(10, 20))
idx = 1
size = math.ceil(math.sqrt(total)/2) * 2
print(size)

fig = plt.figure(figsize=(10, 10))
layers = h5i.get_layers(map)
for layer in layers:
    if idx > 14:
        break
    rgb = h5i.get_patch(row, col, map, layer=layer)
    if np.average(rgb, axis=(0, 1)) > 0:
        fig.add_subplot(size, size, idx)
        plt.imshow(rgb, cmap=mpl.colormaps['plasma'])
        plt.title(layer)
        plt.axis('off')
        idx += 1
        rgb = h5i.get_legend(map, layer)
        fig.add_subplot(size, size, idx)
        plt.imshow(rgb)
        plt.title("legend")
        plt.axis('off')
        idx += 1

while True:
    plt.pause(0.05)
    if plt.waitforbuttonpress():
        break
sys.exit(0)

t = time.time()
rgb = h5i.get_patch(row, col, map)
fig.add_subplot(1, 2, 1)
plt.imshow(rgb)
plt.title('map')
plt.axis('off')
fig.show()
idx += 1
print("patch", time.time() - t)

t = time.time()
fig.add_subplot(1, 2, 1)

for layer in layers:
    if idx > 14:
        break
    rgb = h5i.get_patch(row, col, map, layer=layer)
    if np.average(rgb, axis=(0, 1)) > 0:
        fig.add_subplot(size, size, idx)
        plt.imshow(rgb, cmap=mpl.colormaps['plasma'])
        plt.title(layer)
        plt.axis('off')
        idx += 1
        rgb = h5i.get_legend(map, layer)
        fig.add_subplot(size, size, idx)
        plt.imshow(rgb)
        plt.title("legend")
        plt.axis('off')
        idx += 1
print(idx)
fig.show()
print("patches", time.time() - t)

while True:
    plt.pause(0.05)
    if plt.waitforbuttonpress():
        break
sys.exit(0)


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
