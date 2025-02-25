-- Insert default spell statuses
INSERT INTO spell_status (status_name, status_description) VALUES
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
