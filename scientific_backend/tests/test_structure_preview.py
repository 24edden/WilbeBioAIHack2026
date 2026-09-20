"""Synthetic mmCIF transport fixtures; no scientific or vendor success implied."""
import hashlib
import pytest
from app.structure_preview import preview_from_cif


def cif(coordinate="1.0"):
    return f"""data_fixture
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_entity_id
_atom_site.label_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.pdbx_PDB_model_num
ATOM 1 C CA . ALA A 1 1 ? {coordinate} 2.0 3.0 1.0 50.0 1
#
""".encode()


def preview(data, **receipt):
    return preview_from_cif(data, receipt={"sha256": hashlib.sha256(data).hexdigest(), **receipt},
                            scope="synthetic_test", cif_url="/api/registered/prediction.cif")


def test_real_coordinates_and_only_public_receipt_fields():
    result = preview(cif(), request_id="fixture", confidence_score=.6, private_key="not-exported")
    assert result["chains"][0]["points"] == [{"x": 1., "y": 2., "z": 3., "residue_index": 1, "residue_name": "ALA"}]
    assert "private_key" not in result["receipt"]


def test_tampered_artifact_rejected():
    with pytest.raises(ValueError, match="verified receipt"):
        preview(cif(), sha256="0" * 64)


def test_nonfinite_coordinates_rejected():
    with pytest.raises(ValueError, match="finite"):
        preview(cif("nan"))
