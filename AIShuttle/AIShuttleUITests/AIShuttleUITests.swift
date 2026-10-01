//
//  AIShuttleUITests.swift
//  AIShuttleUITests
//
//  Created by godwinjoel.j on 24/09/26.
//

import XCTest

final class AIShuttleUITests: XCTestCase {

    override func setUpWithError() throws {
        // Put setup code here. This method is called before the invocation of each test method in the class.

        // In UI tests it is usually best to stop immediately when a failure occurs.
        continueAfterFailure = false

        // In UI tests it’s important to set the initial state - such as interface orientation - required for your tests before they run. The setUp method is a good place to do this.
    }

    override func tearDownWithError() throws {
        // Put teardown code here. This method is called after the invocation of each test method in the class.
    }

    @MainActor
    func testHomeScreenAndNavigation() throws {
        let app = XCUIApplication()
        app.launch()

        XCTAssertTrue(app.staticTexts["AI Shuttle"].waitForExistence(timeout: 10), "AI Shuttle title should appear")

        let rideCard = app.staticTexts["Emma"]
        if rideCard.waitForExistence(timeout: 3) {
            rideCard.tap()

            let rideDetailsTitle = app.navigationBars["Ride Details"]
            XCTAssertTrue(rideDetailsTitle.waitForExistence(timeout: 5), "Navigation bar Ride Details should appear")
            XCTAssertTrue(app.staticTexts["Route Details"].exists, "Route Details section should be present")
            XCTAssertTrue(app.staticTexts["Home → School Morning Route"].exists, "Route name should match database")
            XCTAssertTrue(app.staticTexts["AI Shuttle Academy"].exists, "Destination should match database")
        } else {
            XCTAssertTrue(app.staticTexts["No upcoming rides"].waitForExistence(timeout: 5), "Empty state should appear when no rides exist")
        }
    }
}
