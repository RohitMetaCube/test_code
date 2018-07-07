u'Input:'

'''
3
2 7 5 1 6 -1 9 -1 -1 8 11 -1 -1 4 -1
6
ADD 1 L 3
SUM 0 6
UPDATE 11 13
DELETE 5
SUM -1 7
SUM 3 2
'''

u'Output:'
'''
25
38
53
'''


class BinaryOperations:
    def __init__(self, arr, depth):
        self.index_map = {}
        for i, x in enumerate(arr):
            self.index_map[x] = i
        self.arr = arr
        self.end_index = pow(2, depth+1) - 1
    
    def add(self, parent, position, value):
        if position=='L':
            pindex = self.index_map[parent]
            if 2*pindex+1 < self.end_index:
                self.arr[2*pindex+1] = value
        else:
            pindex = self.index_map[parent]
            if 2*pindex+1 < self.end_index:
                self.arr[2*pindex+1] = value
    
    def update(self, value, new_value):
        pindex = self.index_map[value]
        self.arr[pindex] = new_value
        
    def delete(self, value):
        pindex = self.index_map[value]
        self.arr[pindex] = -1
    
    def move_next(self, current_index):
        summ = 0
        if current_index < self.end_index:
            if self.arr[current_index]>0:
                summ += self.arr[current_index]
            left = self.move_next(2*current_index+1)
            right = self.move_next(2*current_index+2)
            summ += left + right
        return summ
    
    def sum(self, parent):
        pindex = self.index_map[parent]
        return self.move_next(pindex)
        
            

def main():
    d =  input()
    a =  [int(x) for x  in raw_input().split()]
    n =  input()
    session = 0
    
    bo_obj = BinaryOperations(a, d)
    input_arr = []
    result_arr = []
    while n:
        q = raw_input().split()
        if q[0]!='SUM':
            session+=1
            input_arr.append(q)
        else:
            s = session if int(q[1])==-1 else int(q[1])
            result_arr.append((s, int(q[2])))
        n-=1
    
    session_indexes = {}
    for i, (s, v) in enumerate(result_arr):
        if s not in session_indexes:
            session_indexes[s] = []
        session_indexes[s].append((i, v))
    
    session=0
    if session in session_indexes:
        for si, v in session_indexes[session]:
            result_arr[si] = bo_obj.sum(v)
            
    for q in input_arr:
        if q[0]=='ADD':
            bo_obj.add(int(q[1]), q[2], int(q[3]))
            session+=1
        elif q[0]=='UPDATE':
            bo_obj.update(int(q[1]), int(q[2]))
            session+=1
        elif q[0]=='DELETE':
            bo_obj.delete(int(q[1]))
            session+=1
        if session in session_indexes:
            for si,v in session_indexes[session]:
                result_arr[si] = bo_obj.sum(v)
                
    for x in result_arr:
        print x
    
if __name__=="__main__":
    main()