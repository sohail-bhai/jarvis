"""Run the control plane inside the desktop app.

The desktop app and the phone should be looking at the same tasks, the same
approvals and the same files. They are when they share one control plane, so
the API runs in this process rather than beside it - starting it from the GUI
is what makes the phone a client of *this* computer instead of a second,
unrelated VAVE.

Nothing here is reachable without pairing, and the pairing code is issued
directly by the same security object the API checks tokens against, so no code
travels over the network to be produced.
"""

import logging
import threading
import time

logger = logging.getLogger(__name__)


class LocalServer:
    """The API, running in a background thread of the desktop app."""

    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self._server = None
        self._thread = None
        self._security = None
        self._error = ""

    # -- state -------------------------------------------------------------

    @property
    def running(self):
        server = self._server
        return bool(server is not None and getattr(server, "started", False))

    @property
    def error(self):
        """Why the last start failed, in words a person can act on."""
        return self._error

    def addresses(self):
        """What to type on the phone. Empty while bound to this machine only."""
        from assistant.api.app import local_addresses

        if self.host in ("127.0.0.1", "localhost"):
            return [f"127.0.0.1:{self.port}"]
        return [f"{address}:{self.port}" for address in local_addresses()]

    # -- lifecycle ---------------------------------------------------------

    def start(self, timeout=10.0):
        """Start listening. Returns True once the port is actually open."""
        if self.running:
            return True

        self._error = ""
        try:
            import uvicorn

            from assistant.api.app import create_app
            from assistant.api.auth import ApiSecurity
            from assistant.control.service import get_control_plane
        except ModuleNotFoundError as missing:
            self._error = (f"{missing.name} is not installed. "
                           "Run: pip install -r requirements.txt")
            logger.warning("Cannot start the phone connection: %s", self._error)
            return False

        # Check the port before starting a thread. Uvicorn reports a bind
        # failure by logging and calling sys.exit, which raises SystemExit on
        # its own thread where nothing can catch it - the GUI would then wait
        # out the whole timeout and blame the wait rather than the port.
        busy = self._port_in_use()
        if busy:
            self._error = (f"Port {self.port} is already in use. Another copy of "
                           "VAVE, or another program, is using it.")
            logger.warning("Cannot start the phone connection: %s", self._error)
            return False

        plane = get_control_plane()
        # Held here as well as inside the app, so the GUI can mint a pairing
        # code without going back through HTTP to reach it.
        self._security = ApiSecurity(plane.store)
        app = create_app(control=plane, security=self._security)

        config = uvicorn.Config(app, host=self.host, port=self.port,
                                log_level="warning", lifespan="off")
        self._server = uvicorn.Server(config)
        # Uvicorn installs signal handlers by default, which only the main
        # thread may do.
        self._server.install_signal_handlers = lambda: None

        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name="vave-api")
        self._thread.start()

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.running:
                logger.info("Phone connection listening on %s:%s", self.host, self.port)
                return True
            if self._error:
                return False
            time.sleep(0.05)

        self._error = f"The server did not start within {int(timeout)} seconds."
        return False

    def _port_in_use(self):
        """True when something already holds our host and port."""
        import errno
        import socket

        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # No SO_REUSEADDR here on purpose: we want to know whether a
            # listener is there, not whether we could share the address.
            probe.bind((self.host, self.port))
            return False
        except OSError as error:
            return error.errno in (errno.EADDRINUSE, errno.EACCES)
        finally:
            probe.close()

    def _run(self):
        try:
            self._server.run()
        except SystemExit:
            # How uvicorn reports a bind failure once it is already running.
            if not self._error:
                self._error = (f"Port {self.port} is already in use. Another copy "
                               "of VAVE, or another program, is using it.")
            logger.warning("Phone connection could not bind port %s", self.port)
        except OSError as error:
            # Almost always "address already in use", which is worth saying
            # exactly rather than as a generic failure.
            self._error = (f"Port {self.port} is already in use. Close whatever "
                           f"is using it, or choose another port.")
            logger.warning("Phone connection failed: %s", error)
        except Exception as error:               # pragma: no cover - defensive
            self._error = str(error)
            logger.exception("Phone connection stopped unexpectedly.")

    def stop(self):
        """Stop listening. Paired phones keep their tokens for next time."""
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._server = None
        self._thread = None

    # -- pairing -----------------------------------------------------------

    def pairing_code(self):
        """A code for a new phone, valid for a few minutes.

        Returns (code, seconds) or (None, 0) when the server is not running -
        the codes live in the running process, so there is nothing to give out
        before it starts.
        """
        if not self.running or self._security is None:
            return None, 0
        issued = self._security.issue_pairing_code()
        return issued["code"], issued["expires_in"]


_server = None


def get_local_server(host=None, port=None):
    """The one server the desktop app starts, created on first use."""
    global _server
    if _server is None:
        from assistant.config import get_setting

        _server = LocalServer(host=host or get_setting("api_host", "0.0.0.0"),
                              port=int(port or get_setting("api_port", 8765)))
    return _server
