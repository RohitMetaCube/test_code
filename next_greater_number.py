def effient_sort(input_number_string):
    a = [0 for _ in range(10)]
    for i in input_number_string:
        a[int(i)]+=1
    output_number_string = ''
    for k, v in enumerate(a):
        if v:
            output_number_string += str(k)*v
    return output_number_string

def get_next_number(input_number_string):
    i = len(input_number_string)
    l =  i -1
    while l>0 and input_number_string[l] <= input_number_string[l-1]:
        l-=1
    if l:
        left_string = input_number_string[:l]
        right_string = input_number_string[l:][::-1]
        for j, x in enumerate(right_string):
            if x>input_number_string[l-1]:
                right_string = right_string[:j] + input_number_string[l-1] + right_string[j+1:]
                left_string = input_number_string[:l-1] + x
                break
        result = left_string + right_string
    else:
        result = input_number_string 
    return result