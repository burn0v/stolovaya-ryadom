"""
Почтовый backend для разработки: печатает письмо в терминал в читаемом виде (не base64 MIME).
"""

import sys
import threading

from django.core.mail.backends.base import BaseEmailBackend


class ReadableConsoleEmailBackend(BaseEmailBackend):
    """Как console.EmailBackend, но тело письма и ссылка видны сразу."""

    def __init__(self, *args, **kwargs):
        self.stream = kwargs.pop("stream", sys.stdout)
        self._lock = threading.RLock()
        super().__init__(*args, **kwargs)

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        count = 0
        with self._lock:
            try:
                for message in email_messages:
                    body = message.body or ""
                    if not body.strip():
                        for content, mimetype in getattr(message, "alternatives", []):
                            if mimetype == "text/plain":
                                body = content
                                break

                    self.stream.write("\n" + "=" * 72 + "\n")
                    self.stream.write("ПИСЬМО (dev, не отправлено по SMTP)\n")
                    self.stream.write(f"Кому: {', '.join(message.to)}\n")
                    self.stream.write(f"Тема: {message.subject}\n")
                    self.stream.write("-" * 72 + "\n")
                    self.stream.write(body)
                    if body and not body.endswith("\n"):
                        self.stream.write("\n")
                    self.stream.write("=" * 72 + "\n\n")
                    self.stream.flush()
                    count += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return count
