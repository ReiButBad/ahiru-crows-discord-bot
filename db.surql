DEFINE PARAM $positions VALUE ['Setter', 'Libero', 'Middle Blocker', 'Outside Hitter', 'Opposite Hitter', 'All Rounder'];
DEFINE PARAM $rosters VALUE ['main', 'sub'];

DEFINE TABLE players SCHEMAFULL;

DEFINE FIELD jersey ON players TYPE int VALUE $value OR NULL ASSERT $value <= 50;
DEFINE FIELD playing_position ON players TYPE string ASSERT $value INSIDE $positions;
DEFINE FIELD positions ON players TYPE array ASSERT array::len($value) > 0;
DEFINE FIELD positions[*] ON players TYPE string ASSERT $value INSIDE $positions;
DEFINE FIELD rblx_id ON players TYPE int ASSERT $value != NONE;
DEFINE FIELD roster ON players TYPE string ASSERT $value INSIDE $rosters;

