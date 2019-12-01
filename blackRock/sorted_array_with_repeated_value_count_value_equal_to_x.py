
def binary_search(arr, x):
    if arr:
        l = len(arr)
        if arr[l/2]==x:
            return binary_search(arr[l/2+1:], x) + 1 + binary_search(arr[:l/2], x)
        elif arr[l/2]<x:
            return binary_search(arr[l/2+1:], x)
        elif arr[l/2]>x:
            return binary_search(arr[:l/2], x)
    else:
        return 0


arr = [1,1,1,3,3,3,3,3,3,3,3,3,3,3,3,3,3,5,5,5,6,6,6]
print binary_search(arr, 5)