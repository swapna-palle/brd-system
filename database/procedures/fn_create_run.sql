CREATE OR REPLACE FUNCTION fn_create_run(
    p_title TEXT,
    p_submitted_by TEXT
)
RETURNS TABLE(run_id TEXT, title TEXT, status TEXT) AS $$
BEGIN
    RETURN QUERY
    INSERT INTO runs (title, submitted_by, status, current_stage)
    VALUES (p_title, p_submitted_by, 'RUNNING', 'REQUIREMENTS_PARSED')
    RETURNING runs.run_id::text, runs.title, runs.status;
END;
$$ LANGUAGE plpgsql;
