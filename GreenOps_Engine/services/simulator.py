"""
GreenOps — Live Demo Simulator

Runs a background thread that periodically generates realistic API calls 
for the demo user, making the dashboard feel "alive" during presentations.
"""

import threading
import time
import uuid
import random
import logging
from datetime import datetime, timezone

from database import insert_api_call, get_demo_user_id, prune_demo_data
from services.model_profiles import estimate_energy_for_call
from services.carbon_calculator import calculate_impact

logger = logging.getLogger("greenops.simulator")
logging.basicConfig(level=logging.INFO)

class SimulatorThread(threading.Thread):
    def __init__(self, interval_seconds: int = 5):
        super().__init__(daemon=True)
        self.interval = interval_seconds
        self.running = False
        self.demo_user_id = None
        self.models = ["gpt-4o", "gpt-4o-mini", "claude-3-5-haiku-20241022", "gemini-2.5-flash"]
        self.projects = ["chatbot", "research", "fraud-detection", "default"]
        self.regions = ["us_virginia", "eu_ireland", "global_average"]

    def run(self):
        self.running = True
        logger.info(f"Simulator thread started (interval={self.interval}s)")

        # Wait for DB to be initialized and get demo user
        while self.running and not self.demo_user_id:
            try:
                self.demo_user_id = get_demo_user_id()
            except Exception:
                pass
            if not self.demo_user_id:
                time.sleep(2)

        logger.info(f"Simulator active for demo user: {self.demo_user_id}")

        counter = 0
        while self.running:
            time.sleep(self.interval)
            try:
                self._generate_call()
                counter += 1
                # Prune every ~20 calls (about 100 seconds) to maintain max 5000 records
                if counter >= 20:
                    prune_demo_data(self.demo_user_id, 5000)
                    from database import vacuum_db
                    vacuum_db()
                    counter = 0
            except Exception as e:
                logger.error(f"Simulator error: {e}")

    def stop(self):
        self.running = False

    def _generate_call(self):
        if not self.demo_user_id:
            return

        model_id = random.choice(self.models)
        project = random.choice(self.projects)
        region = random.choice(self.regions)

        input_tokens = random.randint(10, 500)
        output_tokens = random.randint(10, 200)

        estimation = estimate_energy_for_call(model_id, input_tokens, output_tokens)
        if not estimation:
            return

        impact = calculate_impact(estimation["energy_wh"], region=region)
        
        call_data = {
            "call_id": str(uuid.uuid4()),
            "user_id": self.demo_user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_id": model_id,
            "provider": estimation["provider"],
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "energy_wh": estimation["energy_wh"],
            "co2_g": impact.co2_g,
            "water_ml": impact.water_ml,
            "cost_usd": estimation["cost_usd"],
            "latency_ms": random.randint(150, 1200),
            "region": region,
            "source": "simulator",
            "project": project,
            "metadata": {"simulated": True},
        }

        insert_api_call(call_data)
        logger.debug(f"Simulated call for {model_id} ({input_tokens} in / {output_tokens} out)")

# Global instance
_simulator = None

def start_simulator(interval_seconds: int = 5):
    global _simulator
    if _simulator is None or not _simulator.running:
        _simulator = SimulatorThread(interval_seconds)
        _simulator.start()

def stop_simulator():
    global _simulator
    if _simulator:
        _simulator.stop()
        _simulator = None
