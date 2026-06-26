from datetime import timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from wine_cellar.apps.wine.emails import (
    send_drink_by_reminder,
    send_opened_bottle_reminder,
)
from wine_cellar.apps.wine.models import ImageType, Wine, WineImage


@shared_task(name="drink_by_reminder")
def drink_by_reminder():
    User = get_user_model()
    users = (
        User.objects.exclude(email__isnull=True)
        .exclude(email__exact="")
        .exclude(user_settings__notifications=False)
    )
    date = timezone.now().date() + timedelta(days=14)
    for user in users:
        wines = Wine.objects.filter(
            user=user, drink_by=date, storageitem__isnull=False
        ).distinct()
        if wines.count() > 0:
            send_drink_by_reminder(user, wines)


@shared_task(name="opened_bottle_reminder")
def opened_bottle_reminder():
    from wine_cellar.apps.storage.models import StorageItem

    User = get_user_model()
    users = (
        User.objects.exclude(email__isnull=True)
        .exclude(email__exact="")
        .exclude(user_settings__notifications=False)
    )
    today = timezone.now().date()
    for user in users:
        items = StorageItem.objects.filter(
            user=user, opened=True, deleted=False, drink_by=today
        )
        if items.exists():
            send_opened_bottle_reminder(user, items)


@shared_task(name="download_bodeboca_image")
def download_bodeboca_image(wine_id, image_url, user_id):
    """Download a Bodeboca product image server-side and store it as a local
    WineImage, so display no longer depends on the (Cloudflare-protected)
    hotlink.

    Bodeboca 403s plain server-side requests; curl_cffi replays a real
    browser's TLS fingerprint so the download succeeds (the server shares the
    home public IP Cloudflare already trusts). On any failure we leave
    ``external_bottle_image`` in place as a fallback, so adding wines never
    breaks.
    """
    from curl_cffi import requests as curl_requests
    from django.core.files.base import ContentFile

    try:
        wine = Wine.objects.get(pk=wine_id)
    except Wine.DoesNotExist:
        return

    # Never clobber an existing front image (e.g. a manual upload).
    if WineImage.objects.filter(wine=wine, image_type=ImageType.FRONT).exists():
        return

    try:
        resp = curl_requests.get(image_url, impersonate="chrome", timeout=20)
        resp.raise_for_status()
    except Exception:
        return  # fallback: keep the external URL

    content_type = resp.headers.get("content-type", "")
    if not content_type.startswith("image/"):
        return

    ext = content_type.split(";")[0].rsplit("/", 1)[-1].lower()
    ext = {"jpeg": "jpg", "svg+xml": "svg"}.get(ext, ext)

    WineImage.objects.create(
        wine=wine,
        user_id=user_id,
        image_type=ImageType.FRONT,
        image=ContentFile(resp.content, name=f"bodeboca_{wine_id}.{ext}"),
    )
