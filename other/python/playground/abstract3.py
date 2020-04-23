class Base:
    def __init__(self):
        super().__init__()
        print("Base")

class Base1(Base):
    def __init__(self):
        Base.__init__(self)
        print("Base1")

class Base2(Base):
    def __init__(self):
        Base.__init__(self)
        print("Base2")

class Child(Base2, Base1):
    pass

t = Child()



"""
NewClass = type("NewClass", (), { 'test': lambda self: print("hi"), })
t = NewClass()
t.test()
"""

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