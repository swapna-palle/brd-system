CREATE OR REPLACE FUNCTION fn_finalize_run(
    p_run_id UUID,
    p_status TEXT,
    p_badge TEXT,
    p_score NUMERIC,
    p_revision_count INT,
    p_artifacts JSONB,
    p_content_hash TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE runs
    SET status = p_status,
        current_stage = 'COMPLETED',
        quality_badge = p_badge,
        overall_score = p_score,
        revision_count = p_revision_count,
        updated_at = NOW()
    WHERE run_id = p_run_id;

    INSERT INTO artifacts (run_id, version, artifact_type, payload_json)
    VALUES (p_run_id, p_revision_count, 'FULL_ENGINEERING_PACKAGE', p_artifacts);

    INSERT INTO audit_events (run_id, agent_name, event_type, details_json)
    VALUES (
        p_run_id,
        'Agent1_Main_Orchestrator',
        'RUN_COMPLETED',
        jsonb_build_object(
            'badge', p_badge,
            'overall_score', p_score,
            'revision_count', p_revision_count,
            'input_content_hash', p_content_hash
        )
    );
END;
$$ LANGUAGE plpgsql;
