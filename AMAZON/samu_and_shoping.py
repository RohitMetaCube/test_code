'''
# Read input from stdin and provide input before running code

name = raw_input()
print 'Hi, %s.' % name
'''
t = input()
while t:
    t-=1
    n = input()
    A, B, C = 0, 0, 0
    flag = 0
    while n:
        n-=1
        [shirt, pant, shoe] = [int(x) for x in raw_input().split()]
        t1 = shirt + min(B, C)
        t2 = pant + min(A, C)
        t3 = shoe + min(A, B)
        A, B, C = t1,t2,t3 
    print min(A,B,C)