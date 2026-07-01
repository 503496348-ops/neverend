from scripts.sync_auditor import audit_docs

def test_audit_docs_flags_conflict():
    findings = audit_docs([{'_id':'h:1','body':'<<<<<<< ours'}])
    assert any(f.code == 'conflict_marker' for f in findings)

def test_audit_docs_flags_large_attachment():
    findings = audit_docs([{'_id':'h:2','_attachments':{'a.bin':{'length':9000000}}}])
    assert any(f.code == 'large_attachment' for f in findings)
