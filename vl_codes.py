from math import log2, ceil

def shannon_fano(p):

    # Sort the probabilities in decreasing order, as required in Shannon's paper.
    # 0 probabilities are neglected
    p = dict(sorted([(a,p[a]) for a in p if p[a]>0.0], key = lambda el: el[1], reverse = True))

    # get cumulative prob.
    f = [0]

    for a in p:
        f.append(f[-1]+p[a])
    
    # list is too long, remove 1.0 prob. from the end of the array
    f.pop()

    # convert list into dictionary 
    f = dict([(a,mf) for a,mf in zip(p,f)])

    # Create codeword dictionary 
    code = {} 
    
    for a in p: # for each probability

        # Compute codeword length according to Shannon-Fano formula
        length = ceil(log2(1/p[a]))

        codeword = []
        myf = f[a]
        
        # for each position in length, multiply myf by 2 and take the
        # integral part as our binary digit
        for pos in range(length):
            myf *= 2  # binary left shift 

            # if myf is larger than 1, append a 1 to the codeword,
            # if it is smaller than 1 you should append a 0
            # If it is larger than 1, also substract 1 from myf.
            if (myf > 1):
                codeword.append(1)
                myf -= 1
            else:
                codeword.append(0)
            
        code[a] = codeword # assign the codeword
        
    return code  # return the code table


def huffman(p):
    # create an xtree with all the source symbols (to be the leaves) initially orphaned
    xt = [[-1,[], a] for a in p]
    
    # label the probabilities with a "pointer" to their corresponding nodes in the tree
    # in the process, we convert the probability vector from a Python dictionary to a
    # list of tuples (so we can modify it)
    # k gives index of tree node and p[a] gives its probability
    # The zip function, zips two lists together
    p = [(k,p[a]) for k,a in zip(range(len(p)),p)]

    # the leaves are labeled according to the symbols in the probability vector.
    # label the remaining tree nodes (mainly for visualisation purposes) with numbers
    # starting at len(p)
    # nodelabel is the index of the node in xt as a string
    nodelabel = len(p)

    # this loop will gradually increase the tree and reduce the probability list.
    # It will run until there is only one probability left in the list (which probability
    # will by then be 1.0)
    while len(p) > 1:
        # sort probabilities in ascending order
        p = sorted(p, key = lambda el: el[1])

        # Append a new node to the tree xt with no parent (parent = -1),
        # no children (children = []) and label str(nodelabel)
        xt.append([-1,[],str(nodelabel)])

        # Increase the variable nodelabel by 1 for its next use
        nodelabel += 1

        # For the nodes pointed to by the smallest probabilities, assign a parent.
        xt[p[0][0]][0] = len(xt)-1
        xt[p[1][0]][0] = len(xt)-1
        
        # Assign the children of new node to be the nodes pointed to by
        # p[0] and p[1]. Note that the new node can be addressed as xt[-1]
        xt[-1][1] = [p[0][0], p[1][0]]

        # Create a new entry pointing to the new node in the list of probabilities
        # This new entry is a tuple with len(xt)-1 as its first element,
        # and the sum of the probabilities in p[0] and p[1] as its second element
        p.append((len(xt)-1, p[0][1]+p[1][1]))

        # Remove the two nodes with the smallest probability
        p.pop(0)
        p.pop(0)
        
    return(xt)



def bits2bytes(x):
    n = len(x)+3
    # n % 8 ranges from 0 to 7 so 8 -n % 8 ranges from 1 to 8 so we must mod again
    r = (8 - n % 8) % 8
    
    # represent r as a string in 3-bit binary format
    prefix = format(r, '03b')
    
    # intially x is a list of 0s and 1s so we make it into a string of 0s and 1s instead
    x = ''.join(str(a) for a in x)
    # suffix = string of 0s of length r
    suffix = '0'*r
    x = prefix + x + suffix
    x = [x[k:k+8] for k in range(0,len(x),8)]
    y = []
    for a in x:
        y.append(int(a,2))

    return y

def bytes2bits(y):

    x = [format(a, '08b') for a in y]
    r = int(x[0][0:3],2)
    x = ''.join(x)
    x = [int(a) for a in x]
    for k in range(3):
        x.pop(0)
    for k in range(r):
        x.pop()
    return x

# This requires a code table description of a variable-length code
# c is the variable length code (it follows a code table description)
def vl_encode(x, c):
    y = []
    # x is the file
    # c is the code - a dictionary - key is the character to be encoded
    # y is the encoded file - simply a list of 1s and 0s
    # loop finds the code for each character and assigns it to y
    for a in x:
        y.extend(c[a])
    return y
    # y is a list of bits

# This requires an extended tree description of a code to operates
# xt is the code (it follows an extended tree description)
def vl_decode(y, xt):
    x = []
    # store the indices of nodes with no parent i.e. roots
    root = [k for k in range(len(xt)) if xt[k][0]==-1]
    # if length of root = 0 then we have an array with no roots
    # if length of root > 1 then we have an array with multiple roots
    if len(root) != 1:
        raise NameError('Tree with no or multiple roots!')
    # if there is only one root then convert variable 'root' from list to regular variable
    root = root[0]
    # store the indexes of nodes with no children i.e. leaves
    leaves = [k for k in range(len(xt)) if len(xt[k][1]) == 0]

    n = root

    for k in y:
        
        # if length of child list () is less than the code, y
        if len(xt[n][1]) < k:
            raise NameError('Symbol exceeds alphabet size in tree node')
        # if there is no symbol at the code given (corresponding to a tree node) then raise error
        # think of a tree as extending infinitely in all possible directions - when we normally draw
        # our diagrams, the nodes with no symbols (characters) are invisible - 'Symbol not assigned in tree node'
        if xt[n][1][k] == -1:
            raise NameError('Symbol not assigned in tree node')
        n = xt[n][1][k]
        # if node has no children i.e. empty child list
        if len(xt[n][1]) == 0: # it's a leaf!
            #
            x.append(xt[n][2])
            n = root

    return x


