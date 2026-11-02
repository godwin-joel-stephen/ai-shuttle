class BookingError(ValueError):
    """Base class for booking failures that can be explained to the user."""


class NotFoundError(BookingError):
    """A user, preference, shuttle or booking does not exist."""


class InvalidBookingDateError(BookingError):
    """The requested booking date cannot be booked."""


class ShuttleUnavailableError(BookingError):
    """The requested shuttle has no seat or no alternative exists."""
