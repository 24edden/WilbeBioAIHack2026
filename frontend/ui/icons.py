"""Small local SVG vocabulary. Backend icon IDs never become executable markup."""

PATHS = {
    'planner': '<rect x="3" y="3" width="7" height="6" rx="1"/><rect x="14" y="15" width="7" height="6" rx="1"/><path d="M6.5 9v9H14M10 6h7.5v9"/>',
    'genomics': '<path d="M7 3c0 8 10 10 10 18M17 3c0 8-10 10-10 18M8 6h8M9 10h6M9 14h6M8 18h8"/>',
    'clinical': '<path d="M4 5v5a5 5 0 0 0 10 0V5M4 5h2M12 5h2M9 15v2a4 4 0 0 0 8 0v-2"/><circle cx="18" cy="12" r="3"/>',
    'literature': '<path d="M12 6C8 3 4 4 2 5v14c3-2 7-1 10 1 3-2 7-3 10-1V5c-3-1-6-2-10 1v14M5 8h4M15 8h4"/>',
    'stats': '<path d="M3 3v18h18M7 17v-6M12 17V6M17 17v-9"/>',
    'critic': '<path d="m12 3 8 3v6c0 4-4 7-8 9-4-2-8-5-8-9V6zM9 12l2 2 4-5"/>',
    'supporting': '<circle cx="12" cy="12" r="9"/><path d="M8 12h8M12 8v8"/>',
    'challenging': '<path d="m12 2 10 10-10 10L2 12zM12 7v6M12 17h.01"/>',
    'mechanism': '<circle cx="5" cy="12" r="3"/><circle cx="18" cy="5" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8 10 7-4M8 14l7 4"/>',
    'experiment': '<path d="M8 3h8M10 3v7l-6 9a1 1 0 0 0 1 2h14a1 1 0 0 0 1-2l-6-9V3M8 15h8"/>',
    'agent': '<rect x="5" y="7" width="14" height="13" rx="3"/><path d="M12 7V3M9 12h.01M15 12h.01M9 16h6M2 12h3M19 12h3"/>',
}
ALIASES = {'planning': 'planner', 'variant_analysis': 'genomics', 'clinical_context': 'clinical',
           'proposal': 'supporting', 'challenge': 'challenging', 'critique': 'critic', 'orchestrator': 'planner', 'synthesis': 'critic', 'advocate': 'supporting',
           'skeptic': 'challenging', 'mechanistic': 'mechanism', 'experimental': 'experiment',
           'research': 'literature', 'supporter': 'supporting', 'challenger': 'challenging',
           'clinical_scientist':'clinical','bioinformatician':'genomics','statistician':'stats',
           'clinical_pharmacologist':'clinical','molecular_scientist':'mechanism',
           'translational_scientist':'mechanism','assay_scientist':'experiment',
           'coordinator':'planner','reviewer':'critic','discovery-planning':'planner',
           'research-interpretation':'literature','molecular-interpretation':'mechanism',
           'rosalind-informed-workflow':'literature','bionemo-boltz2':'mechanism',
           'uniprot-skill':'genomics','rcsb-pdb-skill':'mechanism'}


def svg_icon(icon_id: str, size: int = 24) -> str:
    name = ALIASES.get(str(icon_id), str(icon_id))
    paths = PATHS.get(name, PATHS['agent'])
    return (f'<svg class="skill-icon" width="{int(size)}" height="{int(size)}" viewBox="0 0 24 24" '
            'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{paths}</svg>')


ALIGNMENTS = {
    'supporting': ('Support', '#6facf5', '#d8e8fd'),
    'challenging': ('Challenge', '#c0a0f5', '#eadffc'),
    'neutral': ('Neutral', '#9fb4aa', '#e3ece7'),
}


def alignment_style(alignment: str):
    return ALIGNMENTS.get(str(alignment), (str(alignment or 'Unspecified perspective').replace('_', ' '), '#9fb4aa', '#e3ece7'))
