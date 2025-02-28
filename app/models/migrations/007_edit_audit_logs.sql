-- up
ALTER TABLE audit_logs ALTER user_uuid type text;
ALTER TABLE audit_logs rename user_uuid TO username;

-- down
ALTER TABLE audit_logs RENAME username TO user_uuid;
