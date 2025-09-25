import json

import click


class ConsoleOutput:

    @staticmethod
    def format_output(format_type, input_list):
        """
        Method to format the input_list based on a given format_type (json)

        :param format_type: Format type
        :type format_type: str
        :param input_list: List with dicts that needs formatting
        :type input_list: list
        :return: Formatted output
        :rtype: based on given format_type
        """

        if format_type == "json":
            output = json.dumps(input_list, indent=4, sort_keys=True, default=str)
            return output

    @staticmethod
    def print(input_data: str | dict | list, output="json"):
        if isinstance(input_data, list | dict):
            click.echo(ConsoleOutput.format_output(output, input_data))
        elif isinstance(input_data, str):
            click.echo(input_data)
