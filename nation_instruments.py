def solution (A, K):
    # Write your code here
    count = 0
    N = len(A)
    for row in A:
        row2 = [x for x in row[:N]]
        for j, cell in enumerate(row[:N]):
            if cell == 'P':
                mark=False
                for k, value in enumerate(row2[:j][-K:]):
                    if value=='T':
                        mark = (j - K + k) if j>K else k 
                if isinstance(mark, bool):
                    for k, value in enumerate(row2[(j+1):][:K]):
                        if value=='T':
                            mark = (j + k + 1) if (j + k + 1)<N else (N-1) 
                if not isinstance(mark, bool):
                    count+=1
                    row2[mark] = ''
                    print row, row2, mark, j, count  
    return count
                
                
                    
                
    
T = input()
for _ in xrange(T):
    N, K = map(int, raw_input().split())
    A = []
    for _ in xrange(N):
        A.append(raw_input().split())
    out_ = solution(A, K)
    print out_