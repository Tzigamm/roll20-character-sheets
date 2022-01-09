"""Module for providing the parts in the template.html file"""
import csv
import textwrap
from pathlib import Path

import markdown

from . import tab_1_character, tab_2_abilities, tab_3_magic, tab_4_combat, tab_5_spells, tab_6_sheet
from .helpers import xp
from .translations import translation_attrs, translation_attrs_setup


# Alert system to display update notes and warnings on top of the sheet
# Originaly developed to warn about loss of data during an update
# Those functions are typically used from the HTML file itself, leveraging
# the ability of fileval.py to evaluate any python expression embedded into
# the HTML, not just variables

# The system works by assigning an ID, either int or str, to each alerts, and
# using an attribute to hide the alert once it has been closed
def alert(title: str, text: str, *, level: str = "warning", ID: str = None):
    """
    Generate the HTML to display a banner that can be permanently hidden

    This is used to inform player of important changes in updates.

    Arguments:
        text: Main text of the banner
        title: Title of the banner
        type: On of "warning", "info". The aspect of the banner
        ID: optional string ID of this banner, if you need to check if it is
            open/closed somewhere. Do NOT use numbers
    """
    if not level in ("info", "warning"):
        raise ValueError("Level must be among 'info', 'warning'")
    if alert.has_disable_been_called:
        raise RuntimeError(
            "The function alert() is called after disable_old_alert() has generated "
            "the javascript code to handle hidding closed alerts. This breaks the "
            "system completely, make sure disable_old_alerts is called last"
        )
    if ID is None:
        alert_id = alert.numid
        alert.numid += 1
    else:
        alert_id = str(ID)
        alert.strid.append(alert_id)

    indent = " " * 4 * 4
    text = str(text).replace("\n", "\n" + indent)
    return textwrap.dedent(
        f"""\
        <input type="hidden" class="alert-hidder" name="attr_alert-{alert_id}" value="0"/>
        <div class="alert alert-{level}">
            <div>
                <h3> {level.title()} - {title}</h3>
                {text}
            </div>
            <label class="fakebutton">
                <input type="checkbox" name="attr_alert-{alert_id}" value="1" /> ×
            </label>
        </div>"""
    )


# python supports attributes on function
# we use that to store the internal variable used by the function
alert.numid = 0
alert.strid = []
alert.has_disable_been_called = False


def disable_old_alerts(marker: str):
    alert.has_disable_been_called = True
    indent = " " * 4 * 3
    lines = f",\n{indent}".join(
        f'"alert-{i}": 1' for i in list(range(alert.numid)) + alert.strid
    )
    return textwrap.dedent(
        f"""\
        setAttrs({{
            "{marker}": 1,
            {lines}
        }}); """
    )


# Add new parts to this dictionary
# parts can be defined in other modules and imported if the generating
# code is long
EXPORTS = {
    # makes the module available
    "markdown": markdown,
    # makes those function available in the HTML
    "xp": xp,
    "alert": alert,
    "disable_old_alerts": disable_old_alerts,
    # Makes those values available in the HTML
    "translation_attrs": translation_attrs,
    "translation_attrs_setup": translation_attrs_setup,
    "html_header": "<!-- DO NOT MODIFY !\nThis file is automatically generated from a template. Any change will be overwritten\n-->",
    "css_header": "DO NOT MODIFY !\nThis file is automatically generated from a template. Any change will be overwritten\n",
}


EXPORTS["botch_separate"] = (
    "&{template:botch} {{roll= "
    + (
        "?{@{botch_num_i18n} | "
        + "|".join(
            f"{n} {'Die' if n==1 else 'Dice'}," + " ".join(["[[1d10cf10cs0]]"] * n)
            for n in range(1, 9)
        )
        + "}"
    )
    + " }} {{type=Grouped}}"
)

# Colors for the "custom" rolltemplate
with open(Path(__file__).parent / "css_colors.csv", newline="") as f:
    reader = csv.DictReader(f)
    css_rules = []
    for color_def in reader:
        # Base CSS rules
        lines_header = [
            f".sheet-rolltemplate-custom .sheet-crt-container.sheet-crt-color-{color_def['color']} {{",
            f"    --header-bg-color: {color_def['hex']};",
        ]
        lines_rolls = [
            f".sheet-rolltemplate-custom .sheet-crt-container.sheet-crt-rlcolor-{color_def['color']} .inlinerollresult {{",
            f"    --roll-bg-color: {color_def['hex']};",
        ]
        lines_buttons = [
            f".sheet-rolltemplate-custom .sheet-crt-container.sheet-crt-btcolor-{color_def['color']} a {{",
            f"    --button-bg-color: {color_def['hex']};",
        ]

        # Adapt text color to background color
        hex_color = color_def["hex"].lstrip("#")
        r, g, b = tuple(int(hex_color[2 * i : 2 * i + 2], 16) / 255 for i in range(3))
        # Assuming sRGB -> Luma
        # may need fixing, color spaces are confusing
        luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
        if luma > 0.5:  # arbitrary threshold
            # switch to black text if luma is high enough
            lines_header.append("    --header-text-color: #000;")
            lines_buttons.append("    --button-text-color: #000;")
        if luma < 0.5:
            lines_rolls.append("    --roll-text-color: #FFF;")

        # Build the rules
        for lines in (lines_header, lines_rolls, lines_buttons):
            lines.append("}")
            css_rules.append("\n".join(lines))

    EXPORTS["custom_rt_color_css"] = "*/\n" + "\n".join(css_rules) + "\n/*"

# Add the variables from all tabs
EXPORTS.update(tab_1_character.EXPORTS)
EXPORTS.update(tab_2_abilities.EXPORTS)
EXPORTS.update(tab_3_magic.EXPORTS)
EXPORTS.update(tab_4_combat.EXPORTS)
EXPORTS.update(tab_5_spells.EXPORTS)
EXPORTS.update(tab_6_sheet.EXPORTS)