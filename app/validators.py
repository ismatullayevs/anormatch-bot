from datetime import date, datetime

from aiogram.utils.i18n import gettext as _


class Params:
    """Bot validation parameters."""

    name_min_length = 3
    name_max_length = 50

    min_age = 18
    max_age = 100

    bio_max_length = 255

    media_min_count = 1
    media_max_count = 5
    media_max_duration = 60

    message_max_length = 1000


def validate_name(value: str | None) -> str | None:
    """Validate user name input.

    Args:
        value: The name string to validate

    Returns:
        str | None: The validated name

    Raises:
        ValueError: If name is invalid

    """
    if value is None:
        return value

    if not (value and all(x.isalpha() or x.isspace() for x in value)):
        raise ValueError(_("Name must only contain letters and spaces"))

    if len(value) < Params.name_min_length:
        raise ValueError(
            _("Name must be at least {min_length} characters long").format(
                min_length=Params.name_min_length,
            ),
        )
    if len(value) > Params.name_max_length:
        raise ValueError(
            _("Name must be less than {max_length} characters long").format(
                max_length=Params.name_max_length,
            ),
        )
    return value


def validate_birth_date(value: str | None) -> datetime | None:
    """Parse a date string and validate that the person is between given age range.

    Supported formats:
    - YYYY-MM-DD (e.g., "1970-10-20")
    - DD.MM.YYYY (e.g., "20.10.1970")
    - MM/DD/YYYY (e.g., "10/20/1970")

    Args:
        value: String containing the date in one of the supported formats

    Returns:
        datetime object representing the parsed date

    Raises:
        ValueError: If the string cannot be parsed into a valid date
                   or if the age is not between given age range

    """
    if not value:
        return None

    formats = [
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%m/%d/%Y",
    ]

    parsed_date = None
    for date_format in formats:
        try:
            parsed_date = datetime.strptime(value, date_format)
            break
        except ValueError:
            continue

    if parsed_date is None:
        raise ValueError(
            _(
                "Invalid date format. Supported formats are: \n"
                "\n- YYYY-MM-DD (1970-10-20), "
                "\n- DD.MM.YYYY (20.10.1970), "
                "\n- MM/DD/YYYY (10/20/1970)",
            ),
        )

    today = date.today()
    age = (
        today.year
        - parsed_date.year
        - ((today.month, today.day) < (parsed_date.month, parsed_date.day))
    )

    if age < Params.min_age:
        raise ValueError(
            _("You must be at least {min_age} years old to use this bot").format(
                min_age=Params.min_age,
            ),
        )
    if age > Params.max_age:
        raise ValueError(
            _("You must be less than {max_age} years old to use this bot").format(
                max_age=Params.max_age,
            ),
        )

    return parsed_date


def validate_bio(value: str | None) -> str | None:
    """Validate user bio text.

    Args:
        value: The bio string to validate

    Returns:
        str | None: The validated bio

    Raises:
        ValueError: If bio is too long

    """
    if value and len(value) > Params.bio_max_length:
        raise ValueError(
            _("Bio must be less than {max_length} characters long").format(
                max_length=Params.bio_max_length,
            ),
        )
    return value


def validate_media_size[T](value: list[T]) -> list[T]:
    """Validate media list size.

    Args:
        value: List of media items to validate

    Returns:
        list[T]: The validated media list

    Raises:
        ValueError: If media count is invalid

    """
    if len(value) < Params.media_min_count:
        raise ValueError(
            _("Please upload at least {min_length} media files").format(
                min_length=Params.media_min_count,
            ),
        )
    if len(value) > Params.media_max_count:
        raise ValueError(
            _("You can upload up to {max_length} media files").format(
                max_length=Params.media_max_count,
            ),
        )
    return value


def validate_preference_age_string(value: str):
    """Validate age range string and parse it.

    Args:
        value: Age range string in format "min-max"

    Returns:
        tuple[int, int]: The validated min and max ages

    Raises:
        ValueError: If age range format is invalid

    """
    try:
        min_age, max_age = map(int, value.split("-"))
    except ValueError as e:
        raise ValueError(_("Please enter a valid age range")) from e
    min_age = validate_preference_age(min_age)
    max_age = validate_preference_age(max_age)
    min_age, max_age = validate_preference_ages(min_age, max_age)
    return min_age, max_age


def validate_preference_age(value: int | None):
    """Validate a single preference age value.

    Args:
        value: Age value to validate

    Returns:
        int | None: The validated age

    Raises:
        ValueError: If age is out of range

    """
    if value is None:
        return value
    if value < Params.min_age:
        raise ValueError(
            _("Age can't be lower than {min_age}").format(min_age=Params.min_age),
        )
    if value > Params.max_age:
        raise ValueError(
            _("Age can't be higher than {max_age}").format(max_age=Params.max_age),
        )
    return value


def validate_preference_ages(min_age: int | None, max_age: int | None):
    """Validate min/max age combination.

    Args:
        min_age: Minimum age preference
        max_age: Maximum age preference

    Returns:
        tuple[int | None, int | None]: The validated age range

    Raises:
        ValueError: If min_age >= max_age

    """
    if not min_age or not max_age:
        return (None, None)
    if min_age >= max_age:
        raise ValueError(_("Minimum age needs be to lower than maximum age"))
    return (min_age, max_age)


def validate_video_duration(value: int | None):
    """Validate video duration.

    Args:
        value: Duration in seconds

    Returns:
        int | None: The validated duration

    Raises:
        ValueError: If duration exceeds maximum

    """
    if value and value > Params.media_max_duration:
        raise ValueError(
            _("Video duration can't be longer than {max_duration} seconds").format(
                max_duration=Params.media_max_duration,
            ),
        )
    return value


def validate_message_text(value: str | None):
    """Validate message text.

    Args:
        value: Message text to validate

    Returns:
        str | None: The validated and stripped message text

    Raises:
        ValueError: If message is empty or too long

    """
    if value is None:
        return None

    if not value.strip():
        raise ValueError(_("Message text cannot be empty"))
    if len(value) > Params.message_max_length:
        raise ValueError(
            _("Message text must be less than {max_length} characters long").format(
                max_length=Params.message_max_length,
            ),
        )
    return value.strip()
