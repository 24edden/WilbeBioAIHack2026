"""Defer large supporting records while keeping small disclosures instant."""
from collections.abc import Callable

import streamlit as st


def render_details(label: str, render: Callable[[], None], *, key: str, lazy: bool = False) -> None:
    """Small panels open locally; expensive panels render in their own fragment.

    Callers pass a renderer, not pre-serialized content, so closed lazy panels do
    no preparation work. The fragment confines an open/close event to this panel.
    """
    if lazy:
        _render_lazy_details(label, render, key=key)
    else:
        with st.expander(label):
            render()


@st.fragment
def _render_lazy_details(label: str, render: Callable[[], None], *, key: str) -> None:
    panel = st.expander(label, key=key, on_change="rerun")
    if panel.open:
        with panel:
            render()
