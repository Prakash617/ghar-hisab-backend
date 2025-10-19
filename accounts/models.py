from django.db import models


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class EmailSettings(SingletonModel):
    EMAIL_BACKEND = models.CharField(
        max_length=255, default="django.core.mail.backends.smtp.EmailBackend"
    )
    EMAIL_HOST = models.CharField(max_length=255, default="smtp.gmail.com")
    EMAIL_PORT = models.PositiveIntegerField(default=587)
    EMAIL_USE_TLS = models.BooleanField(default=True)
    EMAIL_HOST_USER = models.EmailField()
    EMAIL_HOST_PASSWORD = models.CharField(max_length=255)

    def __str__(self):
        return "Email Settings"
