-- Insert default spell statuses
INSERT INTO spell_status (status_name, status_description) VALUES
('None', 'No special status effect'),
('Paralyze', 'The target can`t move'),
('Frozen', 'The target can`t move.'),
('Burning', 'The target takes damage over time.'),
('Sleep', 'The target starts to feel drowsy'),
('Poisoned', 'The target takes damage over time'),
('Charmed', 'The target won`t attack the caster'),
('Regenerating', 'The target is regenerating'),
('Blessed', 'Cures all status effects');

-- Insert default elements
INSERT INTO element (element_name) VALUES
('Physical'),
('Fire'),
('Water'),
('Earth'),
('Air'),
('Lightning'),
('Void'),
('Sanguiphage'),
('Life'),
('Death'),
('Shadow'),
('Light');

-- Insert default weather conditions
INSERT INTO weather (weather_name) VALUES
('Clear'),
('Sunny'),
('Drizzle'),
('Rainy'),
('Stormy'),
('Snowy'),
('Foggy'),
('Windy'),
('Overcast'),
('Hailstorm'),
('Thunderstorm'),
('Blizzard'),
('Sandstorm'),
('Firestorm'),
('Volcanic Fumes'),
('Source Storm'),
('Nanite Cloud'),
('Flash Flood'),
('Volcanic Eruption'),
('Tectonic Shifts'),
('Incursion');


-- default spell types
INSERT INTO spell_type (spell_type_name) VALUES
('Single Target'),
('Area of Effect'),
('Buff'),
('Debuff'),
('Passive');

-- default event types
INSERT INTO event_type (event_name, event_description) VALUES
('Scavenge', 'Searching the surroundings for useful resources'),
('Craft', 'Creating an item using materials and skill'),
('Enchant', 'Enhancing an item with magical properties'),
('Combat', 'Engaging in a fight with an enemy');
