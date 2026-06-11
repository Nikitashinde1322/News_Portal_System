from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib.auth import logout
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib import messages

from .models import News, Category, Comment, Bookmark
from .forms import NewsForm, RegisterForm

from django.db.models import Count



# =========================================================
# ROLE CHECKS
# =========================================================

def is_author(user):
    return user.groups.filter(name='Author').exists()


def is_admin(user):
    return user.groups.filter(name='Admin').exists() or user.is_superuser


def is_user(user):
    return user.groups.filter(name='User').exists()


# =========================================================
# LANDING PAGE
# =========================================================

def landing(request):
    return render(request, 'landing.html')


# =========================================================
# HOME PAGE
# =========================================================

def home(request):
    query = request.GET.get('q')
    category = request.GET.get('category')

    # ONLY APPROVED NEWS
    news_list = News.objects.filter(is_approved=True)

    # SEARCH
    if query:
        news_list = news_list.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query)
        )

    # CATEGORY FILTER
    if category:
        news_list = news_list.filter(category__name__iexact=category)

    # PAGINATION
    paginator = Paginator(news_list, 6)
    page = request.GET.get('page')
    news = paginator.get_page(page)

    categories = Category.objects.all()

    # TRENDING NEWS
    trending_news = News.objects.filter(is_approved=True).annotate(
        like_count=Count('likes')
    ).order_by('-like_count')[:5]

    # USER BOOKMARKS
    bookmarks = []

    if request.user.is_authenticated:
        bookmarks = Bookmark.objects.filter(
            user=request.user
        ).select_related('news')

    return render(request, 'home.html', {
        'news': news,
        'categories': categories,
        'trending_news': trending_news,
        'bookmarks': bookmarks
    })


# =========================================================
# REGISTER
# =========================================================

def register(request):

    if request.method == 'POST':

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            # AUTO ADD TO USER GROUP
            group = Group.objects.get(name='User')
            user.groups.add(group)

            messages.success(request, "Account created successfully!")

            return redirect('/accounts/login/')

        else:
            print(form.errors)

    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


# =========================================================
# LOGOUT
# =========================================================

def custom_logout(request):
    logout(request)
    return redirect('/')


# =========================================================
# ADD NEWS (AUTHOR ONLY)
# =========================================================

@login_required
@user_passes_test(is_author)
def add_news(request):

    if request.method == 'POST':

        form = NewsForm(request.POST, request.FILES)

        if form.is_valid():

            news = form.save(commit=False)

            news.author = request.user

            # PENDING APPROVAL
            news.is_approved = False

            news.save()

            messages.success(
                request,
                "News submitted for admin approval!"
            )

            return redirect('profile')

    else:
        form = NewsForm()

    return render(request, 'add_news.html', {'form': form})


# =========================================================
# EDIT NEWS
# =========================================================

@login_required
@user_passes_test(is_author)
def edit_news(request, id):

    news = get_object_or_404(News, id=id)

    # AUTHOR SECURITY
    if news.author != request.user:
        return HttpResponseForbidden("Not allowed")

    if request.method == 'POST':

        form = NewsForm(
            request.POST,
            request.FILES,
            instance=news
        )

        if form.is_valid():

            updated_news = form.save(commit=False)

            # REQUIRES RE-APPROVAL
            updated_news.is_approved = False

            updated_news.save()

            messages.success(
                request,
                "News updated and sent for approval!"
            )

            return redirect('profile')

    else:
        form = NewsForm(instance=news)

    return render(request, 'add_news.html', {'form': form})


# =========================================================
# DELETE NEWS
# =========================================================

@login_required
@user_passes_test(is_author)
def delete_news(request, id):

    news = get_object_or_404(News, id=id)

    if news.author != request.user:
        return HttpResponseForbidden("Not allowed")

    news.delete()

    messages.success(request, "News deleted successfully!")

    return redirect('profile')


# =========================================================
# LIKE NEWS
# =========================================================

@login_required
def like_news(request, id):

    news = get_object_or_404(News, id=id)

    if request.user in news.likes.all():
        news.likes.remove(request.user)
    else:
        news.likes.add(request.user)

    return redirect('home')


# =========================================================
# COMMENT NEWS
# =========================================================

