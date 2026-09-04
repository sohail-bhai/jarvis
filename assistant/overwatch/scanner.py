import uiautomation as auto
import logging

logger = logging.getLogger(__name__)

def scan_windows(max_z_order=3):
    root = auto.GetRootControl()
    windows = []
    
    for i, win in enumerate(root.GetChildren()):
        if i >= max_z_order:
            break
        if win.ControlType == auto.ControlType.WindowControl:
            windows.append(win)
            
    elements = []
    for win in windows:
        for control, depth in auto.WalkControl(win, includeTop=True, maxDepth=10):
            if control.Name:
                elements.append({
                    "name": control.Name,
                    "control": control,
                    "runtime_id": control.GetRuntimeId(),
                    "window": win.Name
                })
    return elements
