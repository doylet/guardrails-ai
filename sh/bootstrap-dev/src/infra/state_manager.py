#!/usr/bin/env python3
"""
State Manager Module
Handles installation state tracking and persistence
"""
import yaml
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from .utils import Colors
from .presenters import StatePresenter


class StateManager:
    """Manages installation state persistence and tracking"""

    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.state_path = target_dir / ".ai-guardrails-state.yaml"

    def load_state(self) -> Dict:
        """Load the installation state file"""
        if not self.state_path.exists():
            return {
                'version': '1.0.0',
                'installed_profile': None,
                'installed_components': [],
                'installation_history': []
            }

        try:
            with open(self.state_path) as f:
                return yaml.safe_load(f) or {'version': '1.0.0', 'installed_components': [], 'installation_history': []}
        except Exception as e:
            print(f"{Colors.warn('[WARN]')} Failed to load state file: {e}")
            return {'version': '1.0.0', 'installed_components': [], 'installation_history': []}

    def save_state(self, state: Dict):
        """Save the installation state file"""
        try:
            with open(self.state_path, 'w') as f:
                yaml.dump(state, f, default_flow_style=False, sort_keys=False, indent=2)
        except Exception as e:
            print(f"{Colors.error('[ERROR]')} Failed to save state file: {e}")

    def update_state_for_profile(self, profile: str, components: List[str]):
        """Update state file after profile installation"""
        state = self.load_state()
        state['installed_profile'] = profile
        state['installed_components'] = list(set(state.get('installed_components', []) + components))

        # Add to history
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': 'install_profile',
            'profile': profile,
            'components': components
        }
        state.setdefault('installation_history', []).append(history_entry)

        self.save_state(state)

    def update_state_for_component(self, component: str):
        """Update state file after component installation"""
        state = self.load_state()
        if component not in state.get('installed_components', []):
            state.setdefault('installed_components', []).append(component)

            # Add to history
            history_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': 'install_component',
                'component': component
            }
            state.setdefault('installation_history', []).append(history_entry)

            self.save_state(state)

    def show_state(self):
        """Show current installation state"""
        state = self.load_state()
        StatePresenter.show_state(state)

    def get_installed_components(self) -> List[str]:
        """Get list of installed components"""
        state = self.load_state()
        return state.get('installed_components', [])

    def get_installed_profile(self) -> str:
        """Get currently installed profile"""
        state = self.load_state()
        return state.get('installed_profile')

    def is_component_installed(self, component: str) -> bool:
        """Check if a component is marked as installed"""
        return component in self.get_installed_components()
