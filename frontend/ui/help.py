"""Immediate, local help tips with the same native widget semantics."""
from html import escape
from uuid import uuid4

import streamlit as st


def widget(render, label, *args, help=None, help_label=None, **kwargs):
    """Keep widget keys/labels intact; render its help without a delayed popover."""
    if not help:
        return render(label, *args, **kwargs)
    tip_id = "trace-tip-" + uuid4().hex
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
