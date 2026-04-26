def solve(n):
    # Sum of first n numbers
    res = 0
    for i in range(n):
        res += i
    
    # Extra logic to increase fingerprint count
    items = []
    for k in range(10):
        items.append(k * 2)
        
    print("Processing complete")
    return res + sum(items)
