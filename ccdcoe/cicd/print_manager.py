class PrintManager:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    @staticmethod
    def print_line():
        print(
            f"{PrintManager.HEADER}{PrintManager.OKCYAN}"
            + "*" * 150
            + f"{PrintManager.ENDC}"
        )
        print(
            f"{PrintManager.HEADER}{PrintManager.OKCYAN}"
            + "*" * 150
            + f"{PrintManager.ENDC}"
        )

    @staticmethod
    def exit(exit_code: int):
        PrintManager.print_line()
        exit(exit_code)

    @staticmethod
    def print_start(msg: str) -> None:
        PrintManager.print_line()
        print(f"{PrintManager.HEADER}{PrintManager.OKBLUE}{msg}{PrintManager.ENDC}")

    @staticmethod
    def print_fail(msg: str) -> None:
        print(f"{PrintManager.BOLD}{PrintManager.FAIL}{msg}{PrintManager.ENDC}")

    @staticmethod
    def print_warning(msg: str) -> None:
        print(f"{PrintManager.BOLD}{PrintManager.WARNING}{msg}{PrintManager.ENDC}")

    @staticmethod
    def print_ok(msg: str) -> None:
        print(f"{PrintManager.BOLD}{PrintManager.OKGREEN}{msg}{PrintManager.ENDC}")
