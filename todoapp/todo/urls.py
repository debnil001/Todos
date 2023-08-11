from django.urls import path
from . import views

urlpatterns =[
    path('',views.index,name='index'),
    path('create/',views.create_todo,name='create-todo'),
    path('todo/<id>/',views.todo_detail,name='todo-detail'),
    path('todo-delete/<id>/',views.todo_delete,name='todo-delete'),
    path('todo-edit/<id>/',views.todo_edit,name='todo-edit'),
]

handler404="helpers.views.handle_not_found"