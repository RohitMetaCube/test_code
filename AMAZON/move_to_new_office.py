'''
# Read input from stdin and provide input before running code

name = raw_input()
print 'Hi, %s.' % name
'''
#print 'Hello World!'
def min_cost(arr, arr2, n):
    if arr == arr2:
        return 0
    return min([
        X*(arr[i]-max(arr2[:i])) + Y*(min(x for x in arr2[(i+1):] if x)-arr[i]) + 
        min_cost(arr, arr2[:i] + [arr[i]] + arr2[(i+1):], n) 
        for i in range(1,n-1) if not arr2[i]
    ])

t = input()
while t:
    t-=1
    [X,Y]= [int(x) for x in raw_input().split()]
    n = input()
    arr = [int(x) for x in raw_input().split()]
    print min_cost(arr, [arr[0]] + [0 for _ in range(1, n-1)] + [arr[n-1]], n)