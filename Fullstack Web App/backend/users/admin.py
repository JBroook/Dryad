# myapp/admin.py
from django.contrib import admin
from .models import User  # Import your model

admin.site.register(User)