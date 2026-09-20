"""Accessible icons from the provider's skill IDs, never executable provider markup."""
from hashlib import sha256
from html import escape
from .icons import svg_icon
from .agent_profiles import profile_catalog

DETAILS={
 'planning':('Task planning','Coordinates specialists and turns the question into a bounded investigation.'),
 'variant_analysis':('Variant analysis','Reviews supplied genomic variants and the available tool outputs.'),
 'clinical_context':('Clinical context','Connects supplied observations with the clinical context of the question.'),
 'research':('Evidence review','Inventories supplied evidence and its source references. This role does not imply web search.'),
 'proposal':('Develop proposals','Builds a proposal from the question and revises it after a challenge.'),
 'challenge':('Challenge assumptions','Questions an argument and identifies assumptions or missing evidence.'),
 'critique':('Critical synthesis','Reviews contributions, limitations and whether the evidence supports a conclusion.'),
}

def skill_badges(skills, *, catalog=(), owner='agent', configured=False):
    known={str(s.get('id')):s for s in profile_catalog()}
    known.update({str(s.get('id')):s for s in catalog if isinstance(s,dict)})
    badges=[]
    for index,skill in enumerate(skills):
        skill=str(skill);item=known.get(skill,{})
        label,description=DETAILS.get(skill,(skill.replace('_',' ').title(),'Skill reported by this agent. No additional description was supplied.'))
        label=str(item.get('label') or item.get('name') or label);description=str(item.get('description') or description)
        qualifier='Configured capability; this does not establish execution.' if configured else 'Skill ID reported in this run. Description is reference metadata, not a load or execution receipt.'
        tip='skill-'+sha256(f'{owner}:{index}:{skill}'.encode()).hexdigest()[:14]
        badges.append(f'<span class="pet-skill trace-help-anchor" style="anchor-name:--{tip}"><button type="button" class="trace-help-trigger" aria-label="{escape(label,quote=True)}" aria-describedby="{tip}">{svg_icon(str(item.get("icon") or skill),17)}</button><span class="trace-help-text" id="{tip}" role="tooltip" style="position-anchor:--{tip}"><strong>{escape(label)}</strong><br>{escape(description)}<br><small>{escape(qualifier)}</small></span></span>')
    return '<div class="pet-skills" aria-label="Agent skills">'+''.join(badges)+'</div>' if badges else ''
