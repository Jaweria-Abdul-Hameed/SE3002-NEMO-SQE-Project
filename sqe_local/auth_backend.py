"""Synthetic authentication backend for local SQE testing without LDAP/Kerberos."""

import hmac
import os

from django.contrib.auth.backends import ModelBackend

from NEMO.exceptions import InactiveUserError
from NEMO.models import User
from NEMO.views.authentication import check_user_exists_and_active


class LocalSyntheticAuthBackend(ModelBackend):
    """Authenticates active NEMO users against a configurable local test password."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        expected_password = os.getenv("SQE_LOCAL_TEST_PASSWORD", "nemo-sqe-test-2026")
        if not hmac.compare_digest(str(password), str(expected_password)):
            return None
        try:
            return check_user_exists_and_active(self, username)
        except (User.DoesNotExist, InactiveUserError):
            return None
