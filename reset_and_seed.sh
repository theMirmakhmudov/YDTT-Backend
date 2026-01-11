#!/bin/bash
# Reset and seed database with test data

echo "🗑️  Resetting database..."
docker compose exec -T db psql -U ydtt_user -d ydtt_db -c "
DO \$\$ 
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END \$\$;
"

echo "🔄 Running migrations..."
docker compose exec -T app alembic upgrade head

echo "🌱 Seeding database..."
docker compose exec -T app python -m app.initial_data
docker compose exec -T app python -m app.seed_data

echo "✅ Done!"
