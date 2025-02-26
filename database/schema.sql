-- Dropping all tables in reverse dependency order
DROP TABLE IF EXISTS "character_spell_assignment" CASCADE;
DROP TABLE IF EXISTS "item" CASCADE;
DROP TABLE IF EXISTS "inventory" CASCADE;
DROP TABLE IF EXISTS "weather_assignment" CASCADE;
DROP TABLE IF EXISTS "character" CASCADE;
DROP TABLE IF EXISTS "spells" CASCADE;
DROP TABLE IF EXISTS "settlements" CASCADE;
DROP TABLE IF EXISTS "faction" CASCADE;
DROP TABLE IF EXISTS "weather" CASCADE;
DROP TABLE IF EXISTS "location" CASCADE;
DROP TABLE IF EXISTS "element" CASCADE;
DROP TABLE IF EXISTS "spell_status" CASCADE;
DROP TABLE IF EXISTS "class" CASCADE;
DROP TABLE IF EXISTS "race" CASCADE;
DROP TABLE IF EXISTS "player" CASCADE;
DROP TABLE IF EXISTS "server" CASCADE;

-- Server table to ensure uniqueness per Discord server
CREATE TABLE "server"(
    "server_id" BIGINT NOT NULL,
    "server_name" VARCHAR(100) NOT NULL,
    PRIMARY KEY ("server_id")
);

-- Player table
CREATE TABLE "player"(
    "player_id" SERIAL PRIMARY KEY,
    "player_name" VARCHAR(30) NOT NULL,
    "server_id" BIGINT NOT NULL,
    FOREIGN KEY ("server_id") REFERENCES "server"("server_id") ON DELETE CASCADE
);

-- Core entity tables
CREATE TABLE "race"(
    "race_id" SERIAL PRIMARY KEY,
    "race_name" VARCHAR(30) NOT NULL,
    "speed" SMALLINT NOT NULL,
    "is_playable" BOOLEAN NOT NULL,
    "server_id" BIGINT NOT NULL,
    FOREIGN KEY ("server_id") REFERENCES "server"("server_id") ON DELETE CASCADE
);

CREATE TABLE "class"(
    "class_id" SERIAL PRIMARY KEY,
    "class_name" VARCHAR(30) NOT NULL,
    "is_playable" BOOLEAN NOT NULL,
    "server_id" BIGINT NOT NULL,
    FOREIGN KEY ("server_id") REFERENCES "server"("server_id") ON DELETE CASCADE
);

CREATE TABLE "spell_status"(
    "spell_status_id" SERIAL PRIMARY KEY,
    "status_name" VARCHAR(30) NOT NULL,
    "status_description" VARCHAR(255) NOT NULL
);

CREATE TABLE "element"(
    "element_id" SERIAL PRIMARY KEY,
    "element_name" VARCHAR(30) NOT NULL
);

CREATE TABLE "location"(
    "location_id" SERIAL PRIMARY KEY,
    "location_name" VARCHAR(45) NOT NULL,
    "channel_id" BIGINT NOT NULL,
    "server_id" BIGINT NOT NULL,
    FOREIGN KEY ("server_id") REFERENCES "server"("server_id") ON DELETE CASCADE
);

CREATE TABLE "weather"(
    "weather_id" SERIAL PRIMARY KEY,
    "weather_name" VARCHAR(30) NOT NULL
);

-- Dependent tables
CREATE TABLE "spells"(
    "spell_id" SERIAL PRIMARY KEY,
    "spell_name" VARCHAR(45) NOT NULL,
    "spell_description" VARCHAR(255) NOT NULL,
    "spell_status_id" INTEGER NOT NULL,
    "spell_power" SMALLINT NOT NULL,
    "element_id" INTEGER NOT NULL,
    "mana_cost" SMALLINT NOT NULL,
    "race_id" INTEGER NULL,
    "class_id" INTEGER NULL,
    "server_id" BIGINT NOT NULL,
    FOREIGN KEY ("spell_status_id") REFERENCES "spell_status"("spell_status_id"),
    FOREIGN KEY ("element_id") REFERENCES "element"("element_id"),
    FOREIGN KEY ("race_id") REFERENCES "race"("race_id"),
    FOREIGN KEY ("class_id") REFERENCES "class"("class_id"),
    FOREIGN KEY ("server_id") REFERENCES "server"("server_id") ON DELETE CASCADE
);

