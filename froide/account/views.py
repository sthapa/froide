from datetime import timedelta
from urllib.parse import urlencode

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import Http404
from django.contrib import auth
from django.db import models
from django.views.generic import DetailView, FormView
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.html import format_html
from django.utils import formats, timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, RedirectView

from crossdomainmedia import CrossDomainMediaMixin

from froide.foirequest.models import FoiRequest
from froide.foirequest.services import ActivatePendingRequestService
from froide.helper.utils import render_403, get_redirect, get_redirect_url

from .forms import (
    UserLoginForm,
    PasswordResetForm,
    SignUpForm,
    SetPasswordForm,
    UserEmailConfirmationForm,
    UserChangeDetailsForm,
    UserDeleteForm,
    TermsForm,
    ProfileForm,
)
from .services import AccountService
from .utils import start_cancel_account_process, make_account_private
from .export import (
    request_export,
    ExportCrossDomainMediaAuth,
    get_export_access_token,
    get_export_access_token_by_token,
)

User = auth.get_user_model()


class AccountView(RedirectView):
    # Temporary redirect
    pattern_name = "account-requests"


class NewAccountView(TemplateView):
    template_name = "account/new.html"

    def get_context_data(self, **kwargs):
        context = super(NewAccountView, self).get_context_data(**kwargs)
        context["title"] = self.request.GET.get("title", "")
        context["email"] = self.request.GET.get("email", "")
        return context


class AccountConfirmedView(LoginRequiredMixin, TemplateView):
    template_name = "account/confirmed.html"

    def get_context_data(self, **kwargs):
        context = super(AccountConfirmedView, self).get_context_data(**kwargs)
        context["foirequest"] = self.get_foirequest()
        context["ref"] = self.request.GET.get("ref")
        return context

    def get_foirequest(self):
        request_pk = self.request.GET.get("request")
        if request_pk:
            try:
                return FoiRequest.objects.get(user=self.request.user, pk=request_pk)
            except FoiRequest.DoesNotExist:
                pass
        return None


def confirm(request, user_id, secret, request_id=None):
    if request.user.is_authenticated:
        if request.user.id != user_id:
            messages.add_message(
                request,
                messages.ERROR,
                _("You are logged in and cannot use a confirmation link."),
            )
        return redirect("account-show")
    user = get_object_or_404(User, pk=int(user_id))
    if user.is_active or (not user.is_active and user.email is None):
        return redirect("account-login")
    account_service = AccountService(user)
    result = account_service.confirm_account(secret, request_id)
    if not result:
        messages.add_message(
            request,
            messages.ERROR,
            _(
                "You can only use the confirmation link once, "
                "please login with your password."
            ),
        )
        return redirect("account-login")

    auth.login(request, user)

    params = {}

    if request.GET.get("ref"):
        params["ref"] = request.GET["ref"]

    if request_id is not None:
        req_service = ActivatePendingRequestService({"request_id": request_id})
        foirequest = req_service.process(request=request)
        if foirequest:
            params["request"] = str(foirequest.pk)
    default_url = "%s?%s" % (reverse("account-confirmed"), urlencode(params))
    return get_redirect(request, default=default_url, params=params)


def go(request, user_id, token, url):
    if request.user.is_authenticated:
        if request.user.id != int(user_id):
            messages.add_message(
                request,
                messages.INFO,
                _(
                    "You are logged in with a different user account. Please logout first before using this link."
                ),
            )
        # Delete token without using
        AccountService.delete_autologin_token(user_id, token)
        return redirect(url)

    if request.method == "POST":
        user = User.objects.filter(pk=int(user_id)).first()
        if user:
            account_manager = AccountService(user)
            if account_manager.check_autologin_token(token):
                if not user.is_active:
                    # Confirm user account (link came from email)
                    account_manager.reactivate_account()
                # Perform login
                auth.login(request, user)
                return redirect(url)

        # If login-link fails, prompt login with redirect
        return get_redirect(request, default="account-login", params={"next": url})
    return render(request, "account/go.html")


