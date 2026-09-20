"""Bounded access to every retained activity summary, in arrival order."""
from dataclasses import dataclass

import streamlit as st

PAGE_SIZE = 40


@dataclass(frozen=True)
class ActivityWindow:
    start: int
    end: int
    total: int
    anchor: int
    page: int
    page_count: int


def activity_window(total, *, page=0, anchor=None):
    """Zero-based slice bounds; an older page stays anchored if new entries arrive."""
    total = max(0, total)
    anchor = total if anchor is None else max(0, min(total, anchor))
    pages = max(1, (anchor + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, pages - 1))
    end = max(0, anchor - page * PAGE_SIZE)
    return ActivityWindow(max(0, end - PAGE_SIZE), end, total, anchor, page, pages)


def move_activity_cursor(cursor, action, total):
    window = activity_window(total, **cursor)
    if action == 'newest' or (action == 'newer' and window.page <= 1):
        return {'page': 0, 'anchor': None}
    page = {'older': window.page + 1, 'newer': window.page - 1,
            'oldest': window.page_count - 1}[action]
    return {'page': max(0, min(page, window.page_count - 1)), 'anchor': window.anchor}


def _move(key, action, total):
    st.session_state[key] = move_activity_cursor(st.session_state.get(key, {}), action, total)


def _render_window(state, window):
    from . import components as C

    st.caption('Readable activity summaries in reverse arrival order. Tool arguments and results may be shortened; '
               'Run details > Raw events retains the supplied structured payloads.')
    if window.anchor < window.total:
        st.caption(f'{window.total - window.anchor} newer entries are available. Choose Newest to view them.')
    C.render_timeline(state, end=window.end)


def render_activity_history(state, *, key):
    if len(state.timeline) <= PAGE_SIZE:
        # Bounded small histories are available immediately when opened locally.
        with st.expander(f'Full activity timeline ({len(state.timeline)})'):
            _render_window(state, activity_window(len(state.timeline)))
    else:
        _render_large_history(state, key=key)


@st.fragment
def _render_large_history(state, *, key):
    panel = st.expander(f'Full activity timeline ({len(state.timeline)})', key=f'{key}:open', on_change='rerun')
    if not panel.open:
        return
    with panel:
        cursor_key = f'{key}:cursor'
        window = activity_window(len(state.timeline), **st.session_state.get(cursor_key, {}))
        for column, action, label, disabled in zip(
            st.columns(4), ('newest', 'newer', 'older', 'oldest'), ('Newest', 'Newer', 'Older', 'Oldest'),
            (window.page == 0 and window.anchor == window.total, window.page == 0,
             window.start == 0, window.start == 0),
        ):
            with column:
                st.button(label, key=f'{key}:{action}', disabled=disabled, on_click=_move,
                          args=(cursor_key, action, len(state.timeline)), width='stretch')
        st.caption(f'Page {window.page + 1} of {window.page_count}. Up to {PAGE_SIZE} entries are prepared at a time.')
        _render_window(state, window)
