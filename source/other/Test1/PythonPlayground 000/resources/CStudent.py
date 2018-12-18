import os
print(os.path.abspath(__file__))

class Student:
	
	def __init__(self, name, major, gpa, is_on_probation):
		self.name 						= name
		self.major 						= major
		self.gpa 							= gpa
		self.is_on_probation 	= is_on_probation


	def on_honor_roll(self):
		return self.gpa >= 3.5