class ProfileView(DetailView):
    queryset = User.objects.filter(private=False)
    slug_field = "username"
    template_name = "account/profile.html"

    def get_context_data(self, **kwargs):
        from froide.campaign.models import Campaign
        from froide.publicbody.models import PublicBody

        ctx = super().get_context_data(**kwargs)
        ctx.pop("user", None)  # Remove 'user' key set by super

        foirequests = FoiRequest.published.filter(user=self.object)

        aggregates = foirequests.aggregate(
            count=models.Count("id"),
            first_date=models.Min("first_message"),
            successful=models.Count(
                "id",
                filter=models.Q(
                    status=FoiRequest.STATUS.RESOLVED,
                    resolution=FoiRequest.RESOLUTION.SUCCESSFUL,
                )
                | models.Q(
                    status=FoiRequest.STATUS.RESOLVED,
                    resolution=FoiRequest.RESOLUTION.PARTIALLY_SUCCESSFUL,
                ),
            ),
            refused=models.Count(
                "id",
                filter=models.Q(
                    status=FoiRequest.STATUS.RESOLVED,
                    resolution=FoiRequest.RESOLUTION.REFUSED,
                ),
            ),
            total_costs=models.Sum("costs"),
        )
        campaigns = (
            Campaign.objects.filter(
                foirequest__in=foirequests,
            )
            .exclude(url="")
            .distinct()
            .order_by("-start_date")
        )

        TOP_PUBLIC_BODIES = 3
        top_publicbodies = (
            PublicBody.objects.filter(foirequest__in=foirequests)
            .annotate(user_request_count=models.Count("id"))
            .order_by("-user_request_count")[:TOP_PUBLIC_BODIES]
        )

        TOP_FOLLOWERS = 3
        top_followers = (
            foirequests.annotate(
                follower_count=models.Count(
                    "followers", filter=models.Q(followers__confirmed=True)
                )
            )
            .filter(follower_count__gt=0)
            .order_by("-follower_count")[:TOP_FOLLOWERS]
        )
        user_days = (timezone.now() - self.object.date_joined).days

        no_index = aggregates["count"] < 5 and user_days < 30

        ctx.update(
            {
                "foirequests": foirequests.order_by("-first_message")[:10],
                "aggregates": aggregates,
                "campaigns": campaigns,
                "top_followers": top_followers,
                "top_publicbodies": top_publicbodies,
                "no_index": no_index,
            }
        )
        return ctx


@require_POST
def logout(request):
    auth.logout(request)
    messages.add_message(request, messages.INFO, _("You have been logged out."))
    return redirect("/")


def login(request, context=None, template="account/login.html", status=200):
    if request.user.is_authenticated:
        return get_redirect(request, default="account-show")

    if not context:
        context = {}
    if "reset_form" not in context:
        context["reset_form"] = PasswordResetForm(prefix="pwreset")

    if request.method == "POST" and status == 200:
        status = 400  # if ok, we are going to redirect anyways
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = auth.authenticate(
                request,
                username=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
            )
            if user is not None:
                if user.is_active:
                    auth.login(request, user)
                    messages.add_message(
                        request, messages.INFO, _("You are now logged in.")
                    )
                    return get_redirect(request, default="account-show")
                else:
                    messages.add_message(
                        request,
                        messages.ERROR,
                        _("Please activate your mail address before logging in."),
                    )
            else:
                messages.add_message(
                    request, messages.ERROR, _("E-mail and password do not match.")
                )
    else:
        form = UserLoginForm(initial=None)
    context.update({"form": form, "next": request.GET.get("next")})
    return render(request, template, context, status=status)


