#import asyncio
import time

def gen(num):
    for x in range(0,num):
        if x == 5:
            time.sleep(5)
        yield x




def main():
    for x in gen(10):
        print(x)

main()
