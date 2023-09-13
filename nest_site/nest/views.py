from django.contrib.auth.views import LogoutView, PasswordChangeDoneView, \
    PasswordChangeView


class NestLogoutView(LogoutView):
    template_name = 'nest/logged_out.html'


class NestPasswordChangeView(PasswordChangeView):
    template_name = 'nest/password_change_form.html'


class NestPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'nest/password_change_done.html'
