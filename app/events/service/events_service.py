from app.events.utils.extractor import extract_event_works


class EventsService:
    def extract_raw_event_works(self, raw_text: str) -> list[str]:
        return extract_event_works(raw_text)
