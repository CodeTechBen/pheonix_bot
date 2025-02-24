-- Dropping all of the tables
DROP TABLE IF EXISTS "discord_server" CASCADE;
DROP TABLE IF EXISTS "player" CASCADE;
DROP TABLE IF EXISTS "character" CASCADE;
DROP TABLE IF EXISTS "race" CASCADE;
DROP TABLE IF EXISTS "class" CASCADE;
DROP TABLE IF EXISTS "spell_status" CASCADE;
DROP TABLE IF EXISTS "spells" CASCADE;
DROP TABLE IF EXISTS "location" CASCADE;
DROP TABLE IF EXISTS "weather_assignment" CASCADE;
DROP TABLE IF EXISTS "weather" CASCADE;
DROP TABLE IF EXISTS "inventory" CASCADE;
DROP TABLE IF EXISTS "item" CASCADE;
DROP TABLE IF EXISTS "class_spells" CASCADE;
DROP TABLE IF EXISTS "race_spells" CASCADE;

CREATE TABLE "discord_server"(
    "server_id" SMALLINT NOT NULL,
    "server_name" VARCHAR(45) NOT NULL
);
ALTER TABLE
    "discord_server" ADD PRIMARY KEY("server_id");

CREATE TABLE "player"(
    "player_id" SMALLINT NOT NULL,
    "player_name" VARCHAR(30) NOT NULL,
    "character_id" SMALLINT NOT NULL,
    "server_id" SMALLINT NOT NULL
);
ALTER TABLE
    "player" ADD PRIMARY KEY("player_id");

CREATE TABLE "character"(
    "character_id" SMALLINT NOT NULL,
    "character_name" VARCHAR(30) NOT NULL,
    "race_id" SMALLINT NOT NULL,
    "class_id" SMALLINT NOT NULL,
    "location_id" SMALLINT NOT NULL,
    "experience" INTEGER NOT NULL,
    "health" SMALLINT NOT NULL,
    "mana" SMALLINT NOT NULL,
    "shards" BIGINT NOT NULL,
    "inventory_id" BIGINT NOT NULL
);
ALTER TABLE
    "character" ADD PRIMARY KEY("character_id");

CREATE TABLE "race"(
    "race_id" SMALLINT NOT NULL,
    "race_name" VARCHAR(30) NOT NULL,
    "speed" BIGINT NOT NULL
);
ALTER TABLE
    "race" ADD PRIMARY KEY("race_id");

CREATE TABLE "class"(
    "class_id" SMALLINT NOT NULL,
    "class_name" VARCHAR(30) NOT NULL
);
ALTER TABLE
    "class" ADD PRIMARY KEY("class_id");

CREATE TABLE "spell_status"(
    "spell_status_id" SMALLINT NOT NULL,
    "status_name" VARCHAR(30) NOT NULL,
    "status_description" VARCHAR(255) NOT NULL
);
ALTER TABLE
    "spell_status" ADD PRIMARY KEY("spell_status_id");

CREATE TABLE "spells"(
    "spell_id" SMALLINT NOT NULL,
    "spell_name" VARCHAR(45) NOT NULL,
    "spell_description" VARCHAR(255) NOT NULL,
    "spell_status_id" SMALLINT NOT NULL,
    "spell_power" SMALLINT NOT NULL
);
ALTER TABLE
    "spells" ADD PRIMARY KEY("spell_id");

CREATE TABLE "location"(
    "location_id" SMALLINT NOT NULL,
    "location_name" VARCHAR(45) NOT NULL,
    "server_id" SMALLINT NOT NULL,
    "channel_id" SMALLINT NOT NULL
);
ALTER TABLE
    "location" ADD PRIMARY KEY("location_id");

CREATE TABLE "weather_assignment"(
    "weather_assignment_id" SMALLINT NOT NULL,
    "location_id" SMALLINT NOT NULL,
    "weather_id" SMALLINT NOT NULL
);
ALTER TABLE
    "weather_assignment" ADD PRIMARY KEY("weather_assignment_id");

