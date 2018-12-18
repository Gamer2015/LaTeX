from resources.CStudent import Student
from resources.Question import Question



student1 = Student('Stefan', 'Maths', 3.0, False)
student2 = Student('Stefan', 'Maths', 3.7, False)
print(student1.on_honor_roll())
print(student2.on_honor_roll())

question_prompts = [
	"What color are apples?\n(a) Red/Green\n(b) Purple\n(c) Orange\n\n",
	"What color are bananas?\n(a) Teal\n(b) Magenta\n(c) Yellow\n\n",
	"What color are strawberries?\n(a) Yellow\n(b) Red\n(c) Blue\n\n",
]

questions = [
	Question(question_prompts[0], 'a'),
	Question(question_prompts[1], 'c'),
	Question(question_prompts[2], 'b'),
]

def run_test(questions):
	score = 0
	for question in questions:
		answer = input(question.prompt)
		if answer == question.answer:
			score += 1

	print("You got " + str(score) + "/" + str(len(questions)) + " questions right")

run_test(questions)