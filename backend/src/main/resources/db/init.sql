CREATE DATABASE IF NOT EXISTS ai_prompt_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ai_prompt_manager;

CREATE TABLE IF NOT EXISTS user (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(100) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prompt (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  category VARCHAR(50) NOT NULL,
  creator_id BIGINT NOT NULL DEFAULT 0,
  creator_name VARCHAR(100) NOT NULL DEFAULT '',
  is_private TINYINT NOT NULL DEFAULT 0,
  use_count INT DEFAULT 0,
  favorite_count INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE prompt ADD COLUMN IF NOT EXISTS creator_id BIGINT NOT NULL DEFAULT 0;
ALTER TABLE prompt ADD COLUMN IF NOT EXISTS creator_name VARCHAR(100) NOT NULL DEFAULT '';
ALTER TABLE prompt ADD COLUMN IF NOT EXISTS is_private TINYINT NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS tag (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS prompt_tag (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  prompt_id BIGINT NOT NULL,
  tag_id BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS favorite (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  prompt_id BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usage_record (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  prompt_id BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT IGNORE INTO tag (id, name) VALUES
(1, 'GPT'), (2, '写作'), (3, '编程'), (4, '学习'), (5, 'AI绘画');

INSERT INTO prompt (title, content, category, creator_id, creator_name, is_private, use_count, favorite_count, created_at) VALUES
('写一篇高质量文章', '请以专业作者身份，围绕【主题】写一篇结构清晰、逻辑严谨的文章，包含引言、正文和总结。', '写作', 1, 'system', 0, 120, 45, NOW()),
('Java代码优化助手', '请优化以下Java代码，提高性能和可读性，并给出优化说明：\n【代码】', '编程', 1, 'system', 0, 98, 30, NOW()),
('英语翻译助手', '请将以下中文翻译为地道的英文，并给出语法解释：\n【文本】', '学习', 1, 'system', 0, 150, 60, NOW()),
('Midjourney绘图提示词', 'A highly detailed illustration of 【主题】，cinematic lighting, 8k, ultra realistic', 'AI绘画', 1, 'system', 0, 200, 80, NOW()),
('总结文章内容', '请总结以下文章的核心观点，并列出要点：\n【文章】', '学习', 1, 'system', 0, 110, 40, NOW());
