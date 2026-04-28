import textwrap

class Formatter:
    def __init__(self, width=80):
        self.width = width

    def format(self, text):
        if not text:
            return ""
        lines = text.split('\n')
        formatted = []
        for line in lines:
            if len(line) > self.width:
                formatted.append(textwrap.fill(line, width=self.width))
            else:
                formatted.append(line)
        return '\n'.join(formatted)