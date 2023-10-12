import glob
import concurrent.futures

from h5image import H5Image
import os
import time
import random
import math


workers = 4
numjobs = 4
jobspatch = 30
# total number of patches = numjobs * jobspatch


######################################################################
## OPEN FOLDER
######################################################################
def setup():
    mapsh5i = {}
    for file in glob.glob("hdf/256/*.hdf5"):
        mapname = os.path.basename(file).replace(".hdf5", "")
        mapsh5i[mapname] = H5Image(file, "r")
    return mapsh5i


def main():
    t = time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        jobs = [executor.submit(compute, jobspatch) for x in range(numjobs)]
        for job in concurrent.futures.as_completed(jobs):
            data = job.result()
            #print(len(data))
            #print(job.result())
    print("loop", time.time()-t)


######################################################################
## PARALEL CODE
######################################################################
def compute(count):
    mapsh5i = setup()
    maps = list(mapsh5i.keys())
    result = []
    for i in range(count):
        map = random.choice(maps)
        bounds = mapsh5i[map].get_map_size(map)
        patches = mapsh5i[map].get_patches(map, by_location=True)
        patch = random.choice(list(patches.keys()))
        row = int(patch.split("_")[0])
        col = int(patch.split("_")[1])
        layer = random.choice(patches.get(patch))
        rgb_map = mapsh5i[map].get_patch(row, col, map)
        rgb_layer = mapsh5i[map].get_patch(row, col, map, layer)
        try:
            rgb_legend = mapsh5i[map].get_legend(map, layer)
        except:
            rgb_legend = []
            print(f"Error loading legend {layer} for {map}")
        result.append({ "map": rgb_map, "layer": rgb_layer, "legend": rgb_legend, "mapname": map, "layername": layer })
    return result


if __name__ == "__main__":
    main()
