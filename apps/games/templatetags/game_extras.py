from django import template

register = template.Library()


@register.filter
def best_image(images):
    """
    Returns the URL of the best available image for a game, following priority:
    1. box_art
    2. poster
    3. hero_art
    Returns None if no image is available (template handles fallback UI).
    """
    if not images:
        return None

    for image_type in ["box_art", "poster", "hero_art"]:
        img = images.filter(image_type=image_type).first()
        if img:
            return img.url

    return None