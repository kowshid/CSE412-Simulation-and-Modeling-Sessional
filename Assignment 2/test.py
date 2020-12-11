import numpy as np

arr1 =[1, 2, 3]
arr2 = [0.3, 0.2, 0.5]

temp = np.random.choice(arr1, p = arr2)

print(temp)