CREATE TABLE "weather"(
    "weather_id" SMALLINT NOT NULL,
    "weather" VARCHAR(30) NOT NULL
);
ALTER TABLE
    "weather" ADD PRIMARY KEY("weather_id");

CREATE TABLE "inventory"(
    "inventory_id" SMALLINT NOT NULL,
    "inventory_name" VARCHAR(30) NOT NULL,
    "character_id" SMALLINT NOT NULL
);
ALTER TABLE
    "inventory" ADD PRIMARY KEY("inventory_id");
CREATE TABLE "item"(
    "item_id" SMALLINT NOT NULL,
    "item_name" VARCHAR(255) NOT NULL,
    "value" SMALLINT NOT NULL,
    "inventory_id" SMALLINT NOT NULL
);
ALTER TABLE
    "item" ADD PRIMARY KEY("item_id");
CREATE TABLE "class_spells"(
    "class_spell_id" SMALLINT NOT NULL,
    "class_id" SMALLINT NOT NULL,
    "spell_id" SMALLINT NOT NULL
);
ALTER TABLE
    "class_spells" ADD PRIMARY KEY("class_spell_id");
CREATE TABLE "race_spells"(
    "race_spells_id" SMALLINT NOT NULL,
    "race_id" SMALLINT NOT NULL,
    "spell_id" SMALLINT NOT NULL
);
ALTER TABLE
    "race_spells" ADD PRIMARY KEY("race_spells_id");
ALTER TABLE
    "weather_assignment" ADD CONSTRAINT "weather_assignment_weather_id_foreign" FOREIGN KEY("weather_id") REFERENCES "weather"("weather_id");
ALTER TABLE
    "class_spells" ADD CONSTRAINT "class_spells_spell_id_foreign" FOREIGN KEY("spell_id") REFERENCES "spells"("spell_id");
ALTER TABLE
    "item" ADD CONSTRAINT "item_inventory_id_foreign" FOREIGN KEY("inventory_id") REFERENCES "inventory"("inventory_id");
ALTER TABLE
    "inventory" ADD CONSTRAINT "inventory_character_id_foreign" FOREIGN KEY("character_id") REFERENCES "character"("character_id");
ALTER TABLE
    "weather_assignment" ADD CONSTRAINT "weather_assignment_location_id_foreign" FOREIGN KEY("location_id") REFERENCES "location"("location_id");
ALTER TABLE
    "player" ADD CONSTRAINT "player_server_id_foreign" FOREIGN KEY("server_id") REFERENCES "discord_server"("server_id");
ALTER TABLE
    "character" ADD CONSTRAINT "character_location_id_foreign" FOREIGN KEY("location_id") REFERENCES "location"("location_id");
ALTER TABLE
    "player" ADD CONSTRAINT "player_character_id_foreign" FOREIGN KEY("character_id") REFERENCES "character"("character_id");
ALTER TABLE
    "class_spells" ADD CONSTRAINT "class_spells_class_id_foreign" FOREIGN KEY("class_id") REFERENCES "class"("class_id");
ALTER TABLE
    "race_spells" ADD CONSTRAINT "race_spells_race_id_foreign" FOREIGN KEY("race_id") REFERENCES "race"("race_id");
ALTER TABLE
    "race_spells" ADD CONSTRAINT "race_spells_spell_id_foreign" FOREIGN KEY("spell_id") REFERENCES "spells"("spell_id");
ALTER TABLE
    "location" ADD CONSTRAINT "location_server_id_foreign" FOREIGN KEY("server_id") REFERENCES "discord_server"("server_id");
ALTER TABLE
    "character" ADD CONSTRAINT "character_race_id_foreign" FOREIGN KEY("race_id") REFERENCES "race"("race_id");
ALTER TABLE
    "spells" ADD CONSTRAINT "spells_spell_status_id_foreign" FOREIGN KEY("spell_status_id") REFERENCES "spell_status"("spell_status_id");
ALTER TABLE
    "character" ADD CONSTRAINT "character_class_id_foreign" FOREIGN KEY("class_id") REFERENCES "class"("class_id");