import base64
import json
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.db import connections
from django.db.models import Avg, F, Q, Sum
from django.db.models.functions import Coalesce
from django.forms import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.formats import number_format
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView, DetailView, FormView, TemplateView, View
from django_filters.views import FilterView
from litellm import completion

from wine_cellar.apps.storage.models import StorageItem
from wine_cellar.apps.user.views import get_user_settings
from wine_cellar.apps.wine.bodeboca import search_wines as bodeboca_search
from wine_cellar.apps.wine.fields import OpenChoiceModelFormViewMixin
from wine_cellar.apps.wine.filters import WineFilter
from wine_cellar.apps.wine.forms import (
    WineForm,
    WineUploadAIForm,
    image_fields_map,
)
from wine_cellar.apps.wine.models import (
    Category,
    Wine,
    WineImage,
    WineType,
)
from wine_cellar.apps.wine.serializers import WineAiSerializer
from wine_cellar.apps.wine.tasks import download_bodeboca_image


class HomePageView(TemplateView):
    template_name = "homepage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wines = Wine.objects.filter(user=self.request.user).count()
        wines_in_stock = (
            Wine.objects.filter(storageitem__isnull=False, storageitem__deleted=False)
            .filter(user=self.request.user)
            .distinct()
            .count()
        )
        countries = (
            Wine.objects.filter(user=self.request.user)
            .values_list("country")
            .distinct()
            .count()
        )
        oldest = "-"
        youngest = "-"
        try:
            oldest = (
                Wine.objects.filter(user=self.request.user)
                .filter(vintage__isnull=False)
                .earliest("vintage")
                .vintage
            )
            youngest = (
                Wine.objects.filter(user=self.request.user)
                .filter(vintage__isnull=False)
                .latest("vintage")
                .vintage
            )
        except Wine.DoesNotExist:
            pass
        total_value = StorageItem.objects.aggregate(
            total=Sum(
                Coalesce("price", "wine__price"),
                filter=Q(deleted=False, wine__user=self.request.user),
            )
        )["total"] or Decimal("0")
        total_value = total_value.quantize(Decimal("0"))
        user_settings = get_user_settings(self.request.user)
        currency = settings.CURRENCY_SYMBOLS.get(
            getattr(user_settings, "currency", "EUR"), "€"
        )

        formatted_price = number_format(total_value, use_l10n=True)
        total_value = f"{formatted_price}{currency}"

        context.update(
            {
                "wines": wines,
                "wines_in_stock": wines_in_stock,
                "countries": countries,
                "oldest": oldest,
                "youngest": youngest,
                "total_value": total_value,
            }
        )
        return context


class WineChooseActionView(TemplateView):
    template_name = "wine_choose_action.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ai_enabled = all(
            [getattr(settings, "AI_MODEL", None), getattr(settings, "AI_API_KEY", None)]
        )
        context.update({"ai_enabled": ai_enabled})
        if barcode := self.request.GET.get("barcode"):
            context.update({"barcode": barcode})
        return context


class WineBaseView(OpenChoiceModelFormViewMixin, FormView):
    form_class = WineForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.setdefault("user", self.request.user)
        return kwargs

    def get_wine_instance(self):
        raise NotImplementedError

    def update_wine_from_cleaned_data(self, form, wine=None):
        cleaned_data = form.cleaned_data
        user = self.request.user

        self.create_new_objects(form)

        wine_fields = [
            "abv",
            "category",
            "barcode",
            "comment",
            "country",
            "name",
            "rating",
            "vintage",
            "drink_by",
            "wine_type",
            "price",
            "location",
        ]
        for field in wine_fields:
            setattr(wine, field, cleaned_data[field])
        wine.size = cleaned_data["size"][0]
        wine.region = cleaned_data["region"][0] if cleaned_data["region"] else None
        wine.appellation = (
            cleaned_data["appellation"][0] if cleaned_data["appellation"] else None
        )
        wine.user = user
        wine.save()

        for field in ["vineyard", "grapes", "food_pairings", "attributes", "source"]:
            getattr(wine, field).set(cleaned_data[field])

        for form_field, image_type in image_fields_map.items():
            image = cleaned_data.get(form_field)
            existing = WineImage.objects.filter(
                wine=wine, user=user, image_type=image_type
            )
            if image is False or (image and not hasattr(image, "instance")):
                if existing.exists():
                    old = existing.first()
                    old.image.delete()
                    old.thumbnail.delete()
                    existing.delete()
            if image and not hasattr(image, "instance"):
                WineImage.objects.get_or_create(
                    image=image, wine=wine, user=user, image_type=image_type
                )

        bodeboca_url = cleaned_data.get("bodeboca_image_url")
        if bodeboca_url:
            wine.external_bottle_image = bodeboca_url
            wine.save()
            # Save a local copy of the bottle image (Celery); falls back to the
            # external URL if the download fails.
            download_bodeboca_image.delay(wine.id, bodeboca_url, user.id)

        return wine


