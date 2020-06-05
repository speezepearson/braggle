import dataclasses
import os
from pathlib import Path
import re
from typing import Optional

from braggle import *

def n_leading_spaces(s):
    return len(re.match('^ *', s).group())

def strip_whitespace(s):
    s = s.strip('\n')
    n = min(n_leading_spaces(line) for line in s.split('\n') if line)
    return '\n'.join(line[n:] for line in s.split('\n'))

def exec_then_eval(to_exec, to_eval):
    # Due to some scoping subtlety, the locals and globals in
    # exec and eval should be the same, or we won't be able to
    # exec a program like
    #
    #   xs = []
    #   (lambda: xs)()
    #
    # I dunno. I just dunno.
    scope = globals().copy()
    if to_exec is not None:
        exec(to_exec, scope, scope)
    # print(to_eval)
    return eval(to_eval, scope, scope)

@dataclasses.dataclass
class Example:
    show_code: str
    prep_code: Optional[str] = None

    def to_grid_row(self):
        element = exec_then_eval(to_exec=self.prep_code, to_eval=self.show_code)
        code = self.show_code if self.prep_code is None else f'{self.prep_code}\n\nserve(GUI({self.show_code}))'
        return [CodeBlock(code), element]

def main() -> None:

    examples = {}

    def example_grid_for_types(*types):
        header_row = [Bold('Code'), Bold('Result')]
        rows = [examples[t].to_grid_row() for t in types]
        return Grid(cells=[header_row] + rows)

    examples[Text] = Example('Text("some plain text")')
    # examples[Paragraph] = Example('Container(Paragraph("one"), Paragraph("two"))')
    # examples[Bold] = Example('Bold("some bold text")')
    examples[CodeSnippet] = Example('CodeSnippet("some code")')
    examples[CodeBlock] = Example(r'CodeBlock("one\ntwo")')
    examples[Link] = Example('Link(text="google", url="http://google.com")')

    examples[Container] = Example('Container([Text("one"), CodeSnippet("two")])')
    # examples[Viewport] = Example(strip_whitespace(r'''
    #     Viewport(
    #         CodeBlock('\n'.join(50*'viewport ' for _ in range(100))),
    #         width=400, height=200)'''))
    examples[List] = Example('List([Text("one"), Text("two")])')
    # examples[Grid] = Example(strip_whitespace('''
    #     Grid(cells=[
    #         [Text("00"), Text("01")],
    #         [Text("10"), Text("11")]])'''))

    examples[Image] = Example("Image('https://www.iana.org/_img/2013.1/iana-logo-header.svg')")

    examples[Button] = Example(
        'Container([click_count, button])',
        strip_whitespace('''
            click_count = Text('0')
            def button_clicked():
                n = int(click_count.text)
                click_count.text = str(n+1)

            button = Button('Click me!', callback=button_clicked)'''))

    examples[TextField] = Example(
        'Container([text_field, LineBreak(), reversed_text_field_contents])',
        strip_whitespace('''
            reversed_text_field_contents = Text('')
            def text_field_changed(value):
                reversed_contents = ''.join(reversed(value))
                reversed_text_field_contents.text = reversed_contents

            text_field = TextField(callback=text_field_changed)
            text_field.value = "Reversed"'''))

    # examples[BigTextField] = Example(
    #     'Container(text_field, reversed_text_field_contents)',
    #     strip_whitespace('''
    #         reversed_text_field_contents = Text('')
    #         def text_field_changed():
    #             reversed_contents = ''.join(reversed(text_field.value))
    #             reversed_text_field_contents.text = reversed_contents
    #         text_field = BigTextField(callback=text_field_changed)
    #         text_field.value = "Reversed"'''))
    #
    # examples[Dropdown] = Example(
    #     'Container(dropdown, selected_dropdown_item)',
    #     strip_whitespace('''
    #         selected_dropdown_item = Text('')
    #         dropdown = Dropdown(['Dr', 'op', 'do', 'wn'])
    #         @dropdown.def_change_callback
    #         def _():
    #             selected_dropdown_item.text = dropdown.value
    #         dropdown.value = "wn"'''))
    #
    # examples[NumberField] = Example(
    #     'Container(number_field, number_field_squared)',
    #     strip_whitespace('''
    #         number_field_squared = Text('')
    #         def number_changed():
    #             if number_field.value is None:
    #                 number_field_squared.text = ''
    #             else:
    #                 number_field_squared.text = str(number_field.value ** 2)
    #         number_field = NumberField(callback=number_changed)
    #         number_field.value = 12'''))
    #
    # examples[ColorField] = Example(
    #     'Container(color_field, colored_text)',
    #     strip_whitespace('''
    #         colored_text = Text('colored')
    #         def color_changed():
    #             color = color_field.value
    #             color_hex = '#{:02x}{:02x}{:02x}'.format(*color)
    #             colored_text.css['color'] = color_hex
    #         color_field = ColorField(callback=color_changed)
    #         color_field.value = (0, 0, 255)'''))
    #
    # examples[DateField] = Example(
    #     'Container(date_field, weekday_text)',
    #     strip_whitespace('''
    #         weekday_text = Text('...')
    #         DAYS = ('Monday', 'Tuesday', 'Wednesday', 'Thursday',
    #                         'Friday', 'Saturday', 'Sunday')
    #         def date_changed():
    #             if date_field.value is None:
    #                 weekday_text.text = ''
    #             else:
    #                 weekday_text.text = DAYS[date_field.value.weekday()]
    #         date_field = DateField(callback=date_changed)'''))
    #
    # examples[FloatSlider] = Example(
    #     'Container(slider, slider_value_squared)',
    #     strip_whitespace('''
    #         slider_value_squared = Text('')
    #         def slider_changed():
    #             if slider.value is None:
    #                 slider_value_squared.text = ''
    #             else:
    #                 slider_value_squared.text = '{:.3g}'.format(slider.value ** 2)
    #         slider = FloatSlider(min=0, max=10, callback=slider_changed)
    #         slider.value = 3'''))
    #
    # examples[IntegerSlider] = Example(
    #     'Container(slider, slider_value_squared)',
    #     strip_whitespace('''
    #         slider_value_squared = Text('')
    #         def slider_changed():
    #             if slider.value is None:
    #                 slider_value_squared.text = ''
    #             else:
    #                 slider_value_squared.text = str(slider.value ** 2)
    #         slider = IntegerSlider(min=0, max=5, callback=slider_changed)
    #         slider.value = 3'''))


    serve(GUI(
        Text('''
            Here is a list of all the kinds of Element available to you.
            See the classes' documentation for more detailed information on them.'''),
        List([
            Container([
                Text('Text of many flavors:'),
                example_grid_for_types(Text, CodeSnippet, CodeBlock, Link)]),
            Container([
                Text('Input of many flavors:'),
                example_grid_for_types(Button, TextField)]),
            Container([
                Text('Structural elements of many flavors:'),
                example_grid_for_types(Container, List)]),
            Container([
                Text('Other:'),
                example_grid_for_types(Image)])])
    ))

if __name__ == '__main__':
    main()
