import math

name 	= "John"
age 	= -35
integer = 50
boolean = None

i = 0

print('test' + str(i)) 
print(pow(5,2))
print(max(5,2))
print(min(5,2))

print('test' + str(i))
print(round(5.2))
print(round(5.7))
print(round(5.5))
print('test' + str(i))
print(math.ceil(5.2))
print(math.floor(5.7))
print(math.sqrt(36))

print("Name: " + name + ", yeah!")
print("Age: " + str(abs(age)) + ", yeah!")

string = "this is a test String"
print(string.lower())
print(string.upper())
print(string.isupper())
print(string.upper().isupper())
print(string.lower().isupper())
print(string.lower().islower())
print(len(string))
print(string[20])
print(string.index('t'))
print(string.index('test'))
""" print(string.index('z')) """
print(string.replace('i', 'z'))
print(string.replace('test', 'hello world'))