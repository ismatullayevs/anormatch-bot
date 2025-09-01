from enum import Enum


class FileTypes(str, Enum):
    """File types supported by the bot."""

    image = "image"
    video = "video"
    audio = "audio"
    document = "document"
    other = "other"


class UILanguages(str, Enum):
    """Supported UI languages for the bot."""

    uz = "uz"
    ru = "ru"
    en = "en"


class Genders(str, Enum):
    """User gender options."""

    male = "male"
    female = "female"


class PreferredGenders(str, Enum):
    """Preferred gender options for matching."""

    male = "male"
    female = "female"
    both = "both"


class ReactionType(str, Enum):
    """Types of reactions users can give."""

    like = "like"
    dislike = "dislike"


class ReportStatusTypes(str, Enum):
    """Report status types for user reports."""

    pending = "pending"
    reviewing = "reviewing"
    pending_info = "pending_info"
    valid = "valid"
    invalid = "invalid"
    resolved = "resolved"
    closed = "closed"
