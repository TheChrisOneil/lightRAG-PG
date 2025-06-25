postgress / cypher


## Drop a graph
SELECT drop_graph('chunk_entity_relation', true);


## Confirm AGE installed
SELECT * FROM pg_available_extensions WHERE name = 'age';


## Set up graph serach
CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';

SET search_path = ag_catalog, "$user", public;

## Create a graph
SELECT create_graph('chunk_entity_relation');