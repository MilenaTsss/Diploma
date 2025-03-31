from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models

from core.constants import CHOICE_MAX_LENGTH


class AccessRequest(models.Model):
    """
    Access request between a user and a barrier.

    Tracks who requested access, from whom, and the current status.
    Only allows transitions from 'pending' to 'approved', 'rejected' or 'cancelled'.
    """

    class Meta:
        db_table = "access_request"

    class RequestType(models.TextChoices):
        FROM_USER = "from_user", "From user"
        FROM_BARRIER = "from_barrier", "From barrier"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    ALLOWED_STATUS_TRANSITIONS = {
        Status.PENDING: {Status.APPROVED, Status.REJECTED, Status.CANCELLED},
        Status.APPROVED: set(),
        Status.REJECTED: set(),
        Status.CANCELLED: set(),
    }

    user = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="access_requests",
        null=False,
        help_text="User who requests access.",
    )

    barrier = models.ForeignKey(
        "barriers.Barrier",
        on_delete=models.PROTECT,
        related_name="access_requests",
        null=False,
        help_text="Barrier to which access is requested.",
    )

    request_type = models.CharField(
        max_length=CHOICE_MAX_LENGTH,
        choices=RequestType.choices,
        null=False,
        help_text="Direction of the access request",
    )

    status = models.CharField(
        max_length=CHOICE_MAX_LENGTH,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="Current status of the access request",
    )

    hidden_for_user = models.BooleanField(default=False)
    hidden_for_admin = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=False)

    def __str__(self):
        if self.request_type == AccessRequest.RequestType.FROM_USER:
            return f"`{self.user}` -> `{self.barrier}` [{self.status}]"
        else:
            return f"`{self.barrier}` -> `{self.user}` [{self.status}]"

    def delete(self, *args, **kwargs):
        raise PermissionDenied("Deletion of this object is not allowed.")

    def clean(self):
        """Restrict invalid status transitions"""

        if not self.pk:
            return  # New object — skip check

        old = AccessRequest.objects.get(pk=self.pk)
        allowed = self.ALLOWED_STATUS_TRANSITIONS.get(old.status, set())
        if self.status != old.status and self.status not in allowed:
            raise ValidationError(f"Invalid status transition: {old.status} → {self.status}")

    def save(self, *args, **kwargs):
        self.full_clean()  # Will raise if invalid
        if self.status != self.Status.PENDING and not self.finished_at:
            from django.utils.timezone import now

            self.finished_at = now()
        super().save(*args, **kwargs)
