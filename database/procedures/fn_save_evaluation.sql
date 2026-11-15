CREATE OR REPLACE FUNCTION fn_save_evaluation(
    p_run_id UUID,
    p_version INT,
    p_groundedness NUMERIC,
    p_completeness NUMERIC,
    p_consistency NUMERIC,
    p_actionability NUMERIC,
    p_overall NUMERIC,
    p_badge TEXT,
    p_findings JSONB
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO evaluations (
        run_id, version, groundedness_score, completeness_score,
        consistency_score, actionability_score, overall_score, badge, critic_findings
    )
    VALUES (
        p_run_id, p_version, p_groundedness, p_completeness,
        p_consistency, p_actionability, p_overall, p_badge, p_findings
    );
END;
$$ LANGUAGE plpgsql;
