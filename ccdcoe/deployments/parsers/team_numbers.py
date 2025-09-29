import logging
from typing import List

from ccdcoe.loggers.console_logger import ConsoleLogger

logging.setLoggerClass(ConsoleLogger)

logger = logging.getLogger(__name__)


def parse_team_number(team_number: str) -> List[int]:
    """
    Method for parsing the team number into a list of integers.
    Parsed list is made unique to avoid double entries.
    """
    team_number_list = team_number.split(",")

    parsed_team_numbers = []

    for each in team_number_list:
        if "-" in each:
            splitted = each.split("-")
            try:
                try:
                    for i in range(int(splitted[0]), int(splitted[1]) + 1):
                        parsed_team_numbers.append(i)
                except ValueError:
                    logger.warning(f"Invalid team number entry '{each}'")
            except IndexError:
                logger.warning(f"Invalid range entry for team number'{each}'")
        else:
            try:
                parsed_team_numbers.append(int(each))
            except ValueError:
                logger.warning(
                    f"Invalid team number entry '{each}'; could not convert to int"
                )

    return list(set(parsed_team_numbers))
