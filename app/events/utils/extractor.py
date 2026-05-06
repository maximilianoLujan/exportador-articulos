from app.events.utils.block_finder import find_event_works_block
from app.events.utils.clean_noise import clean_event_work_noise
from app.events.utils.splitter import split_event_works
from app.importer.utils.text_cleaning import clean_text


def extract_event_works(raw_text: str) -> list[str]:
    """Extrae trabajos en eventos (raw strings) desde el texto completo del PDF."""

    block = find_event_works_block(raw_text)
    if not block:
        return []

    block = clean_event_work_noise(block)

    items = split_event_works(block)
    return [clean_text(i).strip() for i in items if clean_text(i).strip()]
