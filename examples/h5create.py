import glob
import os.path
import time
from h5image import H5Image

folder = "./data"
patch = 256

for file in glob.glob(f"{folder}/*.json"):
    h5file = os.path.basename(file).replace('.json', '.hdf5')
    h5path = f"hdf/{patch}/{h5file}"
    if not os.path.exists(h5path):
        h5i = H5Image(h5path, "w", patch_size=patch)
        t = time.time()
        h5i.add_image(file)
        print(os.path.basename(file), time.time() - t)
        h5i.close()
