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
  route      VARCHAR(200),
  icon        VARCHAR(200),
  prompt     VARCHAR(500),
  content     TEXT,
  created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- create table for ai voices, 
CREATE TABLE ai_voices (
  voice_id    BIGSERIAL PRIMARY KEY,
  api_voice_id VARCHAR(200),
  voice_name  VARCHAR(200),
  voice_photo VARCHAR(200),
  voice_prompt VARCHAR(200),
  payment_id  VARCHAR(200),
  payed       BOOLEAN DEFAULT FALSE,
  created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- golf
CREATE TABLE Course (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    rating FLOAT NOT NULL DEFAULT 72.0,
    slope FLOAT NOT NULL DEFAULT 113.0
);

-- Create the Score table
CREATE TABLE Score (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    score INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    tee VARCHAR(20) NOT NULL,
    is_nine_hole BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (course_id) REFERENCES Course(id)
);

-- Index for golf_scores table
CREATE INDEX idx_golf_scores_date ON score(date DESC);

-- If you frequently query by course_id
CREATE INDEX idx_golf_scores_course_id ON score(course_id);

-- News Categories table
CREATE TABLE news_categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- News Headlines table
CREATE TABLE news_headlines (
    id SERIAL PRIMARY KEY,
    category_id SERIAL REFERENCES news_categories(id) ON DELETE CASCADE,
    headline TEXT NOT NULL,
    url TEXT NOT NULL,
    fetched_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster querying
CREATE INDEX idx_news_headlines_category_id ON news_headlines(category_id);
CREATE INDEX idx_news_headlines_fetched_at ON news_headlines(fetched_at);

-- Initial categories (you can modify this list as needed)
INSERT INTO news_categories (name) VALUES 
    ('Mexico'),
    ('Stanford GSB'),
    ('FC Barcelona');