class WineCreateView(WineBaseView):
    template_name = "wine_create.html"
    success_url = reverse_lazy("wine-list")

    def get_initial(self):
        initial = super().get_initial()
        if barcode := self.request.GET.get("barcode"):
            initial["barcode"] = barcode
        if b64 := self.request.GET.get("ai_initial"):
            initial.update(WineAiSerializer().deserialize_ai_payload(b64))
        return initial

    def get_wine_instance(self):
        return Wine()

    def form_valid(self, form):
        form_step = form.cleaned_data.get("form_step", 5)

        if form_step is None:
            form_step = 5
        if form_step == 5 or "save_finish" in self.request.POST:
            self.update_wine_from_cleaned_data(form=form, wine=self.get_wine_instance())
            return super().form_valid(form)
        elif form_step < 5:
            form.data = form.data.copy()
            if "back" in self.request.POST:
                form.data["form_step"] = max(0, form.cleaned_data["form_step"] - 1)
            else:
                form.data["form_step"] = form.cleaned_data["form_step"] + 1
            return super().form_invalid(form)
        return super().form_invalid(form)


class WineUpdateView(WineBaseView):
    template_name = "wine_edit.html"

    def get_initial(self):
        wine = get_object_or_404(Wine, pk=self.kwargs["pk"], user=self.request.user)
        return {**super().get_initial(), **model_to_dict(wine)}

    def get_wine_instance(self):
        return get_object_or_404(Wine, pk=self.kwargs["pk"], user=self.request.user)

    def form_valid(self, form):
        wine = self.get_wine_instance()
        self.update_wine_from_cleaned_data(form=form, wine=wine)
        self.success_url = reverse_lazy("wine-detail", kwargs={"pk": wine.pk})
        return super().form_valid(form)


class WineDetailView(DetailView):
    template_name = "wine_detail.html"
    model = Wine

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)


class WineListView(FilterView):
    model = Wine
    template_name = "wine_list.html"
    context_object_name = "wines"
    filterset_class = WineFilter
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset().order_by("-created")
        qs = qs.annotate(
            effective_price=Coalesce(
                Avg("storageitem__price"),
                F("price"),
            )
        )
        return qs.filter(user=self.request.user)


class WineScanView(TemplateView):
    template_name = "wine_scan.html"


class WineScannedView(TemplateView):
    template_name = "wine_scanned.html"

    def dispatch(self, request, *args, **kwargs):
        barcode = self.kwargs["barcode"]
        wine = (
            Wine.objects.filter(barcode=barcode).filter(user=self.request.user).first()
        )
        if wine:
            return redirect(reverse("wine-detail", kwargs={"pk": wine.pk}))

        return super().dispatch(request, *args, **kwargs)


class WineDeleteView(DeleteView):
    model = Wine
    template_name = "wine_confirm_delete.html"
    success_url = reverse_lazy("wine-list")

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)


class WineMapView(TemplateView):
    template_name = "wine_map.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wines = Wine.objects.filter(user=self.request.user)

        context.update(
            {
                "wines": wines,
            }
        )
        return context


