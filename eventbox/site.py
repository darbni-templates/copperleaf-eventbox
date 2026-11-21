"""What every page shows about EventBox itself. create_app gives templates `site`."""

SITE = {
    "brand": "EventBox",
    "support_email": "help@eventbox.example",
}


def template_values():
    return {"site": SITE}
