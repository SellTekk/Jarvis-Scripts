# Simple calculator (seed)
def add(a,b): return a+b
def sub(a,b): return a-b
def mul(a,b): return a*b
def div(a,b):
    if b==0: raise ZeroDivisionError('division by zero')
    return a/b

def main():
    print('Calculator seed. Improve me!')

if __name__ == '__main__':
    main()