class SignupView(FormView):
    template_name = "account/signup.html"
    form_class = SignUpForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("account-show")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"request": self.request})
        return kwargs

    def get_success_url(self, email=""):
        next_url = self.request.POST.get("next")
        if next_url:
            # Store next in session to redirect on confirm
            self.request.session["next"] = next_url

        url = reverse("account-new")
        query = urlencode({"email": self.user.email.encode("utf-8")})
        return "%s?%s" % (url, query)

    def form_invalid(self, form):
        messages.add_message(
            self.request, messages.ERROR, _("Please correct the errors below.")
        )
        return super().form_invalid(form)

    def form_valid(self, form):
        user, user_created = AccountService.create_user(**form.cleaned_data)
        if user_created:
            form.save(user)

        self.user = user

        next_url = self.request.POST.get("next")
        account_service = AccountService(user)

        time_since_joined = timezone.now() - user.date_joined
        joined_recently = time_since_joined > timedelta(hours=1)

        mail_sent = True
        if user_created:
            account_service.send_confirmation_mail(redirect_url=next_url)
        elif user.is_active:
            # Send login-link email
            account_service.send_reminder_mail()
        elif not user.is_blocked and not joined_recently:
            # User exists, but not activated
            account_service.send_confirmation_mail()
        else:
            mail_sent = False

        if mail_sent:
            messages.add_message(
                self.request,
                messages.SUCCESS,
                _(
                    "Please check your emails for a mail from us with a "
                    "confirmation link."
                ),
            )

        return super().form_valid(form)


@require_POST
@login_required
def change_password(request):
    form = request.user.get_password_change_form(request.POST)
    if form.is_valid():
        form.save()
        auth.update_session_auth_hash(request, form.user)
        messages.add_message(
            request, messages.SUCCESS, _("Your password has been changed.")
        )
        return get_redirect(request, default=reverse("account-show"))
    else:
        messages.add_message(
            request,
            messages.ERROR,
            _("Your password was NOT changed. Please fix the errors."),
        )
    return account_settings(request, context={"password_change_form": form}, status=400)


@require_POST
def send_reset_password_link(request):
    if request.user.is_authenticated:
        messages.add_message(
            request,
            messages.ERROR,
            _("You are currently logged in, you cannot get a password reset link."),
        )
        return get_redirect(request)
    form = auth.forms.PasswordResetForm(request.POST, prefix="pwreset")
    if form.is_valid():
        if request.POST.get("next"):
            request.session["next"] = request.POST.get("next")
        form.save(
            use_https=True,
            email_template_name="account/emails/password_reset_email.txt",
        )
        messages.add_message(
            request,
            messages.SUCCESS,
            _(
                "Check your mail, we sent you a password reset link."
                " If you don't receive an email, check if you entered your"
                " email correctly or if you really have an account."
            ),
        )
        return get_redirect(request, keep_session=True)
    return login(request, context={"reset_form": form}, status=400)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "account/password_reset_confirm.html"
    post_reset_login = True
    form_class = SetPasswordForm

    def form_valid(self, form):
        messages.add_message(
            self.request,
            messages.SUCCESS,
            _("Your password has been set and you are now logged in."),
        )
        return super().form_valid(form)

    def get_success_url(self):
        """
        Returns the supplied success URL.
        """
        return get_redirect_url(self.request, default=reverse("account-show"))


@login_required
def account_settings(request, context=None, status=200):
    if not context:
        context = {}
    if "new" in request.GET:
        request.user.is_new = True
    if "user_delete_form" not in context:
        context["user_delete_form"] = UserDeleteForm(request)
    if "change_form" not in context:
        context["change_form"] = UserChangeDetailsForm(request.user)
    return render(request, "account/settings.html", context, status=status)


@require_POST
@login_required
def change_user(request):
    form = UserChangeDetailsForm(request.user, request.POST)
    if form.is_valid():
        new_email = form.cleaned_data["email"]
        if new_email and request.user.email != new_email:
            AccountService(request.user).send_email_change_mail(
                form.cleaned_data["email"]
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                _(
                    "We sent a confirmation email to your new address. Please click the link in there."
                ),
            )
        form.save()
        messages.add_message(
            request, messages.SUCCESS, _("Your profile information has been changed.")
        )
        return redirect("account-settings")
    messages.add_message(
        request,
        messages.ERROR,
        _("Please correct the errors below. You profile information was not changed."),
    )

    return account_settings(request, context={"change_form": form}, status=400)


@require_POST
@login_required
def change_profile(request):
    form = ProfileForm(data=request.POST, files=request.FILES, instance=request.user)
    if form.is_valid():
        form.save()
        messages.add_message(
            request, messages.SUCCESS, _("Your profile information has been changed.")
        )
        return redirect("account-settings")
    messages.add_message(
        request,
        messages.ERROR,
        _("Please correct the errors below. You profile information was not changed."),
    )

    return account_settings(request, context={"profile_form": form}, status=400)


