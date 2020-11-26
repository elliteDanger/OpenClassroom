from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required


from .models import Classroom,Topic,ClassroomTeachers
from posts.models import Assignment,SubmittedAssignment,AssignmentFile, Attachment
from .forms import ClassroomCreationForm,JoinClassroomForm, PostForm, AssignmentFileForm, AssignmentCreateForm
from comments.forms import CommentCreateForm

@login_required
def home(requests):
    classrooms = requests.user.classroom_set.all()
    classroom_form = ClassroomCreationForm()
    join_classroom_form = JoinClassroomForm()
    context = {
        'classrooms' : classrooms,
        'classroom_form': classroom_form,
        'join_classroom_form':join_classroom_form
    }
    return render(requests, 'classroom/home.html', context)

@login_required
def create_classroom(request):
    if request.method == 'POST':
        print('fORM vaLID')
        form = ClassroomCreationForm(request.POST)
        if form.is_valid(): 
            name = form.cleaned_data.get('name')
            description = form.cleaned_data.get('description')
            classroom = Classroom.objects.create(name=name, description=description, created_by=request.user)
            classroom.save()
            classroom.classroom_code = classroom.name[:4] + str(classroom.id)
            classroom.save()
            topic = Topic(name = 'General' , classroom = classroom)
            topic.save()
            classroom_teachers = ClassroomTeachers(classroom = classroom, teacher=request.user)
            classroom_teachers.save()
            messages.success(request, f'Classroom {name} created !')
        else:
            messages.danger(request, f'Classroom Could not be created :(')
    return redirect('classroom:home')

@login_required
def join_classroom(request):
    if request.method == 'POST':
        print('fORM vaLID')
        form = JoinClassroomForm(request.POST)
        if form.is_valid(): 
            classroom = Classroom.objects.filter(classroom_code = form.cleaned_data.get('code')).first()
            if classroom:
                request.user.classroom_set.add(classroom)
                messages.success(request, f'You are added in {classroom.name}')
            else:
                messages.success(request, f'Error adding you to the classroom')
        else:
            messages.success(request, f'Error adding you to the classroom')
    return redirect('classroom:home')

@login_required
def open_classroom(requests,pk):
    classroom = get_object_or_404(Classroom,pk = pk)
    topics = classroom.topic_set.all()
    contents = []
    for topic in topics:
        contents.extend(list(topic.post_set.all()))
        contents.extend(list(topic.assignment_set.all()))
    
    contents.sort(key = lambda x: x.created_at)

    post_form = PostForm()
    comment_form = CommentCreateForm()

    context = {
        'title' : 'Classroom',
        'classroom' : classroom,
        'contents': reversed(contents),
        'post_form': post_form,
        'comment_form': comment_form,
    }

    return render(requests, 'classroom/classroom.html', context)

@login_required
def delete_classroom(requests):
    context = {
        'title' : 'Classroom',
    }
    return render(requests, 'base.html', context)


@login_required
def members(request, pk):
    classroom = get_object_or_404(Classroom, pk=pk)
    context = {
        'teachers': classroom.classroomteachers_set.all(),
        'students': classroom.users.all(),
    }
    return render(request, 'classroom/members.html', context)

@login_required
def assignment_create(request):
    if request.method == 'POST':
        form = AssignmentCreateForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            topic = get_object_or_404(Topic, pk=int(form.cleaned_data['topics']))
            assignment = Assignment(
                title = form.cleaned_data['title'],
                description = form.cleaned_data['description'],
                created_by = request.user,
                topic = topic,
                due_date = form.cleaned_data['due_date']
            )
            assignment.save()
            files = request.FILES.getlist('file_field')
            for f in files:
                Attachment.objects.create(assignment = assignment,files=f)
            return redirect('classroom:open_classroom', topic.classroom.pk)

    else:
        form = AssignmentCreateForm(request.user)
    context = {'form':form}
    return render(request, 'classroom/assignment_create.html', context)


@login_required
def assignment_submit(request, pk):
    if request.method=='POST':
        print('here 1')
        assignment = get_object_or_404(Assignment,pk=pk)
        submitted_assignment = assignment.submittedassignment_set.filter(user = request.user).first()
        if not submitted_assignment:
            submitted_assignment = SubmittedAssignment.objects.create(assignment = assignment, user = request.user)
        files = request.FILES.getlist('file_field')
        print(files)
        for f in files:
            AssignmentFile.objects.create(submitted_assignment = submitted_assignment,files=f)
    
    form = AssignmentFileForm()
    assignment = get_object_or_404(Assignment, pk=pk)
    submit_assignment = assignment.submittedassignment_set.filter(user=request.user)
    if submit_assignment:
        submit_assignment = submit_assignment.first()
        assignment_files = submit_assignment.assignmentfile_set.all()
    else: assignment_files = None


    context = {
        'assignment': assignment,
        'attachments': assignment.attachment_set.all(),
        'submitted_assignment': submit_assignment,
        'assignment_files': assignment_files,
        'form':form
    }
    return render(request, 'classroom/assignment_submit.html', context)

@login_required
def turnin(request,pk):
    if request.method == 'POST':
        assignment = get_object_or_404(Assignment,pk=pk)
        submitted_assignment = assignment.submittedassignment_set.filter(user = request.user).first()
        if not submitted_assignment:
            submitted_assignment = SubmittedAssignment.objects.create(assignment = assignment, user = request.user)
        submitted_assignment.turned_in = True 
        submitted_assignment.save()
        
    return redirect('classroom:assignment_submit', pk)

@login_required
def unsubmit(request,pk):
    if request.method == 'POST':
        assignment = get_object_or_404(Assignment,pk=pk)
        submitted_assignment = assignment.submittedassignment_set.filter(user = request.user).first()
        submitted_assignment.turned_in = False  
        submitted_assignment.save()
        
    return redirect('classroom:assignment_submit', pk)

@login_required
def unsubmit_file(request, pk):
    if request.method == 'POST':
        assignment_file = get_object_or_404(AssignmentFile, pk=pk)
        assignment_pk = assignment_file.submitted_assignment.assignment.pk
        if assignment_file.submitted_assignment.user == request.user:
            if assignment_file.submitted_assignment.turned_in:
                submitted_assignment = assignment_file.submitted_assignment
                submitted_assignment.turned_in = False  
                submitted_assignment.save()
            assignment_file.delete()
        return redirect('classroom:assignment_submit', assignment_pk)

@login_required
def todo(request):
    classrooms = request.user.classroom_set.all()
    topics = []
    for classroom in classrooms:
        topics.extend(list(classroom.topic_set.all()))
    assignments = []
    for topic in topics:
        assignments.extend(list(topic.assignment_set.all()))
    context = {'assignments':assignments}
    print(assignments)
    return render(request, 'classroom/todo.html', context)

@login_required
def whiteboard(request):
    context = {}
    return render(request, 'classroom/whiteboard.html', context)