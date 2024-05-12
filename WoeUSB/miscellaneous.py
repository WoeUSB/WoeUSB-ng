import gettext
import locale
import os

__version__ = "0.2.12"

locale_dir = os.path.join(os.path.dirname(__file__), "locale")
translation = gettext.translation("woeusb", localedir=locale_dir, languages=[locale.getlocale()[0]], fallback=True)
translation.install()
i18n = translation.gettext