@require_POST
@login_required
def make_user_private(request):
    if request.user.private:
        messages.add_message(
            request, messages.ERROR, _("Your account is already private.")
        )
        return redirect("account-settings")

    make_account_private(request.user)

    messages.add_message(
        request,
        messages.SUCCESS,
        _("Your account has been made private. The changes are being applied now."),
    )
    return redirect("account-settings")


@login_required
def change_email(request):
    form = UserEmailConfirmationForm(request.user, request.GET)
    if form.is_valid():
        form.save()
        messages.add_message(
            request, messages.SUCCESS, _("Your email address has been changed.")
        )
    else:
        messages.add_message(
            request,
            messages.ERROR,
            _("The email confirmation link was invalid or expired."),
        )
    return redirect("account-settings")


@login_required
def profile_redirect(request):
    if request.user.private or not request.user.username:
        messages.add_message(
            request,
            messages.INFO,
            _("Your account is private, so you don't have a public profile."),
        )
        return redirect("account-requests")

    return redirect("account-profile", slug=request.user.username)


@require_POST
@login_required
def delete_account(request):
    form = UserDeleteForm(request, data=request.POST)
    if not form.is_valid():
        messages.add_message(
            request,
            messages.ERROR,
            _("Password or confirmation phrase were wrong. Account was not deleted."),
        )
        return account_settings(request, context={"user_delete_form": form}, status=400)
    # Removing all personal data from account
    start_cancel_account_process(request.user)
    auth.logout(request)
    messages.add_message(
        request,
        messages.INFO,
        _("Your account has been deleted and you have been logged out."),
    )

    return redirect("/")


def new_terms(request):
    next = request.GET.get("next")
    if not request.user.is_authenticated:
        return get_redirect(request, default=next)
    if request.user.terms:
        return get_redirect(request, default=next)

    form = TermsForm()
    if request.POST:
        form = TermsForm(request.POST)
        if form.is_valid():
            form.save(request.user)
            messages.add_message(
                request, messages.SUCCESS, _("Thank you for accepting our new terms!")
            )
            return get_redirect(request, default=next)
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("You need to accept our new terms to continue."),
            )
    return render(request, "account/new_terms.html", {"terms_form": form, "next": next})


def csrf_failure(request, reason=""):
    return render_403(
        request,
        message=_(
            "You probably do not have cookies enabled, but you need cookies to "
            "use this site! Cookies are only ever sent securely. The technical "
            "reason is: %(reason)s"
        )
        % {"reason": reason},
    )


@login_required
def create_export(request):
    if request.method == "POST":
        result = request_export(request.user)
        if result is None:
            messages.add_message(
                request,
                messages.SUCCESS,
                _(
                    "Your export has been started. "
                    "You will receive an email when it is finished."
                ),
            )
        else:
            if result is True:
                messages.add_message(
                    request,
                    messages.INFO,
                    _(
                        "Your export is currently being created. "
                        "You will receive an email once it is available."
                    ),
                )
            else:
                messages.add_message(
                    request,
                    messages.INFO,
                    format_html(
                        _(
                            "Your next export will be possible at {date}. "
                            '<a href="{url}">You can download your current '
                            "export here</a>."
                        ),
                        date=formats.date_format(result, "SHORT_DATETIME_FORMAT"),
                        url=reverse("account-download_export"),
                    ),
                )

    return redirect(reverse("account-settings"))


@login_required
def download_export(request):
    access_token = get_export_access_token(request.user)
    if not access_token:
        return redirect(reverse("account-settings") + "#export")

    mauth = ExportCrossDomainMediaAuth({"object": access_token})
    return redirect(mauth.get_full_media_url(authorized=True))


class ExportFileDetailView(CrossDomainMediaMixin, DetailView):
    """
    Add the CrossDomainMediaMixin
    and set your custom media_auth_class
    """

    media_auth_class = ExportCrossDomainMediaAuth

    def get_object(self):
        access_token = get_export_access_token_by_token(self.kwargs["token"])
        if not access_token:
            raise Http404
        return access_token

    def render_to_response(self, context):
        return super().render_to_response(context)
