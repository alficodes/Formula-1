"""Optional historical ingestion. The dashboard remains runnable without network access."""
import logging
from pathlib import Path
from app.config import settings
log = logging.getLogger(__name__)

def load_monaco_session(year: int = 2024, session_name: str = "R"):
    try:
        import fastf1
        cache = Path(settings.fastf1_cache_dir); cache.mkdir(parents=True, exist_ok=True)
        fastf1.Cache.enable_cache(str(cache))
        session = fastf1.get_session(year, "Monaco", session_name)
        session.load( laps=True, telemetry=False, weather=True, messages=True)
        laps = session.laps
        return {"year": year, "event": "Monaco Grand Prix", "session": session_name, "laps": laps, "weather": getattr(session, "weather_data", None), "race_control": getattr(session, "race_control_messages", None)}
    except Exception as exc:
        log.warning("FastF1 unavailable or session load failed; use deterministic demo replay: %s", exc)
        return None
