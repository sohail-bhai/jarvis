import importlib.util
import unittest

HAS_TKINTER = importlib.util.find_spec("tkinter") is not None

if HAS_TKINTER:
    from gui.store import AppStore
    from gui.app import VaveDashboardApp


@unittest.skipUnless(HAS_TKINTER, "tkinter is not installed on this machine")
class TestVaveGUI(unittest.TestCase):
    def test_store_operations(self):
        store = AppStore()
        self.assertEqual(store.current_page, "home")
        
        # Test navigation
        store.set_page("devices")
        self.assertEqual(store.current_page, "devices")
        
        # Test logs
        initial_count = len(store.system_logs)
        store.add_system_log("Test log entry", "working")
        self.assertEqual(len(store.system_logs), initial_count + 1)
        self.assertEqual(store.system_logs[-1]["text"], "Test log entry")
        
        # Test memory
        initial_mem_count = len(store.memories)
        first_mem_id = store.memories[0]["id"]
        store.forget_memory(first_mem_id)
        self.assertEqual(len(store.memories), initial_mem_count - 1)
        
        # Test drawer
        store.open_drawer("device", {"name": "Test Device"})
        self.assertIsNotNone(store.active_drawer)
        self.assertEqual(store.active_drawer["type"], "device")
        store.close_drawer()
        self.assertIsNone(store.active_drawer)

    def test_app_lifecycle_and_page_switching(self):
        # Instantiate full CustomTkinter dashboard
        app = VaveDashboardApp()
        
        # Verify initial layout and widgets
        self.assertIsNotNone(app.sidebar)
        self.assertIsNotNone(app.topbar)
        self.assertIsNotNone(app.system_log_panel)
        self.assertIsNotNone(app.detail_drawer)
        
        # Cycle through all pages to ensure no errors in rendering
        for page_name in ["home", "devices", "files", "google", "web", "activity", "settings"]:
            app.navigate_to(page_name)
            self.assertEqual(app.current_page_widget, app.pages[page_name])
            app.update_idletasks()
            
        # Test drawer open/close
        app.open_drawer("device", {"name": "My Computer", "status": "Online", "capabilities": ["Access files"]})
        app.update_idletasks()
        app.close_drawer()
        app.update_idletasks()
        
        # Clean up window
        app.destroy()


if __name__ == "__main__":
    unittest.main()
