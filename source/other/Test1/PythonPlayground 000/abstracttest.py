

class Animal:
    def __init__(self, animalType):
        self.animalType = animalType

    def getType(self):
        print(self.animalType)

    def eat(self):
        print("eat")

    def makeNoise(self):
        raise NotImplementedError

class Mammal(Animal):

    def __init__(self, animalType):
        Animal.__init__(self, animalType)
        self.animalType += ', Mammal'

    def breathe(self):
        print("breathe")

    def makeNoise(self):
        print("I am a mammal")

class WingedAnimal(Animal):

    def __init__(self, animalType):
        Animal.__init__(self, animalType)
        self.animalType += ', WingedAnimal'


    def flap(self):
        print("flap")

    def makeNoise(self):
        print("I am a WingedAnimal")

class Bat(WingedAnimal, Mammal):

    def __init__(self, animalType):
        Mammal.__init__(self, animalType)
        WingedAnimal.__init__(self, animalType)

    def shriek(self):
        print("shriek")

bat = Bat("bat")
print(bat)
bat.getType()
bat.makeNoise()
bat.eat()

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