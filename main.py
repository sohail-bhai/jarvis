import argparse

from assistant.controller import AssistantController
from assistant.smoke_test import run_smoke_tests
from assistant import events
from assistant import logging_setup

def build_parser():
    parser = argparse.ArgumentParser(
        description="JARVIS Desktop Assistant"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--text",
        help="Run one text command without using the microphone."
    )
    mode.add_argument(
        "--once",
        action="store_true",
        help="Listen for one microphone command, execute it, then exit."
    )
    mode.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run safe command-router smoke checks with side effects stubbed."
    )
    mode.add_argument(
        "--gui",
        action="store_true",
        help="Launch the CustomTkinter desktop dashboard."
    )
    parser.add_argument(
        "--no-speech",
        action="store_true",
        help="Print responses without using pyttsx3 text-to-speech."
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.smoke_test:
        # Configure logging first; the smoke test reports results through logging.
        logging_setup.configure_logging()
        passed = run_smoke_tests()
        return 0 if passed else 1

    if args.gui:
        from jarvis_gui import main as gui_main
        return gui_main()

    bus = events.EventBus(maxsize=2000)
    events.set_global_event_bus(bus)
    logging_setup.configure_logging(event_bus=bus)

    from assistant import audit, guard, confirm, overwatch
    from pathlib import Path
    audit.configure(Path("logs/audit.jsonl"), max_bytes=5_000_000, backup_count=20)
    guard.configure(event_bus=bus)
    confirm.configure(event_bus=bus)
    overwatch.configure(event_bus=bus)

    controller = AssistantController(event_bus=bus, speech_enabled=not args.no_speech)

    if args.text:
        print(f"Running text command once: {args.text}")
        controller.handle_text_command(args.text)
        return 0

    if args.once:
        print("One-listen mode: listening for one command.")
        controller.run_once()
        return 0

    controller.run_forever()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
