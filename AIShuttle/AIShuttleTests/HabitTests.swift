//
//  HabitTests.swift
//  AIShuttleTests
//
//  F10 learned habits: decoding, the reminder schedule and wording, and
//  how a booking confirmation explains a learned usual.
//

import Foundation
import Testing
import UserNotifications
@testable import AIShuttle

@MainActor
struct HabitTests {
    static let habitsJSON = """
    {
      "pinned_shuttle_id": null,
      "days": [
        {"weekday": "Monday", "shuttle_id": 2, "departure": "07:15:00", "arrival": "08:00:00",
         "source": "weekday", "reason": "you took it on 4 of your last 5 Mondays",
         "rides": 4, "sample": 5, "regular": true},
        {"weekday": "Wednesday", "shuttle_id": 3, "departure": "07:30:00", "arrival": "08:15:00",
         "source": "default", "reason": "it's your saved usual shuttle",
         "rides": 0, "sample": 0, "regular": false}
      ],
      "upcoming": [
        {"date": "2026-11-03", "weekday": "Tuesday", "booked": true, "booked_departure": "07:30:00",
         "habit": {"weekday": "Tuesday", "shuttle_id": 3, "departure": "07:30:00", "arrival": "08:15:00",
                   "source": "weekday", "reason": "you took it on each of your last 5 Tuesdays",
                   "rides": 5, "sample": 5, "regular": true}},
        {"date": "2026-11-04", "weekday": "Wednesday", "booked": false, "booked_departure": null,
         "habit": {"weekday": "Wednesday", "shuttle_id": 3, "departure": "07:30:00", "arrival": "08:15:00",
                   "source": "default", "reason": "it's your saved usual shuttle",
                   "rides": 0, "sample": 0, "regular": false}},
        {"date": "2026-11-09", "weekday": "Monday", "booked": false, "booked_departure": null,
         "habit": {"weekday": "Monday", "shuttle_id": 2, "departure": "07:15:00", "arrival": "08:00:00",
                   "source": "weekday", "reason": "you took it on 4 of your last 5 Mondays",
                   "rides": 4, "sample": 5, "regular": true}}
      ]
    }
    """

    private func habits() throws -> HabitsDTO {
        try JSONDecoder().decode(HabitsDTO.self, from: Data(Self.habitsJSON.utf8))
    }

    @Test func decodesHabitsAndFormatsTimes() throws {
        let habits = try habits()

        #expect(habits.days.first?.source == .weekday)
        #expect(habits.days.first?.formattedDeparture == "7:15 AM")
        #expect(habits.days.first?.isLearned == true)
        #expect(habits.days.last?.isLearned == false)
    }

    @Test func nextUnbookedSkipsBookedAndIrregularDays() throws {
        // Tuesday is booked; Wednesday isn't a riding day.
        #expect(try habits().nextUnbooked?.weekday == "Monday")
    }

    @Test func reminderFiresTheEveningBefore() throws {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(identifier: "Asia/Kolkata")!
        let monday = calendar.date(from: DateComponents(year: 2026, month: 11, day: 9))!

        let fire = try #require(HabitReminders.reminderDate(before: monday, calendar: calendar))

        let parts = calendar.dateComponents([.year, .month, .day, .hour, .minute], from: fire)
        #expect(parts == DateComponents(year: 2026, month: 11, day: 8, hour: 19, minute: 0))
    }

    @Test func reminderExplainsTheHabitAndOffersBook() throws {
        let monday = try #require(try habits().nextUnbooked)

        let content = HabitReminders.content(for: monday)

        #expect(content.title == "Book Monday's shuttle?")
        #expect(content.body == "Your usual Monday shuttle is the 7:15 AM, arriving 8:00 AM — "
            + "you took it on 4 of your last 5 Mondays. You haven't booked it yet.")
        #expect(content.categoryIdentifier == HabitReminders.category)
        #expect(content.userInfo[HabitReminders.dayKey] as? String == "2026-11-09")
    }

    @Test func reminderIdentifierIsPerDay() throws {
        let day = try #require(BookingAPIClient.parseISODay("2026-11-09"))
        #expect(HabitReminderID.forDay(day) == "habit-reminder-2026-11-09")
    }

    @Test func bookingDayFromDate() throws {
        let monday = try #require(BookingAPIClient.parseISODay("2026-11-09"))
        let saturday = try #require(BookingAPIClient.parseISODay("2026-11-07"))

        #expect(BookingDay(weekdayOf: monday) == .monday)
        #expect(BookingDay(weekdayOf: saturday) == .saturday)
    }

    @Test func confirmationExplainsALearnedUsual() throws {
        let json = """
        {"booking_id": 7, "message": "Done.", "already_booked": false,
         "usual_reason": "you took it on 4 of your last 5 Mondays",
         "booking": {"id": 7, "booking_date": "2099-11-09", "pickup_time": "07:15:00",
                     "arrival_time": "08:00:00", "status": "confirmed",
                     "shuttle_name": "Morning Shuttle B", "route_name": "Home → Office",
                     "pickup_location": "Home", "destination": "Office"}}
        """
        let response = try JSONDecoder().decode(BookingResponse.self, from: Data(json.utf8))

        #expect(response.spokenConfirmation.hasSuffix(
            "arriving at Office by 8:00 AM. That's your usual: you took it on 4 of your last 5 Mondays."
        ))
    }

    @Test func confirmationWithoutReasonIsUnchanged() {
        let response = BookingResponse(bookingId: 1, message: "Booked.")
        #expect(response.usualReason == nil)
        #expect(response.spokenConfirmation == "Booked.")
    }

    @Test func pinRequestSendsNullToUnpin() throws {
        let data = try JSONEncoder().encode(PinUsualRequest(userId: 1, shuttleId: nil))
        let object = try JSONSerialization.jsonObject(with: data) as? [String: Any]

        #expect(object?["user_id"] as? Int == 1)
        #expect(object?["shuttle_id"] is NSNull)
    }
}
