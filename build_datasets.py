import requests
import shutil
import os
import errno
import random
import math
import re

num_samples = 3500
num_valid = int(num_samples * .3)

# api-endpoint
URL = "https://isic-archive.com/api/v1/image?limit=" + str(num_samples) + "&offset=10000&sort=name&sortdir=1&detail=true"

# sending get request and saving the response as response object
r = requests.get(url = URL)

# extracting data in json format
data = r.json()
data = filter(lambda item: "anatom_site_general" in item["meta"]["clinical"] \
and item["meta"]["clinical"]["anatom_site_general"] is not None \
and "sex" in item["meta"]["clinical"] \
and item["meta"]["clinical"]["sex"] is not None \
and "age_approx" in item["meta"]["clinical"] \
and item["meta"]["clinical"]["age_approx"] is not None \
and item["meta"]["clinical"]["age_approx"] != 0 \
, data)
print(len(data))

# shuffle data to avoid preexisting sample clump
random.Random(229).shuffle(data)

# labels
labels = [{}, {}, {}, {}]

for index in range(len(data)):
    train_or_valid = "valid" if index < num_valid else "train"
    i = data[index]
    if index % 10 == 0:
        print(index)
    URL = "https://isic-archive.com/api/v1/image/" + i["_id"] + "/thumbnail?width=299&height=299"
    r = requests.get(url = URL, stream=True)
    clinical = i["meta"]["clinical"]
    for j in range(4):
        label = clinical["benign_malignant"]
        if j >= 1:
            label += " " + clinical["anatom_site_general"].replace("/", " or ")
        if j >= 2:
            label += " " + str(int(math.floor(clinical["age_approx"] / 10.) * 10)) + "s"
        if j >= 3:
            label += " " + clinical["sex"]
        if label not in labels[j]:
            labels[j][label] = True
        filename = "./" + train_or_valid + "_" + str(j) + "/" + label + "/" + i["name"] + ".jpg"
        if not os.path.exists(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        with open(filename, "wb") as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

# write labels to files
for j in range(4):
    with open("./labels_" + str(j), "wb") as f:
        for l in labels:
            f.write(l + "\n")