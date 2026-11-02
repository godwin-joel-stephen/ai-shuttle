"""Start a live trip for the demo.

Books the usual shuttle for the next service day if needed, then replays
that trip now so tracking, the Live Activity and Siri show a moving shuttle.

    python -m scripts.demo_trip                  # shuttle 12 min away, real time
    python -m scripts.demo_trip --speed 4        # 4x faster
    python -m scripts.demo_trip --walk 4         # pretend the stop is a 4-min walk
    python -m scripts.demo_trip --delay 15       # make the running trip late
    python -m scripts.demo_trip --stop           # back to the real clock
"""

import argparse
from datetime import timedelta

from app.api.tracking import create_tracking_service
from app.core import clock
from app.db.database import SessionLocal
from app.services.booking_service import SERVICE_WEEKDAYS


USER_ID = 1


def next_service_day():
    day = clock.today() + timedelta(days=1)
    while day.weekday() not in SERVICE_WEEKDAYS:
        day += timedelta(days=1)
    return day


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--start", type=float, default=-12, help="minutes from departure")
    parser.add_argument(
        "--walk",
        type=int,
        help="walk to the stop in minutes, instead of the phone's GPS position",
    )
    parser.add_argument("--delay", type=int, help="set a delay on the running trip")
    parser.add_argument("--stop", action="store_true")
    args = parser.parse_args()

    with SessionLocal() as db:
        tracking = create_tracking_service(db)
        booking = tracking.booking_service.book_usual_shuttle(USER_ID, next_service_day()).booking

        if args.stop:
            tracking.stop_simulation(USER_ID, booking.id)
            print(f"Stopped simulating booking {booking.id}.")
            return

        if args.delay is not None:
            status = tracking.set_delay(USER_ID, booking.id, args.delay)
        else:
            status = tracking.start_simulation(
                USER_ID, booking.id, args.start, args.speed, walk_minutes=args.walk
            )

        print(f"Booking {booking.id} ({booking.booking_date:%A}): {status.message}")


if __name__ == "__main__":
    main()
