"""
class Test:

    def __init__(self):
        self.value = 1

class TChild(Test):
    def __init__(self):
        Test.__init__(self)
        self.myvalue = 500
        pass

t = TChild()
print(t.myvalue)
print(t.value)
"""

class Object:
    def __init__(self):
        self.value = 0

    def printValue(self):
        print(self.value)

    def reset(self):
        self.value = self.privateValue

class Mother(Object):

    def __init__(self):
        self.value = 1
        self.privateValue = 10

class Father(Object):

    def __init__(self, value):
        self.value = 2
        self.privateValue = 20

class Child(Father, Mother):
    pass

c = Child()
c.printValue()
c.reset()
c.printValue()
"""
class Base:

    def method(self):
        raise NotImplementedError

class Child1(Base):

    def method(self):
        print("child1")

class Child2(Base, Child1):

    def method(self):
        print("child2")
lst = [Child1(), Child2(), Base()]

for obj in lst:
    obj.method()

"""