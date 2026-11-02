from sqlalchemy.orm import Session
from langgraph.graph import END, START, StateGraph

from app.agent.schemas import AgentIntent

from app.agent.llm import LLM, LLMUnavailableError
from app.graph.state import BookingState
from app.tools.booking_tools import create_booking_tool


def understand_request(
    state: BookingState,
    llm: LLM,
) -> BookingState:
    user_input = state.get("user_input")

    if not user_input:
        raise ValueError("user_input is required.")

    try:
        request = llm.invoke(user_input)
    except Exception as e:
        raise LLMUnavailableError(str(e)) from e

    return {
        **state,
        "intent": request.intent.value,
        "booking_date": request.booking_date,
    }


def route_entry(state: BookingState) -> str:
    # Callers such as the Siri App Intent already know the intent and
    # date, so there is no language left for the LLM to interpret.
    if state.get("intent") and state.get("booking_date"):
        return "resolve_parameters"

    return "understand_request"


def resolve_parameters(state: BookingState) -> BookingState:
    if "user_id" not in state:
        raise ValueError("user_id is required.")

    if "booking_date" not in state:
        raise ValueError("booking_date is required.")

    if state.get("intent") != AgentIntent.BOOK_USUAL_SHUTTLE:
        raise ValueError(f"Unsupported intent: {state.get('intent')}.")

    return state


def execute_booking(
    state: BookingState,
    book_shuttle,
) -> BookingState:
    outcome = book_shuttle.invoke(
        {
            "user_id": state["user_id"],
            "booking_date": state["booking_date"],
        }
    )

    return {
        **state,
        "booking_id": outcome.booking.id,
        "booking": outcome.booking,
        "already_booked": outcome.already_booked,
    }


def validate_result(state: BookingState) -> BookingState:
    booking_id = state.get("booking_id")

    if booking_id is None:
        raise ValueError("Booking was not created.")

    return state


def describe_booking(booking) -> str:
    shuttle = booking.shuttle
    route = shuttle.route

    return (
        f"the {shuttle.departure_time:%-I:%M %p} shuttle "
        f"from {route.pickup_location} to {route.dropoff_location} "
        f"on {booking.booking_date:%A, %B %-d}, "
        f"arriving at {shuttle.arrival_time:%-I:%M %p}"
    )


def respond(state: BookingState) -> BookingState:
    description = describe_booking(state["booking"])

    if state.get("already_booked"):
        response = f"You're already booked on {description}."
    else:
        response = f"Done. You're booked on {description}."

    return {
        **state,
        "response": response,
    }


def create_booking_graph(
    db: Session,
    llm: LLM,
):
    book_shuttle = create_booking_tool(db)

    graph = StateGraph(BookingState)

    graph.add_node(
        "understand_request",
        lambda state: understand_request(state, llm),
    )

    graph.add_node(
        "resolve_parameters",
        resolve_parameters,
    )

    graph.add_node(
        "execute_booking",
        lambda state: execute_booking(state, book_shuttle),
    )

    graph.add_node(
        "validate_result",
        validate_result,
    )

    graph.add_node(
        "respond",
        respond,
    )

    graph.add_conditional_edges(
        START,
        route_entry,
        ["understand_request", "resolve_parameters"],
    )

    graph.add_edge(
        "understand_request",
        "resolve_parameters",
    )

    graph.add_edge(
        "resolve_parameters",
        "execute_booking",
    )

    graph.add_edge(
        "execute_booking",
        "validate_result",
    )

    graph.add_edge(
        "validate_result",
        "respond",
    )

    graph.add_edge(
        "respond",
        END,
    )

    return graph.compile()
