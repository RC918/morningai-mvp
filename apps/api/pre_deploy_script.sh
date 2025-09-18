export PYTHONPATH=$PYTHONPATH:/app/apps/api
rm -f /app/apps/api/src/database/app.db
mkdir -p /app/apps/api/src/database
python3.11 -c "from src.database import Base, engine; Base.metadata.create_all(engine)"

