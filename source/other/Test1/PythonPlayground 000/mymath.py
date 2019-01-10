

def fequal(num1, num2, prec=0, base=10):
	diff = abs(num1 - num2);
	return round(diff * base / 10, prec) / base * 10 

def myround(x, prec=2, base=10):
	factor = base ** prec
	return round(x * factor) / factor


print(myround(53,0,10))