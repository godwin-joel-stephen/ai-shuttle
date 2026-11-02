"""Start a live trip for the demo.

Books the usual shuttle for the next service day if needed, then replays
that trip now so tracking, the Live Activity and Siri show a moving shuttle.

The defaults are tuned for the demo: a 4-minute walk at 2x speed, starting
11 simulated minutes before pickup, so "Time to leave" (pickup minus walk
minus the 5-minute buffer) arrives about 1 minute after trip mode starts.

    python -m scripts.demo_trip                  # demo defaults (see above)
    python -m scripts.demo_trip --speed 1        # real-time pace
    python -m scripts.demo_trip --walk 0         # use the phone's GPS instead
    python -m scripts.demo_trip --delay 20       # make the running trip late
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
    parser.add_argument("--speed", type=float, default=2.0)
    parser.add_argument("--start", type=float, default=-11, help="minutes from departure")
    parser.add_argument(
        "--walk",
        type=int,
        default=4,
        help="walk to the stop in minutes; 0 uses the phone's GPS position",
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
                USER_ID, booking.id, args.start, args.speed, walk_minutes=args.walk or None
            )

        print(f"Booking {booking.id} ({booking.booking_date:%A}): {status.message}")


if __name__ == "__main__":
    main()