class WineUploadAIView(FormView):
    template_name = "wine_upload_ai.html"
    form_class = WineUploadAIForm
    success_url = reverse_lazy("wine-list")

    wine_types = ", ".join([choice.label.lower() for choice in WineType])
    sweetness_categories = ", ".join([choice.label.lower() for choice in Category])

    MODEL_INSTRUCTIONS = f"""
    You are analyzing wine label images to extract structured data.
    The FIRST image is the FRONT label (mandatory). The SECOND image, if provided, is the BACK label.

    Use the FRONT label for: wine name, producer, vintage, type, region, appellation, grapes, alcohol, bottle size, country.
    Use the BACK label for: tasting notes or description (→ comment), food pairings, and any additional details.

    Return ONLY a JSON object with these fields:
    name: wine name
    country: ISO2 country code
    type: one of {wine_types}
    size: bottle size in liters as float (e.g. 0.75), guess if not shown
    grapes: list of grape variety names
    vintage: harvest year as integer
    abs: alcohol percentage as float
    sweetness: one of {sweetness_categories}
    vineyard: list of producer or winery names
    region: wine region
    appellation: appellation or DOC/AOC/AOP designation
    location: "lat,long" if determinable, otherwise omit
    comment: tasting notes or description from back label, max 200 characters (omit if not available)
    food_pairings: list of food pairing suggestions from back label, e.g. ["red meat", "pasta", "aged cheese"] (omit if not available)

    Return ONLY the JSON object, no markdown formatting or code blocks.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ai_enabled = False
        if hasattr(settings, "AI_MODEL") and hasattr(settings, "AI_API_KEY"):
            if settings.AI_MODEL and settings.AI_API_KEY:
                ai_enabled = True
        context.update({"ai_enabled": ai_enabled})
        return context

    def form_valid(self, form):
        front_img = form.cleaned_data.get("front")
        back_img = form.cleaned_data.get("back")

        _supported = {"image/jpeg", "image/png", "image/gif", "image/webp"}

        def image_data_url(img):
            mime = img.content_type if img.content_type in _supported else "image/jpeg"
            b64 = base64.b64encode(img.read()).decode()
            return f"data:{mime};base64,{b64}"

        content = [{"type": "text", "text": self.MODEL_INSTRUCTIONS}]
        if front_img:
            content.append({"type": "image_url", "image_url": {"url": image_data_url(front_img)}})

        if back_img:
            content.append({"type": "image_url", "image_url": {"url": image_data_url(back_img)}})

        try:
            response = completion(
                model=settings.AI_MODEL,
                messages=[{"role": "user", "content": content}],
                api_key=settings.AI_API_KEY,
            )
        except Exception as e:
            form.add_error(
                None,
                _("AI service error: %(error)s. Please try again.") % {"error": str(e)[:200]},
            )
            return self.form_invalid(form)
        ai_text = response.choices[0].message.content.strip()

        try:
            if ai_text.startswith("```"):
                ai_text = ai_text.split("```")[1]
            if ai_text.startswith("json"):
                ai_text = ai_text[4:]

            ai_json = json.loads(ai_text)
        except json.JSONDecodeError:
            form.add_error(
                None,
                _(
                    "Failed to process AI response. "
                    "Please check the uploaded images and try again."
                ),
            )
            return self.form_invalid(form)

        b64_initial = WineAiSerializer().serialize_ai_payload(ai_json)
        create_url = reverse("wine-add") + f"?ai_initial={b64_initial}"
        if barcode := self.request.GET.get("barcode"):
            create_url += f"&barcode={barcode}"
        return redirect(create_url)


class BodebocaSearchView(View):
    def get(self, request):
        query = request.GET.get("q", "").strip()
        vintage = request.GET.get("vintage", "").strip() or None
        if not query:
            return JsonResponse({"results": []})
        try:
            results = bodeboca_search(query, vintage=vintage)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        return JsonResponse({"results": results})


@login_not_required
def health_check(request):
    db_ok = all(conn.cursor().execute("SELECT 1") for conn in connections.all())
    status_code = 200 if db_ok else 503
    return JsonResponse({"status": "ok" if db_ok else "unhealthy"}, status=status_code)