CREATE TABLE "faction"(
    "faction_id" SERIAL PRIMARY KEY,
    "faction_name" VARCHAR(45) NOT NULL,
    "faction_description" VARCHAR(100) NOT NULL,
    "location_id" INTEGER NOT NULL,
    "server_id" BIGINT NOT NULL,
    FOREIGN KEY ("location_id") REFERENCES "location"("location_id"),
    FOREIGN KEY ("server_id") REFERENCES "server"("server_id") ON DELETE CASCADE
);

CREATE TABLE "settlements"(
    "settlement_id" SERIAL PRIMARY KEY,
    "settlement_name" VARCHAR(45) NOT NULL,
    "thread_id" BIGINT NOT NULL,
    "location_id" INTEGER NOT NULL,
    "server_id" BIGINT NOT NULL,
    FOREIGN KEY ("location_id") REFERENCES "location"("location_id"),
    FOREIGN KEY ("server_id") REFERENCES "server"("server_id") ON DELETE CASCADE
);

CREATE TABLE "character"(
    "character_id" SERIAL PRIMARY KEY,
    "character_name" VARCHAR(30) NOT NULL,
    "race_id" INTEGER NOT NULL,
    "class_id" INTEGER NOT NULL,
    "location_id" INTEGER NOT NULL,
    "experience" INTEGER NOT NULL,
    "health" SMALLINT NOT NULL,
    "mana" SMALLINT NOT NULL,
    "shards" BIGINT NOT NULL,
    "last_scavenge" TIMESTAMP NOT NULL,
    "player_id" INTEGER NOT NULL,
    "selected_character" BOOLEAN NOT NULL,
    "faction_id" INTEGER NOT NULL,
    "server_id" BIGINT NOT NULL,
    FOREIGN KEY ("race_id") REFERENCES "race"("race_id"),
    FOREIGN KEY ("class_id") REFERENCES "class"("class_id"),
    FOREIGN KEY ("location_id") REFERENCES "location"("location_id"),
    FOREIGN KEY ("player_id") REFERENCES "player"("player_id"),
    FOREIGN KEY ("faction_id") REFERENCES "faction"("faction_id"),
    FOREIGN KEY ("server_id") REFERENCES "server"("server_id") ON DELETE CASCADE
);

CREATE TABLE "weather_assignment"(
    "weather_assignment_id" SERIAL PRIMARY KEY,
    "location_id" INTEGER NOT NULL,
    "weather_id" INTEGER NOT NULL,
    FOREIGN KEY ("location_id") REFERENCES "location"("location_id"),
    FOREIGN KEY ("weather_id") REFERENCES "weather"("weather_id")
);

CREATE TABLE "inventory"(
    "inventory_id" SERIAL PRIMARY KEY,
    "inventory_name" VARCHAR(30) NOT NULL,
    "character_id" INTEGER NOT NULL,
    "is_shop" BOOLEAN NOT NULL,
    FOREIGN KEY ("character_id") REFERENCES "character"("character_id")
);

CREATE TABLE "item"(
    "item_id" SERIAL PRIMARY KEY,
    "item_name" VARCHAR(30) NOT NULL,
    "value" SMALLINT NOT NULL,
    "inventory_id" INTEGER NOT NULL,
    FOREIGN KEY ("inventory_id") REFERENCES "inventory"("inventory_id")
);

CREATE TABLE "character_spell_assignment"(
    "character_spell_assignment_id" SERIAL PRIMARY KEY,
    "character_id" INTEGER NOT NULL,
    "spell_id" INTEGER NOT NULL,
    FOREIGN KEY ("character_id") REFERENCES "character"("character_id"),
    FOREIGN KEY ("spell_id") REFERENCES "spells"("spell_id")
);
