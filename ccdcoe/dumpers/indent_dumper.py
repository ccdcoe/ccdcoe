import yaml


class IndentDumper(yaml.Dumper):

    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)
