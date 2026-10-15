import pytest
from app.strategy.engine import tire_wear, lap_delta, simulate_strategies
from app.services.replay import replay_service

def test_tire_wear_increases_with_age():
    # Arrange
    young, old = 5, 18
    # Act
    young_wear, old_wear = tire_wear("Medium", young), tire_wear("Medium", old)
    # Assert
    assert old_wear > young_wear
@pytest.mark.parametrize("compound", ["Soft", "Medium", "Hard", "Intermediate", "Wet"])
def test_lap_delta_is_finite(compound):
    assert isinstance(lap_delta(compound, 10, .5), float)
def test_worn_tire_performance_cliff():
    assert lap_delta("Medium", 25) > lap_delta("Medium", 5)
def test_monte_carlo_returns_ranked_options(race_state):
    results = simulate_strategies(race_state, iterations=500)
    assert len(results) >= 12
    assert [x["rank"] for x in results] == list(range(1, len(results)+1))
    assert all(x["expected_remaining_seconds"] > 0 for x in results)
def test_strategy_results_have_risk_and_confidence(race_state):
    r = simulate_strategies(race_state)[0]
    for key in ("weather_risk", "tire_life_risk", "traffic_risk", "confidence", "explanation"): assert key in r
@pytest.mark.asyncio
async def test_replay_next_lap_advances_and_decreases_rain_eta():
    # Arrange
    await replay_service.reset(); before = replay_service.state.current_lap
    # Act
    state = await replay_service.next_lap()
    # Assert
    assert state["current_lap"] == before + 1
    assert state["rain_eta_laps"] == 2
@pytest.mark.asyncio
async def test_reset_restores_lap_31():
    await replay_service.next_lap(); state = await replay_service.reset()
    assert state["current_lap"] == 31

def test_strategy_set_includes_required_options(race_state):
    results = simulate_strategies(race_state)
    names = {x['name'] for x in results}
    assert {'Stay out','Pit now','Pit next lap','Pit for Soft','Pit for Medium','Pit for Hard','Pit for Intermediates','Pit for Wet','One-stop plan','Two-stop plan','Undercut attempt','Overcut attempt'} <= names

def test_weather_scenario_has_intermediate_candidate(race_state):
    race_state['rain_probability'] = .95
    race_state['rain_eta_laps'] = 1
    results = simulate_strategies(race_state)
    assert any(x['tire'] == 'Intermediate' for x in results)

def test_monte_carlo_output_contains_position_probabilities(race_state):
    result = simulate_strategies(race_state)[0]
    assert 0 <= result['gain_probability'] <= 1
    assert 0 <= result['loss_probability'] <= 1
    assert result['confidence'] >= 0
