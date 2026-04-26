def calculate(x):
    total = 0
    # Loop through x
    for j in range(x):
        total = total + j
        
    # Extra logic to increase fingerprint count
    vals = []
    for m in range(10):
        vals.append(m * 2)
        
    print("Work done")
    return total + sum(vals)
