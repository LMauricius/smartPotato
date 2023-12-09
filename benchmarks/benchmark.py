import requests
from PIL import Image
import time

"""
Execute this to see the performance of imgbeddings
"""

url = "http://images.cocodataset.org/val2017/000000039769.jpg"
s_time = time.time()
image = Image.open(requests.get(url, stream=True).raw)
e_time = time.time()
print(f"Download took {e_time - s_time} seconds.")

s_time = time.time()
from imgbeddings import imgbeddings

e_time = time.time()
print(f"Import took {e_time - s_time} seconds.")
s_time = time.time()
ibed = imgbeddings()
e_time = time.time()
print(f"Model load took {e_time - s_time} seconds.")

s_time = time.time()
embedding = ibed.to_embeddings(image)
e_time = time.time()
print(
    repr(embedding[0][0:5])
)  # array([ 0.914541, 0.45988417, 0.0350069 , -0.9054574 , 0.08941309], dtype=float32)
print(f"Calc took {e_time - s_time} seconds.")
