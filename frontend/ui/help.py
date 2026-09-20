"""Immediate, local help tips with the same native widget semantics."""
from html import escape
from uuid import NAMESPACE_URL, uuid4, uuid5

import streamlit as st


def widget(render, label, *args, help=None, help_label=None, help_key=None, **kwargs):
    """Keep native semantics; explicit help keys must be unique in the visible view.

    Polling callers can retain their help DOM by supplying a stable view/control
    scope. Unscoped repeated controls still get independent IDs by default.
    """
    if not help:
        return render(label, *args, **kwargs)
    tip_id = "trace-tip-" + (uuid5(NAMESPACE_URL, "trace-help:" + str(help_key)).hex
                            if help_key is not None else uuid4().hex)
    accessible_label = help_label or ("this section" if kwargs.get("unsafe_allow_html") else label)
    with st.container():
        result = render(label, *args, **kwargs)
        st.html(
            f'<span class="trace-help-anchor" style="anchor-name:--{tip_id}">'
            f'<button type="button" class="trace-help-trigger" '
            f'aria-label="Help for {escape(str(accessible_label), quote=True)}" '
            f'aria-describedby="{tip_id}">'
            '<span aria-hidden="true">?</span></button>'
            f'<span class="trace-help-text" id="{tip_id}" role="tooltip" '
            f'style="position-anchor:--{tip_id}">{escape(str(help))}</span></span>'
        )
    return result