@login_required
def add_comment(request, id):

    news = get_object_or_404(News, id=id)

    if request.method == 'POST':

        text = request.POST.get('text')

        if text:

            Comment.objects.create(
                news=news,
                user=request.user,
                text=text
            )

            messages.success(request, "Comment added!")

    return redirect('home')


# =========================================================
# BOOKMARK NEWS
# =========================================================

@login_required
def toggle_bookmark(request, id):

    news = get_object_or_404(News, id=id)

    bookmark = Bookmark.objects.filter(
        user=request.user,
        news=news
    )

    if bookmark.exists():
        bookmark.delete()
        messages.success(request, "Bookmark removed!")
    else:
        Bookmark.objects.create(
            user=request.user,
            news=news
        )
        messages.success(request, "News bookmarked!")

    return redirect('home')


# =========================================================
# PROFILE
# =========================================================

@login_required
def profile(request):

    user_news = News.objects.filter(author=request.user)

    user_bookmarks = Bookmark.objects.filter(
        user=request.user
    ).select_related('news')

    return render(request, 'profile.html', {
        'user_news': user_news,
        'user_bookmarks': user_bookmarks
    })


# =========================================================
# DASHBOARD
# =========================================================

@login_required
def dashboard(request):

    category_data = News.objects.values(
        'category__name'
    ).annotate(total=Count('id'))

    context = {
        'total_news': News.objects.count(),
        'total_users': User.objects.count(),
        'total_categories': Category.objects.count(),
        'category_data': category_data,
    }

    return render(request, 'dashboard.html', context)


# =========================================================
# ADMIN - APPROVE NEWS
# =========================================================

@login_required
@user_passes_test(is_admin)
def approve_news(request):

    approved = News.objects.filter(
        author=request.user,
        is_approved=True
    )

    return render(request,
                  'approved_news.html',
                  {'approved_news': approved})


@login_required
def pending_news(request):

    pending = News.objects.filter(
        author=request.user,
        is_approved=False
    )

    return render(request,
                  'pending_news.html',
                  {'pending_news': pending})

# =========================================================
# ADMIN - MANAGE CATEGORIES
# =========================================================

@login_required
@user_passes_test(is_admin)
def manage_categories(request):

    if request.method == 'POST':

        name = request.POST.get('name')

        if name:
            Category.objects.create(name=name)

            messages.success(
                request,
                f"Category '{name}' added!"
            )

        return redirect('manage_categories')

    categories = Category.objects.all()

    return render(
        request,
        'manage_categories.html',
        {'categories': categories}
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):

    context = {

        'total_news': News.objects.count(),

        'approved_news': News.objects.filter(
            is_approved=True
        ).count(),

        'pending_news': News.objects.filter(
            is_approved=False
        ).count(),

        'total_users': User.objects.count(),

        'total_categories': Category.objects.count(),

        'total_comments': Comment.objects.count(),

        'total_bookmarks': Bookmark.objects.count(),

        'pending_articles': News.objects.filter(
            is_approved=False
        ).select_related('author'),

        'recent_articles': News.objects.all().order_by(
            '-created_at'
        )[:10],
    }

    return render(
        request,
        'admin_dashboard.html',
        context
    )


# =========================================================
# API
# =========================================================

def news_api(request):

    query = request.GET.get('q', '')

    news = News.objects.filter(
        title__icontains=query,
        is_approved=True
    )

    data = []

    for n in news:

        data.append({
            'title': n.title,
            'content': n.content[:100],
            'image': n.image.url if n.image else ''
        })

    return JsonResponse(data, safe=False)


def role_redirect(request):

    if is_admin(request.user):
        return redirect('/admin-dashboard/')

    elif is_author(request.user):
        return redirect('/profile/')

    else:
        return redirect('/home/')
    

def trending_news_api(request):

    trending = News.objects.filter(
        is_approved=True
    ).annotate(
        total_likes=Count('likes')
    ).order_by('-total_likes')[:5]

    data = []

    for news in trending:

        data.append({

            'id': news.id,
            'title': news.title,
            'content': news.content[:150],
            'category': news.category.name,
            'author': news.author.username,
            'likes': news.likes.count(),
            'image': news.image.url if news.image else '',
            'created_at': news.created_at.strftime("%d %b %Y")

        })

    return JsonResponse(data, safe=False)

@login_required
def approved_news(request):

    approved = News.objects.filter(
        author=request.user,
        is_approved=True
    )

    return render(
        request,
        'approved_news.html',
        {'approved_news': approved}
    )