class BookingError(ValueError):
    """Base class for booking failures that can be explained to the user.

    `code` is a stable identifier the agent uses to look up the matching
    policy; the message is user-facing text.
    """

    code = "booking_error"


class NotFoundError(BookingError):
    """A user, preference, shuttle or booking does not exist."""

    code = "not_found"


class InvalidBookingDateError(BookingError):
    """The requested booking date cannot be booked."""

    code = "invalid_date"


class DatePassedError(InvalidBookingDateError):
    code = "date_passed"


class NoServiceDayError(InvalidBookingDateError):
    code = "no_service_day"


class OutsideBookingWindowError(InvalidBookingDateError):
    code = "outside_booking_window"


class BookingCutoffPassedError(InvalidBookingDateError):
    code = "booking_cutoff_passed"


class ShuttleUnavailableError(BookingError):
    """The requested shuttle has no seat or no alternative exists."""

    code = "shuttle_unavailable"
