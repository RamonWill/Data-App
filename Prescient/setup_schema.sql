DROP TABLE IF EXISTS login_details;
DROP TABLE IF EXISTS securities;
DROP TABLE IF EXISTS sector_definitions;
DROP TABLE IF EXISTS available_securities;

CREATE TABLE login_details (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE securities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  quantity INTEGER NOT NULL,
  price TEXT NOT NULL,
  sector TEXT NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  holder_id INTEGER NOT NULL,
  comments TEXT,
  FOREIGN KEY (holder_id) REFERENCES login_details (id)
);

CREATE TABLE sector_definitions (
  name TEXT
);

CREATE TABLE available_securities (
  name TEXT NOT NULL,
  ticker TEXT NOT NULL,
  country TEXT NOT NULL,
  benchmark_index TEXT NOT NULL
);
