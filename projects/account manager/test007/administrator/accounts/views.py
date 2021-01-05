from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from .models import Token, Identifier
from django.db import models
from django.db.models import F, When, Case
from django.contrib.auth.models import User
from django.urls import reverse
import datetime
import string 
import random 

from django.db import IntegrityError


# Create your views here.
@login_required
def profile(request):
	return render(request, 'accounts/profile.html', {
		'tokens': Token.objects.filter(user=request.user).order_by('-issued')[:5],
		'identifiers': Identifier.objects.filter(user=request.user)
	})



def insertEntity(entity, primaryKey):
	while True:
		try:
			entity.save()
			return entity
		except IntegrityError as e: 
			if 'UNIQUE constraint' in e.message and ("."+primaryKey) in e.message:
				pass
			raise
		except:
			raise

@login_required
def generateToken(request):
	Token(user=request.user).save()
	return HttpResponseRedirect(reverse('accounts:profile'))

@login_required
def deleteTokens(request):
	Token.objects.filter(user=request.user).delete()
	return HttpResponseRedirect(reverse('accounts:profile'))

@login_required
def generateIdentifier(request):
	insertEntity(Identifier(user=request.user), "id")
	return HttpResponseRedirect(reverse('accounts:profile'))





