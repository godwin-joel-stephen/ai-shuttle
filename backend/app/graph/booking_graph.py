from sqlalchemy.orm import Session
from langgraph.graph import END, START, StateGraph

from app.agent.llm import LLM
from app.graph.state import BookingState
from app.tools.booking_tools import create_booking_tool


def understand_request(
    state: BookingState,
    llm: LLM,
) -> BookingState:
    user_input = state.get("user_input")

    if not user_input:
        raise ValueError("user_input is required.")

    request = llm.invoke(user_input)

    return {
        **state,
        "intent": request.intent.value,
        "booking_date": request.booking_date,
    }


def resolve_parameters(state: BookingState) -> BookingState:
    if "user_id" not in state:
        raise ValueError("user_id is required.")

    if "booking_date" not in state:
        raise ValueError("booking_date is required.")

    return state


def execute_booking(
    state: BookingState,
    book_shuttle,
) -> BookingState:
    booking = book_shuttle.invoke(
        {
            "user_id": state["user_id"],
            "booking_date": state["booking_date"],
        }
    )

    return {
        **state,
        "booking_id": booking.id,
    }


def validate_result(state: BookingState) -> BookingState:
    booking_id = state.get("booking_id")

    if booking_id is None:
        raise ValueError("Booking was not created.")

    return state


def respond(state: BookingState) -> BookingState:
    booking_id = state["booking_id"]

    return {
        **state,
        "response": (
            f"Shuttle booked successfully. "
            f"Booking ID: {booking_id}."
        ),
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

    graph.add_edge(
        START,
        "understand_request",
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
