from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agent.factory import create_llm
from app.agent.llm import LLM
from app.db.database import get_db
from app.graph.booking_graph import create_booking_graph
from app.schemas.booking import BookingRequest, BookingResponse


router = APIRouter(
    prefix="/bookings",
    tags=["bookings"],
)


def get_llm() -> LLM:
    return create_llm(reference_date=date.today())


@router.post("", response_model=BookingResponse)
def create_booking(
    request: BookingRequest,
    db: Session = Depends(get_db),
    llm: LLM = Depends(get_llm),
):
    graph = create_booking_graph(
        db=db,
        llm=llm,
    )

    result = graph.invoke(
        {
            "user_id": request.user_id,
            "user_input": request.message,
        }
    )

    return BookingResponse(
        booking_id=result["booking_id"],
        message=result["response"],
    )
