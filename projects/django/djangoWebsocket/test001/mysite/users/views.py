from django.views.generic.base import TemplateView
from django.shortcuts import render

# Create your views here.

class IndexView(TemplateView):
    template_name = "index.html"

async def websocket_view(socket):
    await socket.accept()
    await socket.send_text('hello')
    await socket.close()
