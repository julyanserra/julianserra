-- Create users table
CREATE TABLE users (
  user_id     BIGSERIAL PRIMARY KEY,
  email       VARCHAR(50) UNIQUE,
  password    VARCHAR(500),
  first_name  VARCHAR(200),
  last_name   VARCHAR(200)
);

-- Create quotes table
CREATE TABLE quotes (
  quote_id    BIGSERIAL PRIMARY KEY,
  quote       TEXT,
  author      VARCHAR(200),
  created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- create table for sidebar pages
CREATE TABLE page (
  page_id  BIGSERIAL PRIMARY KEY,
  title       VARCHAR(200),
  icon        VARCHAR(200),
  content     TEXT
  created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- create table for ai voices, 
CREATE TABLE ai_voices (
  voice_id    BIGSERIAL PRIMARY KEY,
  api_voice_id VARCHAR(200),
  voice_name  VARCHAR(200),
  voice_photo VARCHAR(200),
  voice_prompt VARCHAR(200),
  voice_url   VARCHAR(200),
  payment_id  VARCHAR(200),
  created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
