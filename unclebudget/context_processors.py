from .models import Settings

def theme(request):
    if not request.user.is_anonymous:
        dark_mode = Settings.objects.for_user(request.user).dark_mode
    else:
        dark_mode = True

    theme = 'dark' if dark_mode else 'light'

    return {'theme': theme}
