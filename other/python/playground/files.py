""" 
    THIS IS MY FILE #pythonisnonconst
"""

class Const:

    def __init__(self, value):
        self.__value = value # private

    def copy(self):
        return self.__value



file = Const(open('resources/index.html', 'w'))
file.copy().write('<p>This is some HTML markup </p>')
file.copy().close()



print("test")

with Const(open('resources/employees.txt', 'r')) as EMPLOYEE_FILE:
    print(EMPLOYEE_FILE.copy().readable())
    for line in EMPLOYEE_FILE.copy().readlines():
        print(line)
