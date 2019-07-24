#!/user/bin/python
#-*-coding:utf-8 -*-
__author__ = 'yhx'
__data__ = '2019 06 21 10:09'
x=9
# print("\n".join("\t".join(["%s*%s=%s"%(y,x,x*y) for y in range(1, x+1)] )for x in range(1,10)))
def a():
    s=1
    return s
aaa=a()
class b:
    def __init__(self):
        self.aa=1
    a=2
c=b()
print(getattr(c,'aa'))
print(getattr(aaa,'s'))