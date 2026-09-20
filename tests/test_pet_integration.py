"""The integrated UI must preserve evidence, request ownership and skill attribution."""
from copy import deepcopy
import pytest
from frontend.ui.pet_start import configured_request
from frontend.ui.skill_badges import skill_badges
from frontend.ui.agent_profiles import profiles, profile_catalog

def test_drawer_evidence_and_composer_share_immutable_request():
    draft={'mode':'Demo','backend':'http://localhost:8000','evidence_uploads':[('case.csv',b'a,b')],
           'config':{'specialists':['clinical']}}
    request=configured_request(draft,{'question':'My hypothesis','uploads':[('case.vcf',b'VCF')]})
    draft['config']['specialists'].append('genomics')
    draft['evidence_uploads'].clear()
    assert request.uploads==[('case.vcf',b'VCF'),('case.csv',b'a,b')]
    assert request.config=={'specialists':['clinical']} and not request.sample

def test_combined_evidence_budget_and_recorded_question():
    draft={'mode':'Demo','backend':'','evidence_uploads':[('x.csv',b'x')]*20,'config':{}}
    with pytest.raises(ValueError):configured_request(draft,{'question':'q','uploads':[('y.csv',b'y')]})
    draft.update(mode='Mock',recorded_question='Saved question',fixture='saved.jsonl',speed=2.)
    request=configured_request(draft,{'question':'New question must not relabel a recording','uploads':[]})
    assert request.question=='Saved question' and not request.uploads and request.fixture=='saved.jsonl'

def test_profiles_are_reference_metadata_not_execution_claims():
    assert len(profiles())==9
    catalog=deepcopy(profile_catalog())
    known=next(s for s in catalog if s['id']=='bionemo-boltz2')
    configured=skill_badges(['bionemo-boltz2'],configured=True)
    assert known['name'] in configured and 'does not establish execution' in configured
    reported=skill_badges(['bionemo-boltz2'])
    assert 'reported in this run' in reported and 'not a load or execution receipt' in reported
    assert 'Configured capability' not in reported
    assert skill_badges([])==''  # No invented skills on old events.

def test_provider_metadata_is_escaped_and_unknown_skills_stay_visible():
    html=skill_badges(['custom','unknown'],catalog=[{'id':'custom','label':'<script>','description':'<img onerror=bad>','icon':'<script>'}])
    assert '<script>' not in html and '<img onerror' not in html
    assert '&lt;script&gt;' in html and 'Unknown' in html and 'aria-describedby=' in html

def test_network_svg_preserves_only_observed_edges_and_escapes_labels():
    from frontend.ui.network_svg import network_svg
    from frontend.ui.state import RunState,Agent
    state=RunState(agents={'a':Agent('a','orchestrator'),'b':Agent('b','<script>',parent_id='a')},edges={('a','b'),('ghost','b')},talk={('b','a'):2})
    rendered=network_svg(state)
    assert rendered.count('class="network-spawn"')==1
    assert rendered.count('class="network-message ')==1
    assert 'b to a: 2 message(s)' in rendered
    assert '<script>' not in rendered.lower() and '&lt;script&gt;' in rendered.lower()
    original=deepcopy(state);network_svg(state);assert state==original
