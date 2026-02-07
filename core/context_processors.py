from .models import UserProfile

def user_profile(request):
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            return {'user_profile': profile}
        except UserProfile.DoesNotExist:
            return {'user_profile': None}
    return {}


def profile_data(request):
    default_pic = '/static/avatars/default.jpg'

    if not request.user.is_authenticated:
        return {'profile_picture': default_pic}

    try:
        profile = UserProfile.objects.get(user=request.user)
        return {
            'profile_picture': profile.profile_picture or default_pic,
            'user_profile': profile
        }
    except UserProfile.DoesNotExist:
        return {'profile_picture': default_pic}
