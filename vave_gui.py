def main():
    try:
        from gui.app import VaveDashboardApp
    except ModuleNotFoundError as error:
        if error.name == "customtkinter":
            print("CustomTkinter is not installed.")
            print("Install dependencies with: pip install -r requirements.txt")
            return 1
        raise

    app = VaveDashboardApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
