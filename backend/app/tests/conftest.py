import pytest
from app.models.race import demo_state
@pytest.fixture
def race_state(): return demo_state().to_dict()
