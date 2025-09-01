import logging
from uuid import UUID

import httpx
from aiogram.utils.i18n import gettext as _

from app.http_client import get_http_client_manager
from app.schemas.report import ReportSchema

logger = logging.getLogger(__name__)


async def create_report(
    user_telegram_id: int,
    to_user_id: UUID,
    reason: str,
) -> ReportSchema:
    """Create a new report with privacy-focused logging.

    Args:
        user_telegram_id: Telegram ID of the user making the report
        to_user_id: UUID of the user being reported
        reason: Reason for the report

    Returns:
        ReportSchema: Created report data

    Raises:
        ValueError: If report creation fails or validation error

    """
    try:
        # Validate reason before sending
        if not reason or not reason.strip():
            raise ValueError(_("Report reason cannot be empty"))

        if len(reason.strip()) > 500:  # Reasonable limit
            raise ValueError(
                _("Report reason is too long. Maximum 500 characters."),
            )

        http_client = get_http_client_manager()
        response = await http_client.post(
            "/v1/reports",
            telegram_user_id=user_telegram_id,
            json={
                "reason": reason.strip(),
                "to_user_id": str(to_user_id),
            },
        )
        report = ReportSchema.model_validate(response.json())

        # Privacy-focused logging - don't log user IDs or report content
        logger.info("Report created successfully")
        return report

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            logger.warning("Invalid report data provided")
            raise ValueError(_("Invalid report data. Please check your input."))
        if e.response.status_code == 401:
            logger.warning("Authentication failed for report creation")
            raise ValueError(_("Authentication failed. Please try again."))
        if e.response.status_code == 403:
            logger.warning("Access forbidden for report creation")
            raise ValueError(_("You don't have permission to create reports."))
        if e.response.status_code == 404:
            logger.warning("Target user not found for report")
            raise ValueError(_("User not found. They may have been removed."))
        if e.response.status_code == 409:
            logger.info("Duplicate report attempt")
            raise ValueError(_("You have already reported this user."))
        if e.response.status_code == 429:
            logger.warning("Rate limit exceeded for reports")
            raise ValueError(_("Too many reports. Please try again later."))

        # Privacy: Don't log sensitive information in error messages
        logger.error(f"HTTP error creating report: {e.response.status_code}")
        raise ValueError(
            _("Unable to submit your report. Please try again later."),
        )

    except httpx.RequestError:
        logger.error("Network error creating report")
        raise ValueError(_("Network error. Please check your connection."))

    except ValueError:
        # Re-raise validation errors
        raise

    except Exception as e:
        logger.error(f"Unexpected error creating report: {type(e).__name__}")
        raise ValueError(_("An unexpected error occurred. Please try again."))


async def get_user_reports(user_telegram_id: int) -> list[ReportSchema]:
    """Get reports made by the current user.

    Args:
        user_telegram_id: Telegram ID of the user

    Returns:
        list[ReportSchema]: List of reports made by the user

    Raises:
        ValueError: If API call fails

    """
    try:
        http_client = get_http_client_manager()
        response = await http_client.get(
            "/v1/reports/my",
            telegram_user_id=user_telegram_id,
        )
        reports = [ReportSchema.model_validate(report) for report in response.json()]

        logger.debug(f"Retrieved {len(reports)} reports for user")
        return reports

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            logger.warning("Authentication failed for report retrieval")
            raise ValueError(_("Authentication failed. Please try again."))
        if e.response.status_code == 403:
            logger.warning("Access forbidden for report retrieval")
            raise ValueError(_("Access denied."))
        if e.response.status_code == 404:
            logger.info("No reports found for user")
            return []

        logger.error(f"HTTP error retrieving reports: {e.response.status_code}")
        raise ValueError(
            _("Unable to retrieve your reports. Please try again later."),
        )

    except httpx.RequestError:
        logger.error("Network error retrieving reports")
        raise ValueError(_("Network error. Please check your connection."))

    except Exception as e:
        logger.error(f"Unexpected error retrieving reports: {type(e).__name__}")
        raise ValueError(_("An unexpected error occurred. Please try again."))


def validate_report_reason(reason: str) -> bool:
    """Validate report reason without logging sensitive content.

    Args:
        reason: Report reason to validate

    Returns:
        bool: True if valid

    Raises:
        ValueError: If validation fails

    """
    if not reason or not reason.strip():
        raise ValueError(_("Report reason cannot be empty"))

    reason = reason.strip()

    if len(reason) < 10:
        raise ValueError(_("Report reason must be at least 10 characters long"))

    if len(reason) > 500:
        raise ValueError(_("Report reason is too long. Maximum 500 characters."))

    # Check for common spam patterns without logging content
    spam_indicators = ["http://", "https://", "www.", ".com", ".ru", "@"]
    if any(indicator in reason.lower() for indicator in spam_indicators):
        logger.warning("Potential spam detected in report reason")
        raise ValueError(_("Report reason contains prohibited content"))

    return True
