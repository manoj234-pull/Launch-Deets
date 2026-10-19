"""Offline navigation check; never submits a research request."""
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest


class NavigationTests(unittest.TestCase):
    def test_space_entry_opens_home_then_research(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "streamlit_app.py"), default_timeout=20)
        app.run()
        self.assertFalse(app.exception)
        self.assertIn("space-entry", "".join(m.value for m in app.markdown))
        app.button(key="enter_space").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(app.session_state["entered"])
        app.button(key="home_cta").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox(key="launch_scope").value, "All launches")
