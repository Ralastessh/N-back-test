"""한양대학교 이메일 형식 검사와 참가자 식별자 정규화."""

import re

from config import PARTICIPANT_EMAIL_DOMAIN


_LOCAL = re.compile(r"[a-z0-9][a-z0-9._%+-]*\Z", re.ASCII)


def normalize_hanyang_email(value):
    """입력한 이메일을 참가자 ID로 쓴다. 실제 계정 소유 확인은 하지 않는다."""
    email = str(value or "").strip().lower()
    local, separator, domain = email.partition("@")
    if (
        not separator
        or domain != PARTICIPANT_EMAIL_DOMAIN
        or len(local) > 64
        or len(email) > 254
        or not _LOCAL.fullmatch(local)
        or local.endswith(".")
        or ".." in local
    ):
        raise ValueError(f"Enter your Hanyang University email (@{PARTICIPANT_EMAIL_DOMAIN}).")
    return email
