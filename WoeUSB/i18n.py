import gettext
import os

translation = gettext.translation("woeusb", os.path.dirname(__file__) + "/locale", ['pl', 'zh', 'fr'], fallback=True)
translation.install()
i18n = translation.gettext
