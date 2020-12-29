import gettext
import locale
import os

translation = gettext.translation("woeusb", os.path.dirname(__file__) + "/locale", [locale.getlocale()[0]], fallback=True)
translation.install()
i18n = translation.gettext
