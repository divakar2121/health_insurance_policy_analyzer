-- Create policies table
CREATE TABLE IF NOT EXISTS policies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(255) NOT NULL,
  file_url VARCHAR(500),
  extracted_text TEXT,
  policy_type VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create questions table
CREATE TABLE IF NOT EXISTS questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
  question TEXT NOT NULL,
  ipc_sections JSONB,
  risk_level VARCHAR(20),
  category VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create IPC reference table
CREATE TABLE IF NOT EXISTS ipc_sections (
  section_number VARCHAR(10) PRIMARY KEY,
  title VARCHAR(255),
  description TEXT,
  health_insurance_relevance TEXT
);

-- Insert IPC data
INSERT INTO ipc_sections VALUES
('336', 'Act Endangering Life or Personal Safety', 'By doing any rash or negligent act', 'Insurance coverage for negligence claims'),
('337', 'Causing Hurt by Act Endangering Life', 'Whoever causes hurt by any act', 'Accidental injury claims'),
('420', 'Cheating', 'Fraudulently deceiving any person', 'Insurance fraud detection'),
('304A', 'Death by Negligence', 'Causing death by negligence', 'Fatal accident claims');

-- Create indexes
CREATE INDEX idx_policies_user ON policies(user_id);
CREATE INDEX idx_questions_policy ON questions(policy_id